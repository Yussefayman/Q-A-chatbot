import logging
import os
import sys
from typing import List, Dict, Any, Union
from groq import Groq
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.settings import settings

logger = logging.getLogger(__name__)

class LLMService:
    """Service for LLM operations using Groq"""
    
    def __init__(self, api_key: str = None):
        """Initialize LLM service with Groq client"""
        self.api_key = api_key or settings.groq_api_key
        if not self.api_key:
            raise ValueError("Groq API key is required")
        
        self.client = Groq(api_key=self.api_key)
        self.model = settings.groq_model
        self.temperature = settings.groq_temperature
        self.max_tokens = settings.groq_max_tokens
        
        logger.info(f"LLM service initialized with model: {self.model}")
    
    def generate_answer(self, question: str, context: Union[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
        """
        Generate answer using Groq LLM with retrieved context
        
        Args:
            question: The user's question
            context: Either a formatted context string or list of context chunks
            
        Returns:
            Dictionary with 'answer' and 'confidence_score' keys
        """
        try:
            # Handle both old and new calling patterns
            if isinstance(context, list):
                # Old format: list of context chunks
                formatted_context = self._format_context(context)
            else:
                # New format: already formatted context string
                formatted_context = context
            
            # Create prompt
            prompt = self._create_prompt(question, formatted_context)
            
            # Call Groq API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": self._get_system_prompt()
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                top_p=1,
                stream=False
            )
            
            answer = response.choices[0].message.content.strip()
            
            # Calculate confidence score based on response quality
            confidence_score = self._calculate_confidence(answer, formatted_context)
            
            logger.info(f"Generated answer for question: {question[:50]}... (confidence: {confidence_score:.2f})")
            
            return {
                "answer": answer,
                "confidence_score": confidence_score
            }
            
        except Exception as e:
            logger.error(f"Error generating answer: {str(e)}")
            return {
                "answer": f"I apologize, but I encountered an error while generating the answer: {str(e)}",
                "confidence_score": 0.0
            }
    
    def _calculate_confidence(self, answer: str, context: str) -> float:
        """
        Calculate confidence score based on answer quality and context relevance
        
        Args:
            answer: Generated answer
            context: Context used for generation
            
        Returns:
            Confidence score between 0.0 and 1.0
        """
        try:
            if not answer or len(answer.strip()) < 10:
                return 0.1
            
            # Check for uncertainty indicators
            uncertainty_phrases = [
                "i don't know", "i'm not sure", "i cannot", "unable to", 
                "not available", "insufficient information", "can't find",
                "unclear", "uncertain", "cannot determine"
            ]
            
            answer_lower = answer.lower()
            
            # Lower confidence for uncertain answers
            if any(phrase in answer_lower for phrase in uncertainty_phrases):
                return 0.3
            
            # Higher confidence for longer, detailed answers
            if len(answer) > 200:
                base_confidence = 0.9
            elif len(answer) > 100:
                base_confidence = 0.8
            elif len(answer) > 50:
                base_confidence = 0.7
            else:
                base_confidence = 0.6
            
            # Adjust based on context availability
            if not context or len(context.strip()) < 50:
                base_confidence *= 0.7
            
            return min(base_confidence, 1.0)
            
        except Exception:
            return 0.5  # Default confidence if calculation fails
    
    def _format_context(self, context_chunks: List[Dict[str, Any]]) -> str:
        """Format context chunks into a readable string"""
        if not context_chunks:
            return "No relevant context found."
        
        formatted_context = []
        for i, chunk in enumerate(context_chunks, 1):
            # Handle different chunk formats
            if isinstance(chunk, dict):
                source = chunk.get('metadata', {}).get('source', 'Unknown')
                text = chunk.get('text', chunk.get('content', ''))
            else:
                source = 'Unknown'
                text = str(chunk)
            
            if text:
                formatted_context.append(f"[Context {i} - Source: {source}]\n{text}")
        
        return "\n\n".join(formatted_context)
    
    def _create_prompt(self, question: str, context: str) -> str:
        """Create the prompt for the LLM"""
        return f"""Based on the following context, please answer the question. If the answer cannot be found in the context, please say so clearly.

Context:
{context}

Question: {question}

Please provide a clear, concise answer based on the context provided. If you're unsure or the information isn't available in the context, please indicate that."""
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt for the LLM"""
        return """You are a helpful AI assistant that answers questions based on provided context. 

Guidelines:
- Only answer based on the provided context
- Be clear and concise in your responses
- If the answer isn't in the context, say so clearly
- Don't make up information
- Cite relevant parts of the context when possible
- Maintain a professional and helpful tone
- Don't mention that you're working with provided context in your response"""
    
    def health_check(self) -> bool:
        """Check if the LLM service is healthy"""
        try:
            # Simple test call to verify API connectivity
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=10,
                temperature=0
            )
            return bool(response.choices[0].message.content)
        except Exception as e:
            logger.error(f"LLM health check failed: {str(e)}")
            return False
    