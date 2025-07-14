from typing import List, Dict, Any
from datetime import datetime
import logging
import asyncio
import re
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
            logger.error("OpenRouter API key not found. Analysis will fail without proper LLM configuration.")
            raise ValueError("OpenRouter API key is required for analysis functionality")

    def _extract_risk_level(self, risk_text: str) -> int:
        """
        Extract risk level from risk text and return numeric value for sorting.
        Higher numbers = higher risk priority.
        
        Args:
            risk_text: The risk description text containing risk level
            
        Returns:
            int: 3 for High, 2 for Medium, 1 for Low, 0 for unknown
        """
        if not risk_text:
            return 0
        
        risk_text_lower = risk_text.lower()
        
        # Russian risk levels
        if 'высокий' in risk_text_lower:
            return 3
        elif 'средний' in risk_text_lower:
            return 2
        elif 'низкий' in risk_text_lower:
            return 1
        
        # English risk levels (fallback)
        if 'high' in risk_text_lower:
            return 3
        elif 'medium' in risk_text_lower or 'moderate' in risk_text_lower:
            return 2
        elif 'low' in risk_text_lower:
            return 1
        
        # If no clear risk level found, default to medium priority
        return 2

    def _sort_analysis_points_by_risk(self, analysis_points: List[AnalysisPoint]) -> List[AnalysisPoint]:
        """
        Sort analysis points by risk level from high to low.
        
        Args:
            analysis_points: List of analysis points to sort
            
        Returns:
            List[AnalysisPoint]: Sorted list with high risk first
        """
        return sorted(
            analysis_points,
            key=lambda point: self._extract_risk_level(point.risk),
            reverse=True  # High risk (3) comes first, low risk (1) comes last
        )
    
    async def analyze_document(self, request: AnalyzeRequest, db: Session, user_id: str) -> AnalyzeResponse:
        """Analyze document for legal risks and recommendations with efficient validation"""
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
            
            # Step 1: Analyze all document points (generate raw analysis points)
            analysis_start_time = datetime.now()
            analyzed_points = await self._analyze_points_concurrently(document_points, document_text, db)
            analysis_duration = (datetime.now() - analysis_start_time).total_seconds()
            
            # Step 2: Comprehensive validation with single LLM call
            validation_start_time = datetime.now()
            validated_points = await self._comprehensive_validation(analyzed_points, document_text)
            validation_duration = (datetime.now() - validation_start_time).total_seconds()
            
            # Calculate success metrics
            total_raw_analysis_points = sum(len(point.analysis_points) for point in analyzed_points)
            total_validated_analysis_points = sum(len(point.analysis_points) for point in validated_points)
            
            total_points = len(analyzed_points)
            total_duration = (datetime.now() - analysis_start).total_seconds()
            
            logger.info(
                f"Analysis completed in {total_duration:.2f}s "
                f"(parsing: {parse_duration:.2f}s, analysis: {analysis_duration:.2f}s, validation: {validation_duration:.2f}s) - "
                f"Generated {total_raw_analysis_points} raw analysis points, validated to {total_validated_analysis_points} points "
                f"across {total_points} document points"
            )
            
            # Sort analysis points within each document point by risk level (high to low)
            for analyzed_point in validated_points:
                analyzed_point.analysis_points = self._sort_analysis_points_by_risk(analyzed_point.analysis_points)
            
            # Create response with validated and sorted points
            all_analysis_points = []
            for analyzed_point in validated_points:
                all_analysis_points.extend(analyzed_point.analysis_points)
            
            response = AnalyzeResponse(
                document_points=validated_points,
                document_id=request.id,
                document_metadata=document_metadata,
                total_points=len(validated_points),
                analysis_timestamp=datetime.now().isoformat(),
                points=all_analysis_points  # For backward compatibility
            )
            
            # Save analysis results to database with user context
            try:
                analysis_result = AnalysisResult(
                    document_id=request.id,
                    user_id=user_id,
                    analysis_points=response.dict()  # Store the full response as JSON
                )
                db.add(analysis_result)
                db.commit()
                logger.info(f"Analysis results saved to database for document {request.id}, user {user_id}")
            except Exception as e:
                logger.error(f"Failed to save analysis results to database: {e}")
                db.rollback()
                # Continue execution even if database save fails
            
            return response
       
        except Exception as e:
            total_duration = (datetime.now() - analysis_start).total_seconds()
            logger.error(f"Failed to analyze document after {total_duration:.2f}s: {e}")
            raise

    async def _comprehensive_validation(
        self, 
        analyzed_points: List[DocumentPointAnalysis], 
        document_text: str
    ) -> List[DocumentPointAnalysis]:
        """
        Comprehensive validation using a single LLM call to validate all analysis points together.
        This replaces the expensive individual validation approach.
        
        Args:
            analyzed_points: List of document points with their raw analysis points
            document_text: Full document text for context
            
        Returns:
            List of document points with validated analysis points
        """
        logger.info(f"Starting comprehensive validation for {len(analyzed_points)} document points")
        
        # Collect all analysis points with their context
        all_analysis_points = []
        point_mapping = []  # Track which analysis point belongs to which document point
        
        for doc_point_idx, doc_point in enumerate(analyzed_points):
            for analysis_idx, analysis_point in enumerate(doc_point.analysis_points):
                # Skip default error analysis points
                if analysis_point.cause == "Анализ не выполнен из-за технической ошибки":
                    continue
                    
                # FIXED: ID should be the current index in all_analysis_points array
                current_id = len(all_analysis_points)
                all_analysis_points.append({
                    "id": current_id,
                    "document_point_number": doc_point.point_number,
                    "document_point_content": doc_point.point_content,
                    "cause": analysis_point.cause,
                    "risk": analysis_point.risk,
                    "recommendation": analysis_point.recommendation
                })
                # Store mapping with the correct ID that matches all_analysis_points
                point_mapping.append((doc_point_idx, analysis_idx, current_id))
        
        if not all_analysis_points:
            logger.info("No analysis points to validate")
            return analyzed_points
        
        logger.info(f"Validating {len(all_analysis_points)} analysis points in single LLM call")
        
        try:
            # Create comprehensive validation prompt
            validation_prompt = await self._create_comprehensive_validation_prompt(
                all_analysis_points, 
                document_text
            )
            
            # LLM call with retry logic for validation parsing failures
            invalid_point_ids = await self._call_validation_llm_with_retry(validation_prompt)
            
            valid_count = len(all_analysis_points) - len(invalid_point_ids)
            logger.info(f"Comprehensive validation completed: {valid_count}/{len(all_analysis_points)} points kept valid")
            
            # Apply validation results to document points
            validated_points = []
            for doc_point_idx, doc_point in enumerate(analyzed_points):
                validated_analysis_points = []
                
                # FIXED: Properly track which analysis points are invalid
                for analysis_idx, analysis_point in enumerate(doc_point.analysis_points):
                    # Always keep technical error points
                    if analysis_point.cause == "Анализ не выполнен из-за технической ошибки":
                        validated_analysis_points.append(analysis_point)
                        continue
                    
                    # Find corresponding ID in all_analysis_points
                    analysis_point_id = None
                    for mapped_doc_idx, mapped_analysis_idx, mapped_id in point_mapping:
                        if mapped_doc_idx == doc_point_idx and mapped_analysis_idx == analysis_idx:
                            analysis_point_id = mapped_id
                            break
                    
                    # Keep point if it's NOT in the invalid list (compare IDs, not indices)
                    if analysis_point_id is not None and analysis_point_id not in invalid_point_ids:
                        validated_analysis_points.append(analysis_point)
                
                validated_points.append(DocumentPointAnalysis(
                    point_number=doc_point.point_number,
                    point_content=doc_point.point_content,
                    point_type=doc_point.point_type,
                    analysis_points=validated_analysis_points
                ))
            
            return validated_points
            
        except Exception as e:
            logger.warning(f"Comprehensive validation failed ({e}), keeping all original analysis points")
            # If validation fails, keep all original analysis points
            return analyzed_points

    async def _create_comprehensive_validation_prompt(
        self, 
        all_analysis_points: List[Dict], 
        document_text: str
    ) -> str:
        """Create comprehensive validation prompt for single LLM call"""
        
        # Format all analysis points for validation
        analysis_list = []
        for point in all_analysis_points:
            analysis_list.append(f"""
ID: {point['id']}
Пункт документа #{point['document_point_number']}: {point['document_point_content'][:200]}...
Проблема: {point['cause']}
Риск: {point['risk']}
Рекомендация: {point['recommendation']}
""")
        
        analysis_text = "\n---\n".join(analysis_list)
        
        return f"""
Ты — юрист-эксперт. Проверь правовые проблемы и верни ID только НЕВАЛИДНЫХ анализов, которые были получены от другого юриста.

КОНТЕКСТ ДОКУМЕНТА:
{document_text}

НАЙДЕННЫЕ ПРОБЛЕМЫ ДЛЯ ВАЛИДАЦИИ:
{analysis_text}

ИСКЛЮЧИТЬ (вернуть ID):
- Плейсхолдеры (ФИО, email, паспорт)
- Проблемы, уже решенные в других пунктах
- Типовые формулировки
- Дубли одной проблемы
- Формальные недочеты без практического риска

Верни только массив ID невалидных анализов:
[1, 3, 7, ...]

Если все валидны - верни: []
"""

    async def _call_validation_llm_with_retry(self, validation_prompt: str) -> List[int]:
        """
        Call validation LLM with retry logic for parsing failures.
        Makes up to 2 attempts to get a parseable response.
        
        Args:
            validation_prompt: The prompt for validation
            
        Returns:
            List of invalid analysis point IDs, or empty list if parsing fails
        """
        max_attempts = 2 # TODO: move to settings or to the function parameter
        
        for attempt in range(max_attempts):
            try:
                logger.info(f"Validation LLM call attempt {attempt + 1}/{max_attempts}")
                
                # Make LLM call for validation
                validation_response = await concurrency_manager.with_llm_limit(
                    asyncio.wait_for(
                        self._call_llm(validation_prompt, temperature=0.3),
                        timeout=settings.llm_timeout * 2  # Allow more time for comprehensive validation
                    )
                )
                
                # Try to parse the response
                invalid_point_ids = self._parse_comprehensive_validation_response(validation_response)
                
                # Check if parsing was successful (we got a valid list, even if empty)
                if invalid_point_ids is not None:
                    logger.info(f"Validation LLM attempt {attempt + 1}: Successfully parsed {len(invalid_point_ids)} invalid IDs")
                    return invalid_point_ids
                else:
                    # Parsing failed
                    if attempt < max_attempts - 1:
                        logger.warning(f"Validation LLM attempt {attempt + 1}: Parsing failed, retrying...")
                        continue
                    else:
                        logger.warning(f"Validation LLM: All {max_attempts} parsing attempts failed, treating as all valid")
                        return []
                        
            except Exception as e:
                if attempt < max_attempts - 1:
                    logger.warning(f"Validation LLM attempt {attempt + 1}: Call failed ({e}), retrying...")
                    continue
                else:
                    logger.error(f"Validation LLM: All {max_attempts} attempts failed ({e}), treating as all valid")
                    return []
        
        # Fallback (should not reach here)
        return []

    def _parse_comprehensive_validation_response(self, validation_response: str) -> List[int] | None:
        """Parse comprehensive validation response to extract INVALID analysis point IDs"""
        try:
            import json
            
            if not validation_response or not validation_response.strip():
                logger.debug("Empty comprehensive validation response")
                return None
            
            text = validation_response.strip()
            
            # Try to find array directly [1, 2, 3] format
            array_start = text.find('[')
            array_end = text.rfind(']') + 1
            
            if array_start != -1 and array_end > array_start:
                array_text = text[array_start:array_end]
                
                try:
                    invalid_ids = json.loads(array_text)
                    
                    if isinstance(invalid_ids, list):
                        # Ensure all IDs are integers
                        result = [int(id_val) for id_val in invalid_ids if isinstance(id_val, (int, str)) and str(id_val).isdigit()]
                        logger.debug(f"Successfully parsed validation response: {len(result)} invalid IDs")
                        return result
                        
                except json.JSONDecodeError as e:
                    logger.debug(f"JSON decode error in validation response: {e}")
                    return None
            else:
                logger.debug("No array found in validation response")
                return None
                
        except Exception as e:
            logger.error(f"Error parsing validation response: {e}")
            return None

    async def _analyze_points_concurrently(self, document_points, document_text: str, db: Session) -> List[DocumentPointAnalysis]:
        """Analyze all document points concurrently with optimized batching and resource management"""
        
        if not document_points:
            return []
        
        total_points = len(document_points)
        logger.info(f"Starting optimized analysis of {total_points} points with concurrency limits")
        
        # Process all points with global concurrency limits
        logger.info(f"Processing {total_points} points with global concurrency limits")
        analysis_tasks = [
            concurrency_manager.with_global_limit(
                self._analyze_single_point(
                    point,
                    document_text,
                    db
                )
            )
            for point in document_points
        ]
        
        results = await asyncio.gather(*analysis_tasks, return_exceptions=True)
        
        # Process results and handle failures with detailed logging
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

    async def _analyze_single_point(self, point, document_text: str, db: Session) -> DocumentPointAnalysis:
        """Analyze a single document point"""
        point_start = datetime.now()
        logger.debug(f"Starting analysis for point {point.point_number}")
        
        try:
            # Get context from retrieval service (it will handle embedding generation internally)
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
            
            # Call LLM with retry logic for parsing failures (no individual validation)
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

    async def _get_context_from_retrieval_service(self, point_content: str, db: Session, k: int = 20) -> str:
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
            response = await retrieval_service.retrieve_rules_rrf(retrieve_request, db)
            
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
                        self._call_llm(prompt, temperature=0.7),
                        timeout=settings.llm_timeout
                    )
                )
                
                # Try to parse the response
                analysis_points = self._parse_llm_response(llm_response)
                
                logger.info(f"Point {point_number}: Parsed {len(analysis_points)} analysis points from LLM response")
                
                # Check if parsing was successful (not default fallback)
                is_parsing_successful = (
                    analysis_points is not None and 
                    (len(analysis_points) == 0 or  # Empty array is valid (no issues found)
                     analysis_points[0].cause != "Анализ не выполнен из-за технической ошибки")
                )
                
                if is_parsing_successful:
                    # Return analysis points without individual validation (will be validated comprehensively later)
                    logger.info(f"Point {point_number}: Successfully parsed {len(analysis_points)} analysis points")
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
        logger.error(f"Point {point_number}: All {max_attempts} parsing attempts failed")
        return self._get_default_analysis()



    async def _create_prompt(self, point_content: str, full_document: str) -> str:
        """Create LLM prompt for legal analysis"""
        return f"""
Ты — старший юрист-практик по договорному праву РФ. 
Твоя задача — проанализировать один конкретный пункт договора и выявить потенциальные правовые проблемы и риски, а также предложить конкретные рекомендации по улучшению. Не анализируй весь договор целиком, а только конкретный пункт.
Отвечай строго на русском.
Формат ответа — JSON.  
Не добавляй комментариев, колонтитулов, markdown или любого текста вне JSON.

КОНКРЕТНЫЙ ПУНКТ ДЛЯ АНАЛИЗА (АНАЛИЗИРУЙ ТОЛЬКО ЭТОТ ПУНКТ):
{point_content}

КОНТЕКСТ ВСЕГО ДОКУМЕНТА:
{full_document}

РЕЛЕВАНТНЫЕ ОФИЦИАЛЬНЫЕ ПРАВОВЫЕ НОРМЫ ИЗ КОДЕКСОВ Российской Федерации (которые могут помочь, но не обязательно):
{{context}}

ЗАДАЧА:
Проанализируй данный пункт договора и выявите:
1. Потенциальные причины правовых проблем (учитывай весь контекст договора, вдруг проблема решена в другом пункте)
2. Связанные с ними риски
3. Конкретные рекомендации по улучшению

ФОРМАТ ОТВЕТА:
Верни анализ в следующе строгом JSON формате:
[
  {{
    "cause": "Описание выявленной проблемы или недочета",
    "risk": "Описание риска и его уровень (Низкий/Средний/Высокий)",
    "recommendation": "Конкретная рекомендация по устранению проблемы"
  }}
]

ВАЖНО:
- Если проблем не обнаружено, верни пустой массив []
- Фокусируйся на практических правовых аспектах
- Рекомендации должны быть конкретными и применимыми
- Учитывай российское правовоезаконодательство
- Не считать ошибкой отсутствующие данные — e-mail, ФИО., паспортные реквизиты — если в договоре стоят явные плейсхолдеры, пустые места. Это не ошибка, это нормально, не надо ничего исправлять.
- ОБЯЗАТЕЛЬНО учитывай весь контекст договора: возможно, аналогичное условие уже присутствует в других пунктах договора.

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

    async def _call_llm(self, prompt: str, temperature: float = 0.3) -> str:
        """Call LLM for analysis"""
        if self.openai_client is None:
            logger.error("OpenRouter client not initialized - cannot perform LLM analysis")
            raise RuntimeError("LLM client not available - check OpenRouter configuration")
        
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
                    temperature=temperature
                )
                
                response_content = completion.choices[0].message.content
                if not response_content:
                    logger.error("Empty response received from OpenRouter API")
                    raise RuntimeError("Empty response from LLM service")
                
                logger.debug(f"LLM analysis completed. Response length: {len(response_content)}")
                return response_content
                
            except Exception as e:
                logger.error(f"OpenRouter API error: {e}")
                raise e
        
        return await asyncio.to_thread(_sync_llm_call)

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
            
            # Parse individual analysis points
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
            
            # FIXED: Empty arrays are valid responses (no issues found), not parsing failures
            if isinstance(analysis_data, list):  # Valid JSON array was parsed
                logger.debug(f"Successfully parsed {len(analysis_points)} analysis points from {len(analysis_data)} items")
                return analysis_points  # Can be empty list - that's valid!
            else:
                logger.debug("No valid analysis array found in response")
                return self._get_default_analysis()
            
        except Exception as e:
            logger.error(f"Unexpected error in LLM response parsing: {e}")
            return self._get_default_analysis()

    def _get_default_analysis(self) -> List[AnalysisPoint]:
        """Return explicit failure analysis when processing fails"""
        return [AnalysisPoint(
            cause="Анализ не выполнен из-за технической ошибки",
            risk="Неопределенный риск - требуется ручная проверка",
            recommendation="Обратитесь к разработчику или проверьте пункт вручную"
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