from typing import List, Dict, Any
from datetime import datetime
import logging
import hashlib
from sqlalchemy.orm import Session
from openai import OpenAI
from ..core.config import settings
from ..schemas.requests import RetrieveRequest, AnalyzeRequest
from ..schemas.responses import (
    TextEmbeddingPair, RetrieveResponse, AnalysisPoint, 
    AnalyzeResponse, DocumentPointAnalysis
)
from ..models.database import DocumentEmbedding, AnalysisResult
from .embedding_service import embedding_service
from .document_parser import document_parser
from .retrieval_service import retrieval_service

logger = logging.getLogger(__name__)


class RAGService:
    """Service for RAG operations - retrieval and analysis"""
    
    def __init__(self):
        # Initialize OpenRouter client
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
        """
        Analyze document for legal risks and recommendations point by point
        """
        logger.info(f"Analyzing document with ID: {request.id}")
        
        try:
            # Parse the document to extract text
            document_text = document_parser.parse_document(request.content)
            
            # Extract metadata
            document_metadata = document_parser.extract_document_metadata(document_text)
            
            # Split document into points/clauses
            document_points = document_parser.split_into_points(document_text)
            
            logger.info(f"Document split into {len(document_points)} points")
            
            # Analyze each point
            analyzed_points = []
            for point in document_points:
                try:
                    # Use the new RAG-based analysis function
                    analysis_points = await self._analyze_point(point.content, document_text, db)
                    
                    analyzed_point = DocumentPointAnalysis(
                        point_number=point.point_number,
                        point_content=point.content,
                        point_type=point.point_type,
                        analysis_points=analysis_points
                    )
                    analyzed_points.append(analyzed_point)
                    
                except Exception as e:
                    logger.error(f"Failed to analyze point {point.point_number}: {e}")
                    # Continue with other points even if one fails
                    continue
            
            # Store analysis result in database
            try:
                analysis_result = AnalysisResult(
                    document_id=request.id,
                    analysis_points=[point.dict() for point in analyzed_points]
                )
                db.add(analysis_result)
                db.commit()
                logger.info(f"Stored analysis result for document: {request.id}")
            except Exception as e:
                logger.error(f"Failed to store analysis result: {e}")
                db.rollback()
            
            # Create backward-compatible points list
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

    async def _analyze_point(self, point_content: str, full_document: str, db: Session) -> List[AnalysisPoint]:
        """
        Analyze a specific point/clause of the document using RAG and LLM
        """
        try:
            # Step 1: Retrieve similar chunks using RAG
            context = await self._retrieve_context_for_point(point_content, db)
            
            # Step 2: Create analysis prompt
            prompt = self._create_analysis_prompt(point_content, full_document, context)
            
            # Step 3: Call LLM for analysis
            llm_response = await self._call_llm(prompt)
            
            # Step 4: Parse LLM response into AnalysisPoint objects
            analysis_points = self._parse_llm_response(llm_response)
            
            return analysis_points
            
        except Exception as e:
            logger.error(f"Failed to analyze point: {e}")
            # Return a basic analysis as fallback
            return [AnalysisPoint(
                cause="Ошибка анализа пункта",
                risk="Не удалось определить риски",
                recommendation="Требуется ручная проверка пункта"
            )]
    
    async def _retrieve_context_for_point(self, point_content: str, db: Session, k: int = 5) -> str:
        """
        Retrieve similar legal chunks for the given point using actual RAG retrieval
        """
        try:
            # Create a retrieve request for the point content
            retrieve_request = RetrieveRequest(
                query=point_content,
                k=k,
                distance_function="l2"
            )
            
            # Use the actual retrieval service to get similar documents
            retrieval_response = await retrieval_service.retrieve_documents(retrieve_request, db)
            
            # Extract text from the retrieved results
            context_chunks = []
            for result in retrieval_response.results:
                # Add rule title and text for better context
                if result.metadata.rule_title:
                    context_chunks.append(f"{result.metadata.rule_title}: {result.text}")
                else:
                    context_chunks.append(result.text)
            
            # Join context chunks
            context = "\n\n".join(context_chunks)
            
            logger.info(f"Retrieved {len(retrieval_response.results)} relevant documents for point analysis: {len(context)} characters")
            return context
            
        except Exception as e:
            logger.error(f"Failed to retrieve context: {e}")
            return "Контекст недоступен"
    
    def _create_analysis_prompt(self, point_content: str, full_document: str, context: str) -> str:
        """
        Create analysis prompt for LLM
        """
        prompt = f"""
Вы — старший юрист-практик по договорному праву РФ.
Отвечаете строго на русском.
Формат ответа — JSON.  
Не добавляйте комментариев, колонтитулов, markdown или любого текста вне JSON.
Перед выводом проверьте данные на валидный JSON (без лишних запятых/кавычек).

ПУНКТ ДЛЯ АНАЛИЗА:
{point_content}

КОНТЕКСТ ДОКУМЕНТА:
{full_document[:1500]}...

РЕЛЕВАНТНЫЕ ПРАВОВЫЕ НОРМЫ:
{context}

ЗАДАЧА:
Проанализируйте данный пункт договора и выявите:
1. Потенциальные причины правовых проблем
2. Связанные с ними риски
3. Конкретные рекомендации по улучшению

ЗАМЕЧАНИЯ:
1. Твоя задача — найти только **существенные правовые риски**, которые:
   - могут повлечь судебные споры;
   - создают правовую неопределённость;
   - могут привести к прямым убыткам, штрафам или блокировке исполнения обязательств;
   - могут быть основанием для недействительности договора или его части.
2. Не рассматривайте незначительные организационные советы как риски (например: «следует сохранить копию договора»).
3. Не допускается формулировка рекомендации без чёткого указания причины (cause). Рекомендация должна быть реакцией на риск, а не самостоятельным комментарием.
4. На каждый выявленный риск сгенерируйте обоснованную, конкретную рекомендацию по его устранению.
5. Риски и рекомендации должны быть логически связаны: не должно быть рекомендаций без соответствующего риска.

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

### Пример работы
ПУНКТ ДЛЯ АНАЛИЗА:
Заказчик вправе в любой момент в одностороннем порядке отказаться от исполнения Договора, уведомив Подрядчика не позднее чем за 1 (один) календарный день до предполагаемой даты расторжения. При этом Заказчик не несёт расходов, связанных с таким отказом.

КОНТЕКСТ ДОКУМЕНТА:
ДОГОВОР № 12-А/24 «Оказание маркетинговых услуг»
г. Москва, 15 января 2024 г.
…
2. Предмет договора
2.1. Подрядчик оказывает Заказчику услуги по разработке и запуску рекламной кампании в интернете и наружных медиа.
…
4. Порядок оплаты
4.1. Стоимость услуг составляет 3 200 000 (Три миллиона двести тысяч) рублей. Оплата производится поэтапно:
— 50 % аванс в течение 5 рабочих дней после подписания договора;
— 50 % — в течение 10 рабочих дней после подписания итогового акта.
…
6. Ответственность сторон
6.3. Заказчик вправе в любой момент отказаться от исполнения Договора (см. пункт <данный_пункт>).
…
9. Прочие условия
9.2. Все споры решаются в Арбитражном суде г. Москвы.

РЕЛЕВАНТНЫЕ ПРАВОВЫЕ НОРМЫ:
— ст. 782 ГК РФ «Односторонний отказ от договора возмездного оказания услуг»
— ст. 310 ГК РФ «Недопустимость одностороннего отказа, кроме случаев, предусмотренных законом»
— Постановление Пленума ВАС РФ № 16 от 14.03.2014 г., п. 10 (о возмещении исполнителю фактических расходов)

ОЖИДАЕМЫЙ JSON:
[
{{
"cause": "Крайне короткий срок уведомления (1 день) и отсутствие компенсации нарушают баланс интересов и не дают Подрядчику возможности минимизировать убытки",
"risk": "Высокий: Подрядчик может понести некомпенсированные затраты и обратиться с иском о взыскании расходов, что повлечёт судебные издержки и репутационные потери для Заказчика",
"recommendation": "Увеличить срок уведомления до минимум 15 календарных дней и предусмотреть обязанность Заказчика возместить фактически понесённые Подрядчиком расходы (ст. 782 ГК РФ)"
}}
]
"""
        return prompt
    
    async def _call_llm(self, prompt: str) -> str:
        """
        Call LLM for analysis using OpenRouter
        """
        try:
            if self.openai_client is None:
                logger.warning("OpenRouter client not initialized, using mock response")
                return self._get_mock_response()
            
            # Prepare headers for OpenRouter
            extra_headers = {}
            if settings.site_url:
                extra_headers["HTTP-Referer"] = settings.site_url
            if settings.site_name:
                extra_headers["X-Title"] = settings.site_name
            
            # Call OpenRouter API
            logger.info(f"Calling OpenRouter with model: {settings.openrouter_model}")
            logger.debug(f"Prompt length: {len(prompt)} characters")
            
            completion = self.openai_client.chat.completions.create(
                extra_headers=extra_headers,
                model=settings.openrouter_model,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,
                max_tokens=2000
            )
            
            logger.debug(f"OpenRouter API call completed. Response object: {type(completion)}")
            
            response_content = completion.choices[0].message.content
            
            # Check if response is valid
            if not response_content:
                logger.warning("OpenRouter returned empty response, using mock response")
                return self._get_mock_response()
            
            logger.info(f"LLM analysis completed successfully via OpenRouter. Response length: {len(response_content)}")
            logger.debug(f"OpenRouter response preview: {response_content[:200]}...")
            return response_content
            
        except Exception as e:
            logger.error(f"OpenRouter LLM call failed: {e}")
            # Return fallback mock response
            return self._get_mock_response()
    
    def _get_mock_response(self) -> str:
        """
        Return mock response when LLM is not available
        """
        return '''[
  {
    "cause": "Неопределенность в сроках исполнения обязательств",
    "risk": "Средний риск споров о сроках и возможных штрафных санкций",
    "recommendation": "Установить конкретные календарные даты или четкие критерии определения сроков исполнения"
  },
  {
    "cause": "Отсутствие механизма урегулирования споров",
    "risk": "Высокий риск длительных судебных разбирательств",
    "recommendation": "Добавить пункт о досудебном урегулировании споров и указать применимое право"
  }
]'''
    
    def _parse_llm_response(self, llm_response: str) -> List[AnalysisPoint]:
        """
        Parse LLM response into AnalysisPoint objects
        """
        try:
            import json
            
            # Check if response is empty or None
            if not llm_response or not llm_response.strip():
                logger.warning("LLM response is empty, using default analysis")
                return self._get_default_analysis()
            
            response_text = llm_response.strip()
            logger.debug(f"Raw LLM response: {response_text[:500]}...")
            
            # Try to extract JSON from response if it contains other text
            json_start = response_text.find('[')
            json_end = response_text.rfind(']') + 1
            
            if json_start != -1 and json_end > json_start:
                json_text = response_text[json_start:json_end]
                logger.debug(f"Extracted JSON: {json_text}")
            else:
                json_text = response_text
            
            # Try to parse JSON response
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
            logger.debug(f"LLM response was: '{llm_response}'")
            
            # Try to extract analysis from text if JSON parsing fails
            return self._parse_text_response(llm_response)
    
    def _parse_text_response(self, response: str) -> List[AnalysisPoint]:
        """
        Fallback parser for non-JSON responses
        """
        try:
            # Simple text parsing as fallback
            lines = response.split('\n')
            analysis_points = []
            
            current_analysis = {}
            for line in lines:
                line = line.strip()
                if 'причина' in line.lower() or 'cause' in line.lower():
                    current_analysis['cause'] = line.split(':', 1)[-1].strip()
                elif 'риск' in line.lower() or 'risk' in line.lower():
                    current_analysis['risk'] = line.split(':', 1)[-1].strip()
                elif 'рекомендация' in line.lower() or 'recommendation' in line.lower():
                    current_analysis['recommendation'] = line.split(':', 1)[-1].strip()
                    
                    # If we have all three fields, create AnalysisPoint
                    if all(key in current_analysis for key in ['cause', 'risk', 'recommendation']):
                        analysis_points.append(AnalysisPoint(**current_analysis))
                        current_analysis = {}
            
            return analysis_points if analysis_points else self._get_default_analysis()
            
        except Exception as e:
            logger.error(f"Text parsing failed: {e}")
            return self._get_default_analysis()
    
    def _get_default_analysis(self) -> List[AnalysisPoint]:
        """
        Return default analysis when parsing fails
        """
        return [AnalysisPoint(
            cause="Не удалось провести автоматический анализ",
            risk="Неопределенный риск",
            recommendation="Рекомендуется ручная проверка пункта юристом"
        )]


# Global RAG service instance
rag_service = RAGService() 