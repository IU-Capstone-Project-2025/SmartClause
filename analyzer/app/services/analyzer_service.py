from typing import List, Dict, Any
from datetime import datetime
import logging
import asyncio
from sqlalchemy.orm import Session
from openai import OpenAI
from ..core.config import settings
from ..schemas.requests import AnalyzeRequest, RetrieveRequest
from ..schemas.responses import (
    AnalysisPoint, AnalyzeResponse, DocumentPointAnalysis
)
from .embedding_service import embedding_service
from .document_parser import document_parser
from .retrieval_service import retrieval_service
from .retry_utils import RetryMixin, concurrency_manager

logger = logging.getLogger(__name__)


class AnalyzerService(RetryMixin):
    """Service for concurrent document analysis operations with optimized resource management"""
    
    def __init__(self):
        self.openai_client = None
        if settings.openrouter_api_key:
            self.openai_client = OpenAI(
                base_url=settings.openrouter_base_url,
                api_key=settings.openrouter_api_key,
            )
            logger.info("OpenRouter client initialized successfully")
        else:
            logger.warning("OpenRouter API key not found. LLM analysis will use mock responses.")
    
    async def analyze_document(self, request: AnalyzeRequest, db: Session) -> AnalyzeResponse:
        """Analyze document for legal risks and recommendations with concurrent processing"""
        logger.info(f"Analyzing document with ID: {request.id}")
        
        # Performance monitoring
        analysis_start = datetime.now()
        
        try:
            # Parse document asynchronously
            parse_start = datetime.now()
            document_text, document_metadata, document_points = await asyncio.gather(
                self._parse_document_async(request.content),
                self._extract_metadata_async(request.content),
                self._split_into_points_async(request.content)
            )
            parse_duration = (datetime.now() - parse_start).total_seconds()
            
            logger.info(f"Document parsed in {parse_duration:.2f}s - split into {len(document_points)} points")
            
            if not document_points:
                logger.info("No points found in document")
                return self._create_empty_response(request.id, document_metadata)
            
            # Batch process everything concurrently
            analysis_start_time = datetime.now()
            analyzed_points = await self._analyze_points_concurrently(document_points, document_text, db)
            analysis_duration = (datetime.now() - analysis_start_time).total_seconds()
            
            # Calculate success metrics
            successful_points = sum(
                1 for point in analyzed_points 
                if (len(point.analysis_points) > 0 and 
                    point.analysis_points[0].cause != "Не удалось провести автоматический анализ")
            )
            total_points = len(analyzed_points)
            total_duration = (datetime.now() - analysis_start).total_seconds()
            
            logger.info(
                f"Analysis completed in {total_duration:.2f}s "
                f"(parsing: {parse_duration:.2f}s, analysis: {analysis_duration:.2f}s) - "
                f"Success rate: {successful_points}/{total_points} "
                f"({(successful_points/total_points*100):.1f}%)"
            )
            
            # Create response
            all_analysis_points = []
            for analyzed_point in analyzed_points:
                all_analysis_points.extend(analyzed_point.analysis_points)
            
            response = AnalyzeResponse(
                document_points=analyzed_points,
                document_id=request.id,
                document_metadata=document_metadata,
                total_points=len(analyzed_points),
                analysis_timestamp=datetime.now().isoformat(),
                points=all_analysis_points  # For backward compatibility
            )
            
            return response
       
        except Exception as e:
            total_duration = (datetime.now() - analysis_start).total_seconds()
            logger.error(f"Failed to analyze document after {total_duration:.2f}s: {e}")
            raise

    async def _analyze_points_concurrently(self, document_points, document_text: str, db: Session) -> List[DocumentPointAnalysis]:
        """Analyze all document points concurrently with optimized batching and resource management"""
        
        if not document_points:
            return []
        
        total_points = len(document_points)
        logger.info(f"Starting optimized analysis of {total_points} points with concurrency limits")
        
        # Step 1: Generate embeddings in controlled batches using embedding semaphore
        logger.info(f"Generating embeddings for {total_points} points")
        embedding_tasks = [
            concurrency_manager.with_embedding_limit(
                asyncio.wait_for(
                    self._generate_embedding(point.content),
                    timeout=settings.embedding_timeout
                )
            )
            for point in document_points
        ]
        
        embeddings = await asyncio.gather(*embedding_tasks, return_exceptions=True)
        successful_embeddings = sum(1 for e in embeddings if not isinstance(e, Exception))
        logger.info(f"Generated {successful_embeddings}/{total_points} embeddings successfully")
        
        # Step 2: Process all points with global concurrency limits
        logger.info(f"Processing {total_points} points with global concurrency limits")
        analysis_tasks = [
            concurrency_manager.with_global_limit(
                self._analyze_single_point(
                    point,
                    document_text,
                    embeddings[i],
                    db
                )
            )
            for i, point in enumerate(document_points)
        ]
        
        results = await asyncio.gather(*analysis_tasks, return_exceptions=True)
        
        # Step 3: Process results and handle failures with detailed logging
        analyzed_points = []
        failed_count = 0
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Failed to analyze point {document_points[i].point_number}: {result}")
                analyzed_points.append(self._create_fallback_analysis(document_points[i]))
                failed_count += 1
            else:
                analyzed_points.append(result)
        
        success_rate = ((total_points - failed_count) / total_points) * 100
        logger.info(f"Analysis completed: {total_points - failed_count}/{total_points} points successful ({success_rate:.1f}%)")
        
        return analyzed_points

    async def _generate_embedding(self, content: str):
        """Generate embedding for content"""
        return await asyncio.to_thread(embedding_service.encode_to_list, content)

    async def _analyze_single_point(self, point, document_text: str, embedding, db: Session) -> DocumentPointAnalysis:
        """Analyze a single document point"""
        point_start = datetime.now()
        logger.debug(f"Starting analysis for point {point.point_number}")
        
        try:
            # Handle embedding failure
            if isinstance(embedding, Exception):
                logger.warning(f"Using fallback for point {point.point_number} due to embedding failure: {embedding}")
                context = "Контекст недоступен из-за ошибки генерации embeddings"
            else:
                # Run retrieval (simple call without nested retry)
                try:
                    context = await asyncio.wait_for(
                        self._get_context_from_retrieval_service(point.content, db),
                        timeout=settings.retrieval_timeout
                    )
                except asyncio.TimeoutError:
                    logger.warning(f"Retrieval timeout for point {point.point_number}")
                    context = "Контекст недоступен из-за таймаута поиска"
                except Exception as e:
                    logger.warning(f"Retrieval failed for point {point.point_number}: {e}")
                    context = "Контекст недоступен из-за ошибки поиска"
            
            # Create prompt
            prompt = await self._create_prompt(point.content, document_text)
            final_prompt = prompt.replace("{context}", context)
            
            # Call LLM with retry logic for parsing failures
            analysis_points = await self._call_llm_with_parsing_retry(
                final_prompt, 
                point.point_number
            )
            
            duration = (datetime.now() - point_start).total_seconds()
            logger.debug(f"Completed analysis for point {point.point_number} in {duration:.2f} seconds")
            
            return DocumentPointAnalysis(
                point_number=point.point_number,
                point_content=point.content,
                point_type=point.point_type,
                analysis_points=analysis_points
            )
            
        except Exception as e:
            duration = (datetime.now() - point_start).total_seconds()
            logger.error(f"Failed to analyze point {point.point_number} after {duration:.2f} seconds: {e}")
            return self._create_fallback_analysis(point)

    async def _get_context_from_retrieval_service(self, point_content: str, db: Session, k: int = 5) -> str:
        """Get relevant legal context for the point"""
        try:
            # Create a RetrieveRequest for the retrieval service
            retrieve_request = RetrieveRequest(
                query=point_content,
                k=k,
                distance_function="l2"
            )
            
            # Call the retrieval service directly
            logger.debug(f"Retrieving context for query length: {len(point_content)}")
            response = await retrieval_service.retrieve_rules(retrieve_request, db)
            
            # Format the retrieved rules for context
            chunks = []
            for result in response.results:
                rule_title = result.metadata.rule_title or ""
                text = result.text
                
                if rule_title:
                    chunks.append(f"{rule_title}: {text}")
                else:
                    chunks.append(text)
            
            context = "\n\n".join(chunks)
            logger.debug(f"Retrieved {len(chunks)} relevant rules: {len(context)} characters")
            return context
                
        except Exception as e:
            logger.error(f"Failed to retrieve context from service: {e}")
            return "Контекст недоступен из-за ошибки поиска"

    async def _call_llm_with_parsing_retry(self, prompt: str, point_number: int) -> List[AnalysisPoint]:
        """Call LLM with retry logic specifically for parsing failures"""
        max_attempts = settings.max_retries + 1
        
        for attempt in range(max_attempts):
            try:
                # Make LLM call with concurrency limit and timeout
                llm_response = await concurrency_manager.with_llm_limit(
                    asyncio.wait_for(
                        self._call_llm(prompt),
                        timeout=settings.llm_timeout
                    )
                )
                
                # Try to parse the response
                analysis_points = self._parse_llm_response(llm_response)
                
                # Check if parsing was successful (not default fallback)
                if (analysis_points and 
                    len(analysis_points) > 0 and 
                    analysis_points[0].cause != "Не удалось провести автоматический анализ"):
                    logger.debug(f"Successfully parsed LLM response for point {point_number} on attempt {attempt + 1}")
                    return analysis_points
                else:
                    # Parsing failed, but this counts as a "parsing failure"
                    if attempt < max_attempts - 1:
                        delay = settings.retry_delay * (settings.retry_backoff_factor ** attempt)
                        logger.warning(
                            f"Point {point_number}: LLM response parsing failed on attempt {attempt + 1}/{max_attempts}. "
                            f"Retrying in {delay:.2f} seconds..."
                        )
                        await asyncio.sleep(delay)
                        continue
                    else:
                        logger.error(f"Point {point_number}: All {max_attempts} parsing attempts failed")
                        return self._get_default_analysis()
                        
            except asyncio.TimeoutError:
                if attempt < max_attempts - 1:
                    delay = settings.retry_delay * (settings.retry_backoff_factor ** attempt)
                    logger.warning(
                        f"Point {point_number}: LLM timeout on attempt {attempt + 1}/{max_attempts}. "
                        f"Retrying in {delay:.2f} seconds..."
                    )
                    await asyncio.sleep(delay)
                    continue
                else:
                    logger.error(f"Point {point_number}: LLM timeout on all {max_attempts} attempts")
                    return self._get_default_analysis()
                    
            except Exception as e:
                if attempt < max_attempts - 1:
                    delay = settings.retry_delay * (settings.retry_backoff_factor ** attempt)
                    error_msg = str(e) if str(e).strip() else type(e).__name__
                    logger.warning(
                        f"Point {point_number}: LLM call failed on attempt {attempt + 1}/{max_attempts} ({error_msg}). "
                        f"Retrying in {delay:.2f} seconds..."
                    )
                    await asyncio.sleep(delay)
                    continue
                else:
                    error_msg = str(e) if str(e).strip() else type(e).__name__
                    logger.error(f"Point {point_number}: LLM call failed on all {max_attempts} attempts ({error_msg})")
                    return self._get_default_analysis()
        
        # This shouldn't be reached, but just in case
        return self._get_default_analysis()

    async def _create_prompt(self, point_content: str, full_document: str) -> str:
        """Create LLM prompt for legal analysis"""
        return f"""
Вы — старший юрист-практик по договорному праву РФ.
Отвечаете строго на русском.
Формат ответа — JSON.  
Не добавляйте комментариев, колонтитулов, markdown или любого текста вне JSON.

ПУНКТ ДЛЯ АНАЛИЗА:
{point_content}

КОНТЕКСТ ДОКУМЕНТА:
{full_document[:1500]}...

РЕЛЕВАНТНЫЕ ПРАВОВЫЕ НОРМЫ:
{{context}}

ЗАДАЧА:
Проанализируйте данный пункт договора и выявите:
1. Потенциальные причины правовых проблем
2. Связанные с ними риски
3. Конкретные рекомендации по улучшению

ФОРМАТ ОТВЕТА:
Верните анализ в следующе строгом JSON формате:
[
  {{
    "cause": "Описание выявленной проблемы или недочета",
    "risk": "Описание риска и его уровень",
    "recommendation": "Конкретная рекомендация по устранению проблемы"
  }}
]

ВАЖНО:
- Если проблем не обнаружено, верните пустой массив []
- Фокусируйтесь на практических правовых аспектах
- Рекомендации должны быть конкретными и применимыми
- Учитывайте российское законодательство
"""

    async def _call_llm(self, prompt: str) -> str:
        """Call LLM for analysis"""
        if self.openai_client is None:
            return self._get_mock_response()
        
        def _sync_llm_call():
            try:
                extra_headers = {}
                if settings.site_url:
                    extra_headers["HTTP-Referer"] = settings.site_url
                if settings.site_name:
                    extra_headers["X-Title"] = settings.site_name
                
                logger.debug(f"Calling OpenRouter with model: {settings.openrouter_model}")
                completion = self.openai_client.chat.completions.create(
                    extra_headers=extra_headers,
                    model=settings.openrouter_model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.0,
                    max_tokens=2000
                )
                
                response_content = completion.choices[0].message.content
                if not response_content:
                    logger.warning("Empty response from OpenRouter, using mock response")
                    return self._get_mock_response()
                
                logger.debug(f"LLM analysis completed. Response length: {len(response_content)}")
                return response_content
                
            except Exception as e:
                logger.error(f"OpenRouter API error: {e}")
                raise e
        
        try:
            return await asyncio.to_thread(_sync_llm_call)
        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            # Return mock response as fallback
            return self._get_mock_response()



    def _parse_llm_response(self, llm_response: str) -> List[AnalysisPoint]:
        """Parse LLM response into AnalysisPoint objects"""
        try:
            import json
            
            if not llm_response or not llm_response.strip():
                logger.debug("Empty LLM response received")
                return self._get_default_analysis()
            
            # Extract JSON from response
            text = llm_response.strip()
            json_start = text.find('[')
            json_end = text.rfind(']') + 1
            
            if json_start != -1 and json_end > json_start:
                json_text = text[json_start:json_end]
            else:
                logger.debug(f"No JSON array found in LLM response: {text[:100]}...")
                return self._get_default_analysis()
            
            # Parse JSON response
            try:
                analysis_data = json.loads(json_text)
            except json.JSONDecodeError as e:
                logger.debug(f"JSON decode error: {e}. Response fragment: {json_text[:200]}...")
                return self._get_default_analysis()
            
            if not isinstance(analysis_data, list):
                logger.debug(f"LLM response is not a list: {type(analysis_data)}")
                return self._get_default_analysis()
            
            analysis_points = []
            for i, item in enumerate(analysis_data):
                if isinstance(item, dict) and all(key in item for key in ['cause', 'risk', 'recommendation']):
                    analysis_points.append(AnalysisPoint(
                        cause=item['cause'],
                        risk=item['risk'],
                        recommendation=item['recommendation']
                    ))
                else:
                    logger.debug(f"Invalid analysis item {i}: missing required keys or not a dict")
            
            if analysis_points:
                logger.debug(f"Successfully parsed {len(analysis_points)} analysis points")
                return analysis_points
            else:
                logger.debug("No valid analysis points found in response")
                return self._get_default_analysis()
            
        except Exception as e:
            logger.error(f"Unexpected error in LLM response parsing: {e}")
            return self._get_default_analysis()

    def _get_mock_response(self) -> str:
        """Return mock response when LLM is not available"""
        return '''[
  {
    "cause": "Неопределенность в сроках исполнения обязательств",
    "risk": "Средний риск споров о сроках и возможных штрафных санкций",
    "recommendation": "Установить конкретные календарные даты или четкие критерии определения сроков исполнения"
  }
]'''

    def _get_default_analysis(self) -> List[AnalysisPoint]:
        """Return default analysis when parsing fails"""
        return [AnalysisPoint(
            cause="Не удалось провести автоматический анализ",
            risk="Неопределенный риск",
            recommendation="Рекомендуется ручная проверка пункта юристом"
        )]

    def _create_fallback_analysis(self, point) -> DocumentPointAnalysis:
        """Create fallback analysis for failed points"""
        return DocumentPointAnalysis(
            point_number=point.point_number,
            point_content=point.content,
            point_type=point.point_type,
            analysis_points=self._get_default_analysis()
        )

    def _create_empty_response(self, document_id: str, metadata: Dict[str, Any]) -> AnalyzeResponse:
        """Create empty response for documents with no points"""
        return AnalyzeResponse(
            document_points=[],
            document_id=document_id,
            document_metadata=metadata,
            total_points=0,
            analysis_timestamp=datetime.now().isoformat(),
            points=[]
        )

    # Document processing methods
    async def _parse_document_async(self, content: bytes) -> str:
        """Parse document asynchronously"""
        return await asyncio.to_thread(document_parser.parse_document, content)
    
    async def _extract_metadata_async(self, content: bytes) -> Dict[str, Any]:
        """Extract metadata asynchronously"""
        text = await self._parse_document_async(content)
        return await asyncio.to_thread(document_parser.extract_document_metadata, text)
    
    async def _split_into_points_async(self, content: bytes):
        """Split document into points asynchronously"""
        text = await self._parse_document_async(content)
        return await asyncio.to_thread(document_parser.split_into_points, text)

# Global analyzer service instance
analyzer_service = AnalyzerService() 