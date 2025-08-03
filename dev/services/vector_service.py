import logging
import warnings
import os
from typing import List, Dict, Any, Optional

# Disable telemetry
os.environ.update({
    "ANONYMIZED_TELEMETRY": "False",
    "CHROMA_TELEMETRY": "False",
    "CHROMA_DISABLE_TELEMETRY": "True"
})
warnings.filterwarnings("ignore", message=".*telemetry.*")

import chromadb
from chromadb.config import Settings as ChromaSettings
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

class VectorService:
    """REDESIGNED Simple vector database service using ChromaDB"""
    
    def __init__(self, persist_directory: str = "./chroma_db", collection_name: str = "user_documents"):
        self.persist_directory = persist_directory
        self.collection_name = collection_name
        self.embedding_model_name = "all-MiniLM-L6-v2"
        
        # Initialize ChromaDB client with persistence
        self.chroma_client = chromadb.PersistentClient(
            path=self.persist_directory,
            settings=ChromaSettings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        # Initialize embedding model
        print(f"Loading embedding model: {self.embedding_model_name}")
        self.embedding_model = SentenceTransformer(self.embedding_model_name)
        
        # Get or create collection
        self.collection = self._get_or_create_collection()
        
        print(f"Vector service initialized with collection: {self.collection_name}")
    
    def _get_or_create_collection(self):
        """Get existing collection or create new one"""
        try:
            # Try to get existing collection
            collection = self.chroma_client.get_collection(
                name=self.collection_name,
                embedding_function=None 
            )
            print(f"Using existing collection: {self.collection_name}")
            return collection
        except Exception:
            # Create new collection if it doesn't exist
            collection = self.chroma_client.create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"},
                embedding_function=None  
            )
            print(f"Created new collection: {self.collection_name}")
            return collection
    
    def add_document(self, user_id: int, document_id: int, filename: str, doc_chunks) -> int:
        """
        Add document chunks to the vector database - REDESIGNED SIMPLE VERSION
        
        Args:
            user_id: User ID who owns the document
            document_id: Document ID from SQL database
            filename: Original filename
            doc_chunks: List of DocumentChunk objects
            
        Returns:
            Number of chunks successfully added
        """
        if not doc_chunks:
            print("No document chunks to add")
            return 0
        
        try:
            print(f"Adding {len(doc_chunks)} chunks for user {user_id}, document {document_id}")
            
            # Prepare data for ChromaDB - SIMPLE STRUCTURE
            texts = []
            ids = []
            metadatas = []
            
            for i, chunk in enumerate(doc_chunks):
                # SIMPLE ID FORMAT: user_id + document_id + chunk_number
                chunk_id = f"{user_id}_{document_id}_{i}"
                ids.append(chunk_id)
                
                # Extract text
                texts.append(chunk.text)
                
                # SIMPLE METADATA - Only what we need
                metadata = {
                    "user_id": user_id,           # For user isolation
                    "document_id": document_id,   # For document deletion
                    "filename": filename,         # For reference
                    "chunk_index": i              # For ordering
                }
                metadatas.append(metadata)
            
            # Generate embeddings
            print("Generating embeddings...")
            embeddings = self.embedding_model.encode(
                texts, 
                show_progress_bar=len(texts) > 5,
                convert_to_numpy=True
            )
            
            # Add to ChromaDB
            self.collection.add(
                ids=ids,
                embeddings=embeddings.tolist(),
                documents=texts,
                metadatas=metadatas
            )
            
            print(f"✅ Successfully added {len(doc_chunks)} chunks to vector database")
            return len(doc_chunks)
            
        except Exception as e:
            print(f"❌ Error adding documents to vector database: {str(e)}")
            raise
    
    def search_similar(self, query: str, user_id: int, n_results: int = 3) -> List[Dict[str, Any]]:
        """
        Search for similar document chunks - USER ISOLATED
        
        Args:
            query: Search query
            user_id: User ID for filtering results
            n_results: Number of results to return
            
        Returns:
            List of similar chunks with metadata
        """
        try:
            print(f"Searching for user {user_id}: '{query[:50]}...', n_results={n_results}")
            
            # Generate embedding for query
            query_embedding = self.embedding_model.encode([query])
            
            # Search with user filter - SIMPLE WHERE CLAUSE
            results = self.collection.query(
                query_embeddings=query_embedding.tolist(),
                n_results=n_results,
                where={"user_id": user_id},  # ONLY USER'S DOCUMENTS
                include=["documents", "metadatas", "distances"]
            )
            
            # Format results
            formatted_results = []
            if results['documents'] and results['documents'][0]:
                for i in range(len(results['documents'][0])):
                    formatted_results.append({
                        "text": results['documents'][0][i],
                        "metadata": results['metadatas'][0][i],
                        "distance": results['distances'][0][i],
                        "similarity_score": 1 - results['distances'][0][i]
                    })
            
            print(f"Found {len(formatted_results)} similar chunks for user {user_id}")
            return formatted_results
            
        except Exception as e:
            print(f"❌ Error searching similar chunks: {str(e)}")
            return []
    
    def delete_document(self, user_id: int, document_id: int) -> int:
        """
        Delete all chunks for a specific document - BULLETPROOF VERSION
        
        Args:
            user_id: User ID who owns the document
            document_id: Document ID to delete
            
        Returns:
            Number of chunks deleted
        """
        try:
            print(f"Deleting document {document_id} for user {user_id}")
            
            # Get all chunks for this user and document
            results = self.collection.get(
                where={
                    "user_id": user_id,
                    "document_id": document_id
                },
                include=["metadatas"]
            )
            
            if results['ids']:
                # Delete all matching chunks
                self.collection.delete(ids=results['ids'])
                deleted_count = len(results['ids'])
                print(f"✅ Deleted {deleted_count} chunks for document {document_id}")
                return deleted_count
            else:
                print(f"⚠️ No chunks found for document {document_id}")
                return 0
                
        except Exception as e:
            print(f"❌ Error deleting document from vector database: {str(e)}")
            raise
    
    def delete_user_documents(self, user_id: int) -> int:
        """
        Delete ALL documents for a user
        
        Args:
            user_id: User ID to delete all documents for
            
        Returns:
            Number of chunks deleted
        """
        try:
            print(f"Deleting ALL documents for user {user_id}")
            
            # Get all chunks for this user
            results = self.collection.get(
                where={"user_id": user_id},
                include=["metadatas"]
            )
            
            if results['ids']:
                # Delete all user's chunks
                self.collection.delete(ids=results['ids'])
                deleted_count = len(results['ids'])
                print(f"✅ Deleted {deleted_count} chunks for user {user_id}")
                return deleted_count
            else:
                print(f"No chunks found for user {user_id}")
                return 0
                
        except Exception as e:
            print(f"❌ Error deleting user documents: {str(e)}")
            raise
    
    def get_user_stats(self, user_id: int) -> Dict[str, Any]:
        """
        Get statistics for a specific user
        
        Args:
            user_id: User ID to get stats for
            
        Returns:
            Dictionary with user statistics
        """
        try:
            # Get all user's documents
            results = self.collection.get(
                where={"user_id": user_id},
                include=["metadatas"]
            )
            
            total_chunks = len(results['ids']) if results['ids'] else 0
            
            # Count unique documents
            unique_documents = set()
            if results['metadatas']:
                for metadata in results['metadatas']:
                    unique_documents.add(metadata['document_id'])
            
            return {
                "user_id": user_id,
                "total_chunks": total_chunks,
                "unique_documents": len(unique_documents),
                "collection_name": self.collection_name
            }
            
        except Exception as e:
            print(f"❌ Error getting user stats: {str(e)}")
            return {"error": str(e)}
    
    def reset_collection(self) -> bool:
        """
        NUCLEAR OPTION: Reset entire collection
        """
        try:
            # Delete the collection
            self.chroma_client.delete_collection(name=self.collection_name)
            
            # Recreate it
            self.collection = self.chroma_client.create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"},
                embedding_function=None
            )
            
            print("✅ Collection reset successfully")
            return True
            
        except Exception as e:
            print(f"❌ Error resetting collection: {str(e)}")
            return False