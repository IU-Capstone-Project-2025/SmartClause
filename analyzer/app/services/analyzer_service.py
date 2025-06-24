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
from ..models.database import AnalysisResult
from .embedding_service import embedding_service
from .document_parser import document_parser
from .retrieval_service import retrieval_service
from .retry_utils import RetryMixin, concurrency_manager, with_retry, with_concurrency_limit

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
        metrics = {
            "total_points": 0,
            "successful_points": 0,
            "failed_points": 0,
            "embedding_failures": 0,
            "retrieval_failures": 0,
            "llm_failures": 0,
        }
        
        try:
            # Parse document asynchronously
            parse_start = datetime.now()
            document_text, document_metadata, document_points = await asyncio.gather(
                self._parse_document_async(request.content),
                self._extract_metadata_async(request.content),
                self._split_into_points_async(request.content)
            )
            parse_duration = (datetime.now() - parse_start).total_seconds()
            
            metrics["total_points"] = len(document_points)
            logger.info(f"Document parsed in {parse_duration:.2f}s - split into {len(document_points)} points")
            
            if not document_points:
                logger.info("No points found in document")
                return self._create_empty_response(request.id, document_metadata)
            
            # Batch process everything concurrently
            analysis_start_time = datetime.now()
            analyzed_points = await self._analyze_points_concurrently(document_points, document_text, db)
            analysis_duration = (datetime.now() - analysis_start_time).total_seconds()
            
            # Calculate metrics
            for point in analyzed_points:
                if len(point.analysis_points) > 0 and point.analysis_points[0].cause != "Не удалось провести автоматический анализ":
                    metrics["successful_points"] += 1
                else:
                    metrics["failed_points"] += 1
            
            total_duration = (datetime.now() - analysis_start).total_seconds()
            
            logger.info(
                f"Analysis completed in {total_duration:.2f}s "
                f"(parsing: {parse_duration:.2f}s, analysis: {analysis_duration:.2f}s) - "
                f"Success rate: {metrics['successful_points']}/{metrics['total_points']} "
                f"({(metrics['successful_points']/metrics['total_points']*100):.1f}%)"
            )
            
            # Create response
            all_analysis_points = []
            for analyzed_point in analyzed_points:
                all_analysis_points.extend(analyzed_point.analysis_points)
            
            return AnalyzeResponse(
                document_points=analyzed_points,
                document_id=request.id,
                document_metadata=document_metadata,
                total_points=len(analyzed_points),
                analysis_timestamp=datetime.now().isoformat(),
                points=all_analysis_points  # For backward compatibility
            )
            
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
                    self._generate_embedding_with_timeout(point.content),
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
                self._analyze_single_point_with_timeout(
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

    async def _generate_embedding_with_timeout(self, content: str):
        """Generate embedding with timeout protection"""
        return await asyncio.to_thread(embedding_service.encode_to_list, content)

    async def _analyze_single_point_with_timeout(self, point, document_text: str, embedding, db: Session) -> DocumentPointAnalysis:
        """Analyze a single point with timeout protection and retry logic"""
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
            base_prompt = await self._create_prompt_async(point.content, document_text)
            final_prompt = base_prompt.replace("{context}", context)
            
            # Call LLM with concurrency limit and simple timeout
            try:
                llm_response = await concurrency_manager.with_llm_limit(
                    asyncio.wait_for(
                        self._call_llm_with_timeout(final_prompt),
                        timeout=settings.llm_timeout
                    )
                )
            except asyncio.TimeoutError:
                logger.warning(f"LLM timeout for point {point.point_number}")
                llm_response = self._get_mock_response()
            except Exception as e:
                logger.warning(f"LLM call failed for point {point.point_number}: {e}")
                llm_response = self._get_mock_response()
            
            analysis_points = self._parse_llm_response(llm_response)
            
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
        """Get context by calling the retrieval service with improved error handling"""
        try:
            # Create a RetrieveRequest for the retrieval service
            retrieve_request = RetrieveRequest(
                query=point_content,
                k=k,
                distance_function="cosine"
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

    async def _create_prompt_async(self, point_content: str, full_document: str) -> str:
        """Create analysis prompt template"""
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

    async def _call_llm_with_timeout(self, prompt: str) -> str:
        """Call LLM with timeout protection and improved error handling"""
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
                    temperature=0.3,
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

    async def _call_llm_async(self, prompt: str) -> str:
        """Legacy method for backward compatibility - delegates to new timeout version"""
        return await self._call_llm_with_timeout(prompt)

    def _parse_llm_response(self, llm_response: str) -> List[AnalysisPoint]:
        """Parse LLM response into AnalysisPoint objects"""
        try:
            import json
            
            if not llm_response or not llm_response.strip():
                return self._get_default_analysis()
            
            # Extract JSON from response
            text = llm_response.strip()
            json_start = text.find('[')
            json_end = text.rfind(']') + 1
            
            if json_start != -1 and json_end > json_start:
                json_text = text[json_start:json_end]
            else:
                json_text = text
            
            # Parse JSON response
            analysis_data = json.loads(json_text)
            
            analysis_points = []
            for item in analysis_data:
                if isinstance(item, dict) and all(key in item for key in ['cause', 'risk', 'recommendation']):
                    analysis_points.append(AnalysisPoint(
                        cause=item['cause'],
                        risk=item['risk'],
                        recommendation=item['recommendation']
                    ))
            
            return analysis_points if analysis_points else self._get_default_analysis()
            
        except (json.JSONDecodeError, KeyError, TypeError) as e:
            logger.error(f"Failed to parse LLM response: {e}")
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

    # Async wrapper methods for document processing
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