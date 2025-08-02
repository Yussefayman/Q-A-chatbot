import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.llm_provider import LLMService
from services.document_parser import DocumentService
from services.vector_service import VectorService
from services.logging_service import QueryLogger

logger = logging.getLogger(__name__)

class QAService:
    """Simple QA service for file-based document processing with logging"""
    
    def __init__(self):
        """Initialize QA service with all dependencies"""
        self.llm_service = LLMService()
        self.document_service = DocumentService()
        self.vector_service = VectorService()
        self.query_logger = QueryLogger()  # Add query logger
        
        print("QA service initialized with logging")
    
    def process_file(self, file_path: str, user_id: int = 1) -> Dict[str, Any]:
        """
        Process a file and add it to the knowledge base
        
        Args:
            file_path: Path to the file to process
            user_id: User ID for document isolation
            
        Returns:
            Dictionary with processing results
        """
        start_time = datetime.now()
        
        try:
            print(f"Processing file: {file_path}")
            
            # Process document into chunks
            doc_chunks = self.document_service.process_file(file_path)
            
            if not doc_chunks:
                return {
                    "success": False,
                    "message": "No content could be extracted from the document",
                    "chunks_created": 0
                }
            
            # Add chunks to vector database
            chunks_added = self.vector_service.add_documents(doc_chunks, user_id)
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            return {
                "success": True,
                "message": "Document processed successfully",
                "chunks_created": chunks_added,
                "processing_time": processing_time
            }
            
        except Exception as e:
            processing_time = (datetime.now() - start_time).total_seconds()
            print(f"Error processing file: {e}")
            
            return {
                "success": False,
                "message": f"Error processing document: {str(e)}",
                "chunks_created": 0,
                "processing_time": processing_time
            }
    
    def ask_question(self, question: str, user_id: int = 1, max_chunks: int = 3) -> Dict[str, Any]:
        """
        Ask a question and get an answer based on processed documents with logging
        
        Args:
            question: The user's question
            user_id: User ID for filtering results
            max_chunks: Maximum number of context chunks to use
            
        Returns:
            Dictionary with answer and metadata
        """
        start_time = datetime.now()
        
        try:
            # Search for relevant chunks
            similar_chunks = self.vector_service.search_similar(
                query=question,
                n_results=max_chunks,
                user_id=user_id
            )
            
            if not similar_chunks:
                response_time = (datetime.now() - start_time).total_seconds()
                answer = "I couldn't find any relevant information to answer your question. Please make sure you have processed a relevant document first."
                
                # Log the query
                self.query_logger.log_query(
                    user_id=user_id,
                    question=question,
                    answer=answer,
                    response_time=response_time,
                    confidence_score=0.0,
                    sources=[]
                )
                
                return {
                    "question": question,
                    "answer": answer,
                    "sources": [],
                    "response_time": response_time,
                    "retrieved_chunks": 0,
                    "confidence_score": 0.0
                }
            
            # Generate answer using LLM
            answer = self.llm_service.generate_answer(question, similar_chunks)
            
            # Extract sources
            sources = list(set([
                chunk.get('metadata', {}).get('source', chunk.get('source', 'Unknown'))
                for chunk in similar_chunks
            ]))
            
            # Calculate confidence (simple average of similarity scores)
            avg_similarity = 0.0
            if similar_chunks:
                similarity_scores = [chunk.get('similarity_score', 0) for chunk in similar_chunks]
                avg_similarity = sum(similarity_scores) / len(similarity_scores)
            
            response_time = (datetime.now() - start_time).total_seconds()
            confidence_score = round(avg_similarity, 3)
            
            # Log the query
            self.query_logger.log_query(
                user_id=user_id,
                question=question,
                answer=answer,
                response_time=response_time,
                confidence_score=confidence_score,
                sources=sources
            )
            
            return {
                "question": question,
                "answer": answer,
                "sources": sources,
                "response_time": response_time,
                "retrieved_chunks": len(similar_chunks),
                "confidence_score": confidence_score
            }
            
        except Exception as e:
            response_time = (datetime.now() - start_time).total_seconds()
            answer = f"I encountered an error while processing your question: {str(e)}"
            print(f"Error processing question: {e}")
            
            # Log the error query
            self.query_logger.log_query(
                user_id=user_id,
                question=question,
                answer=answer,
                response_time=response_time,
                confidence_score=0.0,
                sources=[]
            )
            
            return {
                "question": question,
                "answer": answer,
                "sources": [],
                "response_time": response_time,
                "retrieved_chunks": 0,
                "confidence_score": 0.0
            }
    
    def get_query_history(self, user_id: int = 1, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get query history for a user
        
        Args:
            user_id: User ID to get history for
            limit: Maximum number of queries to return
            
        Returns:
            List of previous queries
        """
        return self.query_logger.get_user_queries(user_id, limit)
    
    def get_query_stats(self) -> Dict[str, Any]:
        """
        Get statistics about all queries
        
        Returns:
            Dictionary with query statistics
        """
        return self.query_logger.get_stats()
    
    def health_check(self) -> Dict[str, Any]:
        """Check if all services are working"""
        health_status = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "services": {}
        }
        
        # Check each service
        services = {
            "llm_service": self.llm_service,
            "document_service": self.document_service,
            "vector_service": self.vector_service
        }
        
        all_healthy = True
        for service_name, service in services.items():
            try:
                if hasattr(service, 'health_check'):
                    is_healthy = service.health_check()
                    health_status["services"][service_name] = "healthy" if is_healthy else "unhealthy"
                    if not is_healthy:
                        all_healthy = False
                else:
                    health_status["services"][service_name] = "healthy"
            except Exception as e:
                health_status["services"][service_name] = f"error: {str(e)}"
                all_healthy = False
        
        # Check logging service
        try:
            stats = self.query_logger.get_stats()
            health_status["services"]["query_logger"] = "healthy" if "error" not in stats else "unhealthy"
        except Exception as e:
            health_status["services"]["query_logger"] = f"error: {str(e)}"
            all_healthy = False
        
        if not all_healthy:
            health_status["status"] = "degraded"
        
        return health_status
    
    def get_stats(self, user_id: int = 1) -> Dict[str, Any]:
        """Get statistics about processed documents and queries"""
        try:
            vector_stats = self.vector_service.get_collection_stats(user_id)
            query_stats = self.query_logger.get_stats()
            
            return {
                "documents": vector_stats,
                "queries": query_stats
            }
        except Exception as e:
            return {"error": str(e)}