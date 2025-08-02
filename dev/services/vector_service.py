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
    """Simple vector database service using ChromaDB"""
    
    def __init__(self, persist_directory: str = "./chroma_db", collection_name: str = "documents"):
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
    
    def add_documents(self, doc_chunks, user_id: Optional[int] = None) -> int:
        """
        Add document chunks to the vector database
        
        Args:
            doc_chunks: List of DocumentChunk objects (simple version)
            user_id: Optional user ID for multi-user isolation
            
        Returns:
            Number of chunks successfully added
        """
        if not doc_chunks:
            print("No document chunks to add")
            return 0
        
        try:
            print(f"Adding {len(doc_chunks)} document chunks to vector database")
            
            # Prepare data for ChromaDB
            texts = []
            ids = []
            metadatas = []
            
            for chunk in doc_chunks:
                # Extract text
                texts.append(chunk.text)
                
                # Create unique ID
                chunk_id = f"{chunk.source}_{chunk.chunk_id}"
                if user_id:
                    chunk_id = f"user_{user_id}_{chunk_id}"
                ids.append(chunk_id)
                
                # Create simple metadata
                metadata = {
                    "source": chunk.source,
                    "chunk_id": chunk.chunk_id,
                    "text_length": len(chunk.text)
                }
                
                # Add user ID for multi-user isolation
                if user_id:
                    metadata["user_id"] = user_id
                
                metadatas.append(metadata)
            
            # Generate embeddings
            print("Generating embeddings...")
            embeddings = self.embedding_model.encode(
                texts, 
                show_progress_bar=len(texts) > 10,
                convert_to_numpy=True
            )
            
            # Add to ChromaDB
            self.collection.add(
                ids=ids,
                embeddings=embeddings.tolist(),
                documents=texts,
                metadatas=metadatas
            )
            
            print(f"Successfully added {len(doc_chunks)} chunks to vector database")
            return len(doc_chunks)
            
        except Exception as e:
            print(f"Error adding documents to vector database: {str(e)}")
            raise
    
    def search_similar(self, query: str, n_results: int = 3, user_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Search for similar document chunks
        
        Args:
            query: Search query
            n_results: Number of results to return
            user_id: Optional user ID for filtering results
            
        Returns:
            List of similar chunks with metadata
        """
        try:
            print(f"Searching for similar chunks: query='{query[:50]}...', n_results={n_results}")
            
            # Generate embedding for query
            query_embedding = self.embedding_model.encode([query])
            
            # Prepare where clause for user filtering
            where_clause = None
            if user_id:
                where_clause = {"user_id": user_id}
            
            # Search in vector database
            results = self.collection.query(
                query_embeddings=query_embedding.tolist(),
                n_results=n_results,
                where=where_clause,
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
                        "similarity_score": 1 - results['distances'][0][i]  # Convert distance to similarity
                    })
            
            print(f"Found {len(formatted_results)} similar chunks")
            return formatted_results
            
        except Exception as e:
            print(f"Error searching similar chunks: {str(e)}")
            return []
    
    def get_collection_stats(self, user_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Get statistics about the collection
        
        Args:
            user_id: Optional user ID for filtering stats
            
        Returns:
            Dictionary with collection statistics
        """
        try:
            # Get all documents
            where_clause = {"user_id": user_id} if user_id else None
            results = self.collection.get(
                where=where_clause,
                include=["metadatas"]
            )
            
            total_chunks = len(results['ids']) if results['ids'] else 0
            
            # Count unique sources
            sources = set()
            if results['metadatas']:
                for metadata in results['metadatas']:
                    if 'source' in metadata:
                        sources.add(metadata['source'])
            
            stats = {
                "total_chunks": total_chunks,
                "unique_documents": len(sources),
                "collection_name": self.collection_name,
                "embedding_model": self.embedding_model_name
            }
            
            if user_id:
                stats["user_id"] = user_id
            
            return stats
            
        except Exception as e:
            print(f"Error getting collection stats: {str(e)}")
            return {"error": str(e)}
    