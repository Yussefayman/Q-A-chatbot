import sqlite3
import os
from datetime import datetime
from typing import Optional, List, Dict, Any

class QueryLogger:
    """Simple query logging to SQLite database"""
    
    def __init__(self, db_path: str = "qa_queries.db"):
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """Initialize SQLite database and create table"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS query_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    user_id INTEGER NOT NULL,
                    question TEXT NOT NULL,
                    answer TEXT NOT NULL,
                    response_time REAL NOT NULL,
                    confidence_score REAL,
                    sources TEXT
                )
            """)
            conn.commit()
        print(f"Query logging initialized: {self.db_path}")
    
    def log_query(self, user_id: int, question: str, answer: str, 
                  response_time: float, confidence_score: float = None, 
                  sources: List[str] = None):
        """
        Log a query to the database
        
        Args:
            user_id: ID of the user who asked the question
            question: The question that was asked
            answer: The answer that was generated
            response_time: Time taken to respond in seconds
            confidence_score: Confidence score of the answer
            sources: List of source documents used
        """
        try:
            timestamp = datetime.now().isoformat()
            sources_str = ", ".join(sources) if sources else ""
            
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO query_logs 
                    (timestamp, user_id, question, answer, response_time, confidence_score, sources)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (timestamp, user_id, question, answer, response_time, confidence_score, sources_str))
                conn.commit()
                
            print(f"Query logged for user {user_id}")
            
        except Exception as e:
            print(f"Error logging query: {e}")
    
    def get_user_queries(self, user_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent queries for a specific user
        
        Args:
            user_id: User ID to get queries for
            limit: Maximum number of queries to return
            
        Returns:
            List of query dictionaries
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row  # Enable dict-like access
                cursor = conn.execute("""
                    SELECT * FROM query_logs 
                    WHERE user_id = ? 
                    ORDER BY timestamp DESC 
                    LIMIT ?
                """, (user_id, limit))
                
                queries = []
                for row in cursor.fetchall():
                    queries.append({
                        "id": row["id"],
                        "timestamp": row["timestamp"],
                        "question": row["question"],
                        "answer": row["answer"],
                        "response_time": row["response_time"],
                        "confidence_score": row["confidence_score"],
                        "sources": row["sources"].split(", ") if row["sources"] else []
                    })
                
                return queries
                
        except Exception as e:
            print(f"Error getting user queries: {e}")
            return []
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get basic statistics about logged queries
        
        Returns:
            Dictionary with query statistics
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("SELECT COUNT(*) as total_queries FROM query_logs")
                total_queries = cursor.fetchone()[0]
                
                cursor = conn.execute("SELECT COUNT(DISTINCT user_id) as unique_users FROM query_logs")
                unique_users = cursor.fetchone()[0]
                
                cursor = conn.execute("SELECT AVG(response_time) as avg_response_time FROM query_logs")
                avg_response_time = cursor.fetchone()[0] or 0
                
                return {
                    "total_queries": total_queries,
                    "unique_users": unique_users,
                    "avg_response_time": round(avg_response_time, 2)
                }
                
        except Exception as e:
            print(f"Error getting stats: {e}")
            return {"error": str(e)}
    
    def clear_logs(self):
        """Clear all logged queries (for testing)"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("DELETE FROM query_logs")
                conn.commit()
            print("All query logs cleared")
        except Exception as e:
            print(f"Error clearing logs: {e}")