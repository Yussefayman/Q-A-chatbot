import logging
import os
import sys
from typing import List, Dict, Any
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
    
    def generate_answer(self, question: str, context_chunks: List[Dict[str, Any]]) -> str:
        """
        Generate answer using Groq LLM with retrieved context
        
        Args:
            question: The user's question
            context_chunks: List of relevant document chunks
            
        Returns:
            Generated answer from the LLM
        """
        try:
            # Prepare context from retrieved chunks
            context = self._format_context(context_chunks)
            
            # Create prompt
            prompt = self._create_prompt(question, context)
            
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
            logger.info(f"Generated answer for question: {question[:50]}...")
            return answer
            
        except Exception as e:
            logger.error(f"Error generating answer: {str(e)}")
            return f"I apologize, but I encountered an error while generating the answer: {str(e)}"
    
    def _format_context(self, context_chunks: List[Dict[str, Any]]) -> str:
        """Format context chunks into a readable string"""
        if not context_chunks:
            return "No relevant context found."
        
        formatted_context = []
        for i, chunk in enumerate(context_chunks, 1):
            source = chunk.get('metadata', {}).get('source', 'Unknown')
            text = chunk.get('text', '')
            formatted_context.append(f"[Context {i} - Source: {source}]\n{text}")
        
        return "\n\n".join(formatted_context)
    
    def _create_prompt(self, question: str, context: str) -> str:
        return f"""Based on the following context, please answer the question. If the answer cannot be found in the context, please say so clearly. Don't say in the result that it has provided context.
        Context:{context}
        Question: {question}
        Please provide a clear, concise answer based on the context provided. If you're unsure or the information isn't available in the context, please indicate that."""
    
    def _get_system_prompt(self) -> str:
        return """You are a helpful AI assistant that answers questions based on provided context. 
        Guidelines:
        - Only answer based on the provided context
        - Be clear and concise in your responses
        - If the answer isn't in the context, say so
        - Don't make up information
        - Cite relevant parts of the context when possible
        - Maintain a professional and helpful tone
        - Don't mention based on provided context sentence"""
    
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