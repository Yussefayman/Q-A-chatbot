import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.llm_provider import LLMService
from services.document_parser import DocumentService
from services.vector_service import VectorService  # Your new redesigned vector service
from services.logging_service import QueryLogger

logger = logging.getLogger(__name__)

class QAService:
    """UPDATED QA service for the new vector database design"""
    
    def __init__(self):
        """Initialize QA service with all dependencies"""
        self.llm_service = LLMService()
        self.document_service = DocumentService()
        self.vector_service = VectorService()  # New redesigned service
        self.query_logger = QueryLogger()
        
        print("QA service initialized with NEW vector service design")
    
    def process_document(self, file_path: str, user_id: int, document_id: int, filename: str) -> Dict[str, Any]:
        """
        Process a file and add it to the knowledge base - UPDATED FOR NEW DESIGN
        
        Args:
            file_path: Path to the file to process
            user_id: User ID for document isolation
            document_id: Document ID from SQL database
            filename: Original filename
            
        Returns:
            Dictionary with processing results
        """
        start_time = datetime.now()
        
        try:
            print(f"Processing file: {file_path} for user {user_id}, document {document_id}")
            
            # Process document into chunks
            doc_chunks = self.document_service.process_file(file_path)
            
            if not doc_chunks:
                return {
                    "success": False,
                    "message": "No content could be extracted from the document",
                    "chunks_created": 0,
                    "processing_time": 0
                }
            
            # Add chunks to vector database using NEW method
            chunks_added = self.vector_service.add_document(
                user_id=user_id,
                document_id=document_id,
                filename=filename,
                doc_chunks=doc_chunks
            )
            
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
    
    def ask_question(self, question: str, user_id: int, max_chunks: int = 3) -> Dict[str, Any]:
        """
        Ask a question and get an answer - UPDATED FOR USER ISOLATION
        
        Args:
            question: The user's question
            user_id: User ID for filtering results
            max_chunks: Maximum number of context chunks to use
            
        Returns:
            Dictionary with answer and metadata
        """
        start_time = datetime.now()
        
        try:
            print(f"User {user_id} asking: '{question[:50]}...'")
            
            # Search for relevant chunks using NEW method (always with user_id)
            similar_chunks = self.vector_service.search_similar(
                query=question,
                user_id=user_id,  # REQUIRED - no optional user_id anymore
                n_results=max_chunks
            )
            
            if not similar_chunks:
                response_time = (datetime.now() - start_time).total_seconds()
                answer = "I don't have any documents to search through. Please upload some documents first."
                
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
                    "answer": answer,
                    "confidence_score": 0.0,
                    "response_time": response_time,
                    "sources": [],
                    "retrieved_chunks": 0
                }
            
            # Build context from similar chunks
            context_pieces = []
            sources = []
            
            for chunk in similar_chunks:
                context_pieces.append(chunk["text"])
                # Extract source info from metadata
                metadata = chunk.get("metadata", {})
                filename = metadata.get("filename", "Unknown")
                if filename not in sources:
                    sources.append(filename)
            
            # Combine context
            context = "\n\n".join(context_pieces)
            
            # Generate answer using LLM
            print("Generating answer with LLM...")
            llm_response = self.llm_service.generate_answer(question, context)
            
            # Calculate response time
            response_time = (datetime.now() - start_time).total_seconds()
            
            # Extract answer and confidence
            answer = llm_response.get("answer", "I couldn't generate an answer.")
            confidence_score = llm_response.get("confidence_score", 0.8)
            
            # Log the query
            self.query_logger.log_query(
                user_id=user_id,
                question=question,
                answer=answer,
                response_time=response_time,
                confidence_score=confidence_score,
                sources=sources
            )
            
            print(f"✅ Generated answer for user {user_id} in {response_time:.2f}s")
            
            return {
                "answer": answer,
                "confidence_score": confidence_score,
                "response_time": response_time,
                "sources": sources,
                "retrieved_chunks": len(similar_chunks)
            }
            
        except Exception as e:
            response_time = (datetime.now() - start_time).total_seconds()
            error_answer = f"Sorry, I encountered an error while processing your question: {str(e)}"
            
            print(f"❌ Error in ask_question: {e}")
            
            # Log the error
            self.query_logger.log_query(
                user_id=user_id,
                question=question,
                answer=error_answer,
                response_time=response_time,
                confidence_score=0.0,
                sources=[]
            )
            
            return {
                "answer": error_answer,
                "confidence_score": 0.0,
                "response_time": response_time,
                "sources": [],
                "retrieved_chunks": 0
            }
    
    def delete_document(self, user_id: int, document_id: int) -> Dict[str, Any]:
        """
        Delete a document from vector database
        
        Args:
            user_id: User ID who owns the document
            document_id: Document ID to delete
            
        Returns:
            Dictionary with deletion results
        """
        try:
            chunks_deleted = self.vector_service.delete_document(user_id, document_id)
            
            return {
                "success": True,
                "message": f"Document {document_id} deleted successfully",
                "chunks_deleted": chunks_deleted
            }
            
        except Exception as e:
            print(f"❌ Error deleting document: {e}")
            return {
                "success": False,
                "message": f"Error deleting document: {str(e)}",
                "chunks_deleted": 0
            }
    
    def get_user_stats(self, user_id: int) -> Dict[str, Any]:
        """Get statistics for a specific user"""
        try:
            # Get vector stats for user
            vector_stats = self.vector_service.get_user_stats(user_id)
            
            # Get query stats for user
            query_stats = self.query_logger.get_user_queries(user_id, limit=100)
            total_queries = len(query_stats)
            
            if query_stats:
                avg_response_time = sum(q.get('response_time', 0) for q in query_stats) / len(query_stats)
            else:
                avg_response_time = 0
            
            return {
                "user_id": user_id,
                "vector_database": vector_stats,
                "queries": {
                    "total_queries": total_queries,
                    "avg_response_time": round(avg_response_time, 2)
                }
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get health status of all services"""
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