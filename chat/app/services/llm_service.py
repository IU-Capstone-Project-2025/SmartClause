from typing import List, Dict, Any, Tuple, Optional
import logging
import asyncio
from datetime import datetime
from openai import AsyncOpenAI

from ..models.database import Message, MessageType
from .retrieval_service import RetrieveResponse
from ..core.config import settings
from .retrieval_service import retrieval_service
from .document_service import document_service

logger = logging.getLogger(__name__)


class LLMService:
    """Service for generating LLM responses with legal context"""
    
    def __init__(self):
        # Initialize OpenAI client if API key is provided
        if settings.openrouter_api_key:
            self.openai_client = AsyncOpenAI(
                api_key=settings.openrouter_api_key,
                base_url="https://openrouter.ai/api/v1"
            )
            logger.info(f"LLM service initialized with model: {settings.llm_model}")
        else:
            self.openai_client = None
            logger.warning("OpenRouter API key not provided - using mock responses")
    
    async def generate_response(
        self,
        user_message: str,
        conversation_history: List[Message],
        space_id: str,
        user_id: str,
        service_token: str = None
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Generate LLM response with legal context
        
        Args:
            user_message: The user's input message
            conversation_history: Previous messages for context
            space_id: Space ID for context
            user_id: User ID
            service_token: JWT token for service-to-service calls
            
        Returns:
            Tuple of (response_text, metadata)
        """
        try:
            # Get document analysis context from the same space
            space_documents = await document_service.get_space_documents_with_analysis(space_id, user_id, service_token)
            logger.info(f"Retrieved space documents: {space_documents}")
            document_analysis_context = document_service.format_analysis_for_llm(space_documents)
            logger.info(f"Formatted document analysis context: '{document_analysis_context[:200]}...' ({len(document_analysis_context)} chars)")
            
            # Extract legal concepts from documents for better RAG queries
            legal_concepts = self._extract_legal_concepts_from_documents(space_documents)
            
            # Get legal rules context using extracted concepts (if available) or user question as fallback
            legal_response = None
            if legal_concepts:
                # Use extracted legal concepts as queries for better retrieval
                query_for_rag = " ".join(legal_concepts[:3])  # Use top 3 concepts
                logger.debug(f"Using extracted legal concepts as RAG query: '{query_for_rag}'")
            else:
                # Fallback to user question if no documents or analysis available
                query_for_rag = user_message
                logger.debug(f"Using user question as RAG query (no document concepts): '{query_for_rag[:50]}...'")
            
            legal_response = await retrieval_service.retrieve_legal_rules(
                query=query_for_rag,
                k=20
            )
            
            # Format conversation history for LLM
            conversation_context = self._format_conversation_history(conversation_history)
            
            # Format retrieved legal rules for LLM
            legal_context = ""
            if legal_response:
                legal_context = retrieval_service.format_rules_for_llm(legal_response)
            
            # Generate response using LLM
            if self.openai_client:
                response_text = await self._generate_llm_response(
                    user_message=user_message,
                    conversation_context=conversation_context,
                    legal_context=legal_context,
                    document_analysis_context=document_analysis_context
                )
            else:
                response_text = self._generate_mock_response(user_message, legal_response, space_documents)
            
            # Prepare metadata
            metadata = {
                "document_references": self._extract_document_references(legal_response),
                "retrieval_context": {
                    "legal_rules_count": len(legal_response.results) if legal_response else 0,
                    "query": legal_response.query if legal_response else user_message,
                    "query_strategy": "concept_based" if legal_concepts else "user_question",
                    "extracted_concepts": legal_concepts if legal_concepts else []
                },
                "document_analysis_context": {
                    "total_documents": space_documents.get("total_documents", 0),
                    "analyzed_documents": space_documents.get("analyzed_documents", 0),
                    "documents_included": bool(document_analysis_context)
                },
                "analysis_context": {
                    "space_id": space_id,
                    "conversation_length": len(conversation_history),
                    "timestamp": datetime.utcnow().isoformat(),
                    "llm_model": settings.llm_model,
                    "llm_temperature": settings.llm_temperature
                }
            }
            
            logger.info(f"Generated response for user {user_id} in space {space_id} using {settings.llm_model}")
            return response_text, metadata
            
        except Exception as e:
            logger.error(f"Error generating LLM response: {e}")
            # Return fallback response
            return self._get_fallback_response(), {}
    
    async def _generate_llm_response(
        self,
        user_message: str,
        conversation_context: str,
        legal_context: str,
        document_analysis_context: str = ""
    ) -> str:
        """Generate response using OpenRouter LLM"""
        try:
            # Build the system prompt
            system_prompt = self._build_system_prompt()
            
            # Build the user prompt with context
            user_prompt = self._build_user_prompt(
                user_message=user_message,
                conversation_context=conversation_context,
                legal_context=legal_context,
                document_analysis_context=document_analysis_context
            )
            
            # Make API call to OpenRouter with configured model
            response = await self.openai_client.chat.completions.create(
                model=settings.llm_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=settings.llm_max_tokens,
                temperature=settings.llm_temperature
            )
            
            response_text = response.choices[0].message.content.strip()
            logger.debug(f"LLM response generated using {settings.llm_model}: {len(response_text)} characters")
            return response_text
            
        except Exception as e:
            logger.error(f"Error calling OpenRouter API with model {settings.llm_model}: {e}")
            return self._get_fallback_response()
    
    def _build_system_prompt(self) -> str:
        """Build the system prompt for the LLM"""
        return """You are a legal AI assistant specialized in Russian legal documents and codes. Your role is to:

1. Analyze legal documents and provide expert insights
2. Answer questions about Russian legal regulations and codes
3. Explain legal concepts in clear, understandable language
4. Reference specific legal articles and rules when applicable
5. Provide practical recommendations based on legal analysis

Guidelines:
- Always cite specific legal sources when making legal statements
- Explain complex legal terms in simple language
- Be precise and accurate in your legal interpretations
- If you're uncertain about something, acknowledge the limitation
- Focus on being helpful while maintaining legal accuracy
- Respond in the same language as the user's question

You have access to:
- Russian legal codes and regulations database
- User's uploaded legal documents and their analysis
- Previous conversation context

Provide clear, actionable, and legally sound advice."""

    def _build_user_prompt(
        self,
        user_message: str,
        conversation_context: str,
        legal_context: str,
        document_analysis_context: str = ""
    ) -> str:
        """Build the user prompt with all context"""
        prompt_parts = []
        
        # Add conversation history if available
        if conversation_context.strip():
            prompt_parts.append("=== CONVERSATION HISTORY ===")
            prompt_parts.append(conversation_context)
            prompt_parts.append("")
        
        # Add legal context if available
        if legal_context.strip():
            prompt_parts.append(legal_context)
            prompt_parts.append("")
        
        # Add document analysis context if available
        if document_analysis_context.strip():
            prompt_parts.append(document_analysis_context)
            prompt_parts.append("")
        
        # Add current user message
        prompt_parts.append("=== USER QUESTION ===")
        prompt_parts.append(user_message)
        prompt_parts.append("")
        prompt_parts.append("Please provide a comprehensive response based on the available legal context, document analysis, and conversation history.")
        
        return "\n".join(prompt_parts)
    
    def _format_conversation_history(self, messages: List[Message]) -> str:
        """Format conversation history for LLM context"""
        try:
            if not messages:
                return ""
            
            formatted_messages = []
            for message in messages[-10:]:  # Last 10 messages to avoid token limits
                role = "User" if message.type == MessageType.USER else "Assistant"
                timestamp = message.timestamp.strftime("%H:%M")
                formatted_messages.append(f"[{timestamp}] {role}: {message.content}")
            
            return "\n".join(formatted_messages)
            
        except Exception as e:
            logger.error(f"Error formatting conversation history: {e}")
            return ""
    
    def _extract_document_references(self, legal_response: Optional[RetrieveResponse]) -> List[Dict[str, Any]]:
        """Extract document references from legal rules response"""
        references = []
        
        try:
            if not legal_response:
                return references
                
            # Extract from legal rules
            for rule in legal_response.results:
                metadata = rule.metadata
                if metadata.get("file_name"):
                    references.append({
                        "type": "legal_rule",
                        "file_name": metadata.get("file_name"),
                        "rule_title": metadata.get("rule_title"),
                        "rule_number": metadata.get("rule_number"),
                        "similarity_score": rule.similarity_score
                    })
            
            return references
            
        except Exception as e:
            logger.error(f"Error extracting document references: {e}")
            return []
    
    def _extract_legal_concepts_from_documents(self, space_documents: Dict[str, Any]) -> List[str]:
        """
        Extract legal concepts from document analysis for better RAG queries.
        
        Instead of using the user's meta-question directly, we extract actual legal
        concepts from the analyzed documents to create more targeted RAG queries.
        """
        concepts = []
        
        try:
            documents = space_documents.get("documents", [])
            
            for doc in documents:
                analysis = doc.get("analysis")
                if not analysis:
                    continue
                
                # Extract concepts from document analysis points
                document_points = analysis.get("document_points", [])
                for point in document_points:
                    analysis_points = point.get("analysis_points", [])
                    
                    for ap in analysis_points:
                        # Extract risk concepts (these often contain legal terms)
                        risk = ap.get("risk", "")
                        if risk:
                            # Extract key legal terms from risk descriptions
                            risk_concepts = self._extract_key_terms_from_text(risk)
                            concepts.extend(risk_concepts)
                        
                        # Extract recommendation concepts
                        recommendation = ap.get("recommendation", "")
                        if recommendation:
                            rec_concepts = self._extract_key_terms_from_text(recommendation)
                            concepts.extend(rec_concepts)
                
                # Extract concepts from document metadata if available
                metadata = analysis.get("document_metadata", {})
                title = metadata.get("title", "")
                if title:
                    title_concepts = self._extract_key_terms_from_text(title)
                    concepts.extend(title_concepts)
            
            # Remove duplicates and filter out too short/generic terms
            unique_concepts = list(set(concepts))
            filtered_concepts = [c for c in unique_concepts if len(c) > 3 and c.lower() not in 
                               {'документ', 'статья', 'пункт', 'часть', 'может', 'должен', 'если', 'того', 'этом', 'при'}]
            
            logger.debug(f"Extracted {len(filtered_concepts)} legal concepts from {len(documents)} documents")
            return filtered_concepts[:10]  # Return top 10 concepts
            
        except Exception as e:
            logger.error(f"Error extracting legal concepts: {e}")
            return []
    
    def _extract_key_terms_from_text(self, text: str) -> List[str]:
        """Extract key legal terms from a text string."""
        if not text or len(text) < 5:
            return []
        
        # Simple extraction - look for legal keywords and important phrases
        legal_keywords = [
            'ответственность', 'обязательство', 'договор', 'соглашение', 'штраф', 'неустойка',
            'гарантия', 'залог', 'поручительство', 'страхование', 'компенсация', 'возмещение',
            'нарушение', 'исполнение', 'прекращение', 'расторжение', 'изменение', 'дополнение',
            'срок', 'платеж', 'оплата', 'цена', 'стоимость', 'налог', 'пошлина',
            'право', 'обязанность', 'полномочие', 'компетенция', 'юрисдикция', 'подсудность',
            'собственность', 'владение', 'пользование', 'распоряжение', 'аренда', 'лизинг',
            'интеллектуальная собственность', 'авторское право', 'товарный знак', 'патент',
            'конфиденциальность', 'коммерческая тайна', 'персональные данные', 'защита информации',
            'форс-мажор', 'непреодолимая сила', 'обстоятельства', 'риск', 'ущерб', 'убыток'
        ]
        
        text_lower = text.lower()
        found_terms = []
        
        for keyword in legal_keywords:
            if keyword in text_lower:
                found_terms.append(keyword)
        
        # Also extract phrases that might be legal concepts (2-4 words)
        words = text.split()
        for i in range(len(words) - 1):
            phrase = ' '.join(words[i:i+2]).strip('.,;:!?').lower()
            if any(keyword in phrase for keyword in legal_keywords):
                found_terms.append(phrase)
        
        return found_terms

    def _generate_mock_response(self, user_message: str, legal_response: Optional[RetrieveResponse], space_documents: Dict[str, Any] = None) -> str:
        """Generate a mock response when LLM is not available"""
        legal_rules_count = len(legal_response.results) if legal_response else 0
        
        # Include document analysis information
        document_info = ""
        if space_documents:
            total_docs = space_documents.get("total_documents", 0)
            analyzed_docs = space_documents.get("analyzed_documents", 0)
            document_info = f"\n\nДокументы в этом пространстве: {total_docs} (анализ доступен для {analyzed_docs})"
        
        return f"""Благодарю за ваш вопрос: "{user_message}"

На основе анализа правовой базы данных я нашел {legal_rules_count} релевантных правовых норм.{document_info}

[ДЕМО-РЕЖИМ: Настоящий ответ будет сгенерирован после настройки OpenRouter API ключа]

Текущая конфигурация:
- Модель: {settings.llm_model}
- Температура: {settings.llm_temperature}
- Максимум токенов: {settings.llm_max_tokens}

Для получения подробного правового анализа, пожалуйста, убедитесь, что:
1. Настроен API ключ OpenRouter (OPENROUTER_API_KEY)
2. Документы загружены в систему для анализа
3. Правовая база данных содержит актуальную информацию

Могу ли я помочь вам с чем-то еще?"""
    
    def _get_fallback_response(self) -> str:
        """Get fallback response for errors"""
        return """Извините, возникла техническая ошибка при генерации ответа.

Пожалуйста, попробуйте:
1. Переформулировать ваш вопрос
2. Проверить, что документы загружены корректно
3. Обратиться к администратору, если проблема повторяется

Я готов помочь вам снова, как только проблема будет решена."""


# Global LLM service instance
llm_service = LLMService() 