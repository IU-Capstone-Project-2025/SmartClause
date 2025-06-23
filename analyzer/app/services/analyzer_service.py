from typing import List, Dict, Any
from datetime import datetime
import logging
import asyncio
from sqlalchemy.orm import Session
from openai import OpenAI
from ..core.config import settings
from ..schemas.requests import AnalyzeRequest
from ..schemas.responses import (
    AnalysisPoint, AnalyzeResponse, DocumentPointAnalysis
)
from ..models.database import AnalysisResult
from .embedding_service import embedding_service
from .document_parser import document_parser

logger = logging.getLogger(__name__)


class AnalyzerService:
    """Service for concurrent document analysis operations"""
    
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
        
        try:
            # Parse document asynchronously
            document_text, document_metadata, document_points = await asyncio.gather(
                self._parse_document_async(request.content),
                self._extract_metadata_async(request.content),
                self._split_into_points_async(request.content)
            )
            
            logger.info(f"Document split into {len(document_points)} points")
            
            if not document_points:
                return self._create_empty_response(request.id, document_metadata)
            
            # Batch process everything concurrently
            start_time = datetime.now()
            analyzed_points = await self._analyze_points_concurrently(document_points, document_text)
            duration = (datetime.now() - start_time).total_seconds()
            
            logger.info(f"Completed concurrent analysis of {len(analyzed_points)} points in {duration:.2f} seconds")
            
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
            logger.error(f"Failed to analyze document: {e}")
            raise

    async def _analyze_points_concurrently(self, document_points, document_text: str) -> List[DocumentPointAnalysis]:
        """Analyze all document points concurrently with optimized batching"""
        
        # Step 1: Generate all embeddings concurrently
        logger.info(f"Generating embeddings for {len(document_points)} points")
        embedding_tasks = [
            asyncio.to_thread(embedding_service.encode_to_list, point.content)
            for point in document_points
        ]
        embeddings = await asyncio.gather(*embedding_tasks, return_exceptions=True)
        
        # Step 2: Process all points concurrently (retrieval + LLM calls)
        logger.info(f"Starting concurrent analysis of {len(document_points)} points")
        analysis_tasks = [
            self._analyze_single_point(point, document_text, embeddings[i])
            for i, point in enumerate(document_points)
        ]
        
        results = await asyncio.gather(*analysis_tasks, return_exceptions=True)
        
        # Step 3: Process results and handle failures
        analyzed_points = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Failed to analyze point {document_points[i].point_number}: {result}")
                analyzed_points.append(self._create_fallback_analysis(document_points[i]))
            else:
                analyzed_points.append(result)
        
        return analyzed_points

    async def _analyze_single_point(self, point, document_text: str, embedding) -> DocumentPointAnalysis:
        """Analyze a single point with concurrent retrieval and LLM processing"""
        point_start = datetime.now()
        logger.info(f"Starting analysis for point {point.point_number}")
        
        try:
            # Run retrieval and prompt creation concurrently
            context_task = self._get_context_async(embedding) if not isinstance(embedding, Exception) else asyncio.create_task(asyncio.sleep(0, result="Контекст недоступен"))
            prompt_task = asyncio.create_task(self._create_prompt_async(point.content, document_text))
            
            context, base_prompt = await asyncio.gather(context_task, prompt_task)
            
            # Create final prompt and call LLM
            final_prompt = base_prompt.replace("{context}", context)
            llm_response = await self._call_llm_async(final_prompt)
            analysis_points = self._parse_llm_response(llm_response)
            
            duration = (datetime.now() - point_start).total_seconds()
            logger.info(f"Completed analysis for point {point.point_number} in {duration:.2f} seconds")
            
            return DocumentPointAnalysis(
                point_number=point.point_number,
                point_content=point.content,
                point_type=point.point_type,
                analysis_points=analysis_points
            )
            
        except Exception as e:
            logger.error(f"Failed to analyze point {point.point_number}: {e}")
            return self._create_fallback_analysis(point)

    async def _get_context_async(self, embedding: List[float], k: int = 5) -> str:
        """Get context using pre-computed embedding with separate DB session"""
        if not embedding:
            return "Контекст недоступен"
            
        def _db_query():
            from sqlalchemy import text
            from ..core.database import SessionLocal
            
            db = SessionLocal()
            try:
                query_vector = f"[{','.join(map(str, embedding))}]"
                sql = text(f"""
                    SELECT rule_title, rule_text
                    FROM legal_rules 
                    WHERE embedding IS NOT NULL
                    ORDER BY (1 - (embedding <=> '{query_vector}')) DESC
                    LIMIT :k
                """)
                
                rows = db.execute(sql, {"k": k}).fetchall()
                chunks = []
                for row in rows:
                    if row.rule_title:
                        chunks.append(f"{row.rule_title}: {row.rule_text}")
                    else:
                        chunks.append(row.rule_text)
                return chunks
            finally:
                db.close()
        
        try:
            chunks = await asyncio.to_thread(_db_query)
            context = "\n\n".join(chunks)
            logger.info(f"Retrieved {len(chunks)} relevant documents: {len(context)} characters")
            return context
        except Exception as e:
            logger.error(f"Failed to retrieve context: {e}")
            return "Контекст недоступен"

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

    async def _call_llm_async(self, prompt: str) -> str:
        """Call LLM asynchronously using thread pool"""
        if self.openai_client is None:
            return self._get_mock_response()
        
        def _sync_llm_call():
            extra_headers = {}
            if settings.site_url:
                extra_headers["HTTP-Referer"] = settings.site_url
            if settings.site_name:
                extra_headers["X-Title"] = settings.site_name
            
            completion = self.openai_client.chat.completions.create(
                extra_headers=extra_headers,
                model=settings.openrouter_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=2000
            )
            
            response_content = completion.choices[0].message.content
            if not response_content:
                return self._get_mock_response()
            
            logger.info(f"LLM analysis completed. Response length: {len(response_content)}")
            return response_content
        
        try:
            logger.info(f"Calling OpenRouter with model: {settings.openrouter_model}")
            return await asyncio.to_thread(_sync_llm_call)
        except Exception as e:
            logger.error(f"OpenRouter LLM call failed: {e}")
            return self._get_mock_response()

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