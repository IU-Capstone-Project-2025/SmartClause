from typing import List, Dict, Any
from datetime import datetime
import logging
import hashlib
from sqlalchemy.orm import Session
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
        pass
    
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
Проанализируйте следующий пункт договора на предмет юридических рисков и дайте рекомендации.

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

ФОРМАТ ОТВЕТА:
Верните анализ в следующем JSON формате:
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
        return prompt
    
    async def _call_llm(self, prompt: str) -> str:
        """
        Call LLM for analysis
        TODO: Replace with your actual LLM implementation
        """
        try:
            # TODO: Implement actual LLM call
            # This could be OpenAI, local model, or any other LLM service
            
            # Example with OpenAI:
            # import openai
            # response = await openai.chat.completions.create(
            #     model="gpt-4",
            #     messages=[{"role": "user", "content": prompt}],
            #     temperature=0.3
            # )
            # return response.choices[0].message.content
            
            # Example with local model (e.g., Ollama):
            # import httpx
            # async with httpx.AsyncClient() as client:
            #     response = await client.post(
            #         "http://localhost:11434/api/generate",
            #         json={"model": "llama2", "prompt": prompt, "stream": False}
            #     )
            #     return response.json()["response"]
            
            # Example with langchain:
            # from langchain.llms import OpenAI
            # llm = OpenAI(temperature=0.3)
            # return await llm.agenerate([prompt])
            
            # For now, using mock response
            
            # Mock response for now
            mock_response = '''[
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
            
            logger.info("LLM analysis completed (mock response)")
            return mock_response
            
        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            # Return fallback analysis
            return '''[
  {
    "cause": "Ошибка при анализе с помощью ИИ",
    "risk": "Невозможно определить риски автоматически",
    "recommendation": "Необходима ручная проверка юристом"
  }
]'''
    
    def _parse_llm_response(self, llm_response: str) -> List[AnalysisPoint]:
        """
        Parse LLM response into AnalysisPoint objects
        """
        try:
            import json
            
            # Try to parse JSON response
            analysis_data = json.loads(llm_response.strip())
            
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
            logger.debug(f"LLM response was: {llm_response}")
            
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