import pytest
import io
import sqlite3
from unittest.mock import patch, Mock, mock_open
from services.document_parser import DocumentChunk

class TestHealthEndpoint:
    """Test health check functionality"""
    
    def test_health_check_success(self, client):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "version" in data

class TestAuthentication:
    """Test user registration and authentication"""
    
    def test_register_user_success(self, client, test_user):
        """Test successful user registration"""
        with patch('apis.main.get_db_connection') as mock_db:
            # Mock database connection and cursor
            mock_conn = Mock()
            mock_cursor = Mock()
            mock_cursor.lastrowid = 1
            mock_conn.cursor.return_value = mock_cursor
            mock_db.return_value = mock_conn
            
            response = client.post("/register", json=test_user)
            
            assert response.status_code == 200
            data = response.json()
            assert data["email"] == test_user["email"]
            assert data["id"] == 1
    
    def test_register_duplicate_email(self, client, test_user):
        """Test registration with existing email"""
        with patch('apis.main.get_db_connection') as mock_db:
            mock_conn = Mock()
            mock_cursor = Mock()
            mock_cursor.execute.side_effect = sqlite3.IntegrityError("UNIQUE constraint failed")
            mock_conn.cursor.return_value = mock_cursor
            mock_db.return_value = mock_conn
            
            response = client.post("/register", json=test_user)
            assert response.status_code == 400
            assert "already registered" in response.json()["detail"]
    
    def test_login_success(self, client, test_user, mock_db_user):
        """Test successful login"""
        with patch('apis.main.get_user_by_email') as mock_get_user, \
             patch('apis.main.verify_password') as mock_verify:
            
            mock_get_user.return_value = mock_db_user
            mock_verify.return_value = True
            
            response = client.post("/token", data={
                "username": test_user["email"],
                "password": test_user["password"]
            })
            
            assert response.status_code == 200
            data = response.json()
            assert "access_token" in data
            assert data["token_type"] == "bearer"
    
    def test_login_invalid_credentials(self, client, test_user):
        """Test login with wrong password"""
        with patch('apis.main.get_user_by_email') as mock_get_user:
            mock_get_user.return_value = None
            
            response = client.post("/token", data={
                "username": test_user["email"],
                "password": "wrongpassword"
            })
            
            assert response.status_code == 401

class TestDocumentUpload:
    """Test document upload functionality"""
    
    def test_upload_success(self, client, test_txt_file, mock_db_user):
        """Test successful document upload"""
        with patch('apis.main.get_current_user') as mock_user, \
             patch('apis.main.get_db_connection') as mock_db, \
             patch('apis.main.qa_service.process_document') as mock_process:
            
            # Mock user authentication
            mock_user.return_value = mock_db_user
            
            # Mock database operations
            mock_conn = Mock()
            mock_cursor = Mock()
            mock_cursor.lastrowid = 1
            mock_conn.cursor.return_value = mock_cursor
            mock_db.return_value = mock_conn
            
            # Mock QA service
            mock_process.return_value = {
                "success": True,
                "message": "Document processed successfully",
                "chunks_created": 5,
                "processing_time": 1.5
            }
            
            with open(test_txt_file, 'rb') as f:
                response = client.post(
                    "/upload",
                    files={"file": ("test.txt", f, "text/plain")},
                    headers={"Authorization": "Bearer fake-token"}
                )
            
            assert response.status_code == 200
            data = response.json()
            assert data["chunks_created"] == 5
            assert "successfully" in data["message"]
    
    def test_upload_invalid_file_type(self, client, mock_db_user):
        """Test upload with unsupported file type"""
        with patch('apis.main.get_current_user') as mock_user:
            mock_user.return_value = mock_db_user
            
            file_content = b"test content"
            response = client.post(
                "/upload",
                files={"file": ("test.docx", io.BytesIO(file_content), "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
                headers={"Authorization": "Bearer fake-token"}
            )
            
            assert response.status_code == 400
            assert "not supported" in response.json()["detail"]
    
    def test_upload_file_too_large(self, client, mock_db_user):
        """Test upload with file exceeding size limit"""
        with patch('apis.main.get_current_user') as mock_user:
            mock_user.return_value = mock_db_user
            
            # Create file larger than 10MB limit
            large_content = b"A" * (11 * 1024 * 1024)
            response = client.post(
                "/upload",
                files={"file": ("large.txt", io.BytesIO(large_content), "text/plain")},
                headers={"Authorization": "Bearer fake-token"}
            )
            
            assert response.status_code == 400
            assert "exceeds" in response.json()["detail"]

class TestQuestionAnswering:
    """Test question answering functionality"""
    
    def test_ask_question_success(self, client, mock_db_user):
        """Test successful question answering"""
        with patch('apis.main.get_current_user') as mock_user, \
             patch('apis.main.get_db_connection') as mock_db, \
             patch('apis.main.qa_service.ask_question') as mock_ask:
            
            mock_user.return_value = mock_db_user
            
            # Mock database to show user has documents
            mock_conn = Mock()
            mock_cursor = Mock()
            mock_cursor.fetchone.return_value = (1,)  # 1 document
            mock_conn.cursor.return_value = mock_cursor
            mock_db.return_value = mock_conn
            
            # Mock QA service response
            mock_ask.return_value = {
                "answer": "Artificial Intelligence (AI) is a technology that simulates human intelligence.",
                "confidence_score": 0.9,
                "response_time": 1.2,
                "sources": ["test.txt"],
                "retrieved_chunks": 2
            }
            
            response = client.post(
                "/ask",
                json={"question": "What is AI?"},
                headers={"Authorization": "Bearer fake-token"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "AI" in data["answer"]
            assert data["confidence_score"] == 0.9
            assert data["retrieved_chunks"] == 2
    
    def test_ask_empty_question(self, client, mock_db_user):
        """Test asking empty question"""
        with patch('apis.main.get_current_user') as mock_user:
            mock_user.return_value = mock_db_user
            
            response = client.post(
                "/ask",
                json={"question": "   "},
                headers={"Authorization": "Bearer fake-token"}
            )
            
            assert response.status_code == 400
            assert "cannot be empty" in response.json()["detail"]
    
    def test_ask_without_documents(self, client, mock_db_user):
        """Test asking question when user has no documents"""
        with patch('apis.main.get_current_user') as mock_user, \
             patch('apis.main.get_db_connection') as mock_db:
            
            mock_user.return_value = mock_db_user
            
            # Mock database to return 0 documents
            mock_conn = Mock()
            mock_cursor = Mock()
            mock_cursor.fetchone.return_value = (0,)  # 0 documents
            mock_conn.cursor.return_value = mock_cursor
            mock_db.return_value = mock_conn
            
            response = client.post(
                "/ask",
                json={"question": "What is AI?"},
                headers={"Authorization": "Bearer fake-token"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "don't have any documents" in data["answer"]

class TestDocumentService:
    """Test document processing service"""
    
    def test_document_service_init(self):
        """Test DocumentService initialization"""
        from services.document_parser import DocumentService
        
        service = DocumentService(chunk_size=500, chunk_overlap=50)
        assert service.chunk_size == 500
        assert service.chunk_overlap == 50
    
    def test_process_text_file(self, test_txt_file, test_file_content):
        """Test processing text file"""
        from services.document_parser import DocumentService
        
        service = DocumentService(chunk_size=100, chunk_overlap=20)
        chunks = service.process_file(test_txt_file)
        
        assert len(chunks) > 0
        assert isinstance(chunks[0], DocumentChunk)
        assert chunks[0].text in test_file_content
        assert chunks[0].source == "test_txt_file"  # filename part
    
    def test_process_nonexistent_file(self):
        """Test processing non-existent file"""
        from services.document_parser import DocumentService
        
        service = DocumentService()
        with pytest.raises(FileNotFoundError):
            service.process_file("nonexistent.txt")
    
    def test_chunk_text_simple(self):
        """Test text chunking functionality"""
        from services.document_parser import DocumentService
        
        service = DocumentService(chunk_size=50, chunk_overlap=10)
        text = "This is a test. " * 10  # 160 characters
        chunks = service._chunk_text(text)
        
        assert len(chunks) > 1
        # Each chunk should be roughly chunk_size length
        assert all(len(chunk) <= 60 for chunk in chunks)  # chunk_size + some buffer

class TestQAService:
    """Test QA Service functionality"""
    
    def test_qa_service_init(self):
        """Test QA Service initialization"""
        with patch('services.qa_service.LLMService'), \
             patch('services.qa_service.DocumentService'), \
             patch('services.qa_service.VectorService'), \
             patch('services.qa_service.QueryLogger'):
            
            from services.qa_service import QAService
            service = QAService()
            assert service is not None
    
    def test_process_document_success(self, test_txt_file):
        """Test successful document processing"""
        with patch('services.qa_service.LLMService'), \
             patch('services.qa_service.DocumentService') as mock_doc, \
             patch('services.qa_service.VectorService') as mock_vector, \
             patch('services.qa_service.QueryLogger'):
            
            from services.qa_service import QAService
            service = QAService()
            
            # Mock document service to return chunks
            mock_chunks = [
                DocumentChunk(text="chunk 1", source="test.txt", chunk_id=0),
                DocumentChunk(text="chunk 2", source="test.txt", chunk_id=1)
            ]
            mock_doc.return_value.process_file.return_value = mock_chunks
            mock_vector.return_value.add_document.return_value = 2
            
            result = service.process_document(
                test_txt_file, 
                user_id=1, 
                document_id=1, 
                filename="test.txt"
            )
            
            assert result["success"] is True
            assert result["chunks_created"] == 2
            assert result["processing_time"] > 0
    
    def test_ask_question_success(self):
        """Test successful question answering"""
        with patch('services.qa_service.LLMService') as mock_llm, \
             patch('services.qa_service.DocumentService'), \
             patch('services.qa_service.VectorService') as mock_vector, \
             patch('services.qa_service.QueryLogger') as mock_logger:
            
            from services.qa_service import QAService
            service = QAService()
            
            # Mock vector search results
            mock_vector.return_value.search_similar.return_value = [
                {"content": "AI is artificial intelligence", "metadata": {"source": "doc1.pdf"}},
                {"content": "Machine learning is AI", "metadata": {"source": "doc2.pdf"}}
            ]
            
            # Mock LLM response
            mock_llm.return_value.generate_answer.return_value = {
                "answer": "AI is artificial intelligence technology.",
                "confidence_score": 0.9
            }
            
            result = service.ask_question("What is AI?", user_id=1)
            
            assert "answer" in result
            assert result["confidence_score"] == 0.9
            assert result["retrieved_chunks"] == 2

class TestAuthenticationUtilities:
    """Test authentication utilities"""
    
    def test_password_hashing(self):
        """Test password hashing and verification"""
        from apis.main import get_password_hash, verify_password
        
        password = "testpassword123"
        hashed = get_password_hash(password)
        
        assert hashed != password
        assert verify_password(password, hashed) is True
        assert verify_password("wrongpassword", hashed) is False
    
    def test_jwt_token_creation(self):
        """Test JWT token creation"""
        from apis.main import create_access_token
        from datetime import timedelta
        
        data = {"sub": "test@example.com"}
        token = create_access_token(data, expires_delta=timedelta(minutes=30))
        
        assert isinstance(token, str)
        assert len(token) > 0

class TestIntegration:
    """Integration tests for complete workflows"""
    
    def test_complete_workflow(self, client, test_txt_file):
        """Test complete user workflow: register -> login -> upload -> ask"""
        with patch('apis.main.get_db_connection') as mock_db, \
             patch('apis.main.qa_service.process_document') as mock_process, \
             patch('apis.main.qa_service.ask_question') as mock_ask:
            
            # Mock database operations
            mock_conn = Mock()
            mock_cursor = Mock()
            mock_cursor.lastrowid = 1
            mock_cursor.fetchone.side_effect = [(1,), (1,)]  # For doc count checks
            mock_conn.cursor.return_value = mock_cursor
            mock_db.return_value = mock_conn
            
            # Mock QA service
            mock_process.return_value = {
                "success": True,
                "message": "Document processed successfully",
                "chunks_created": 3,
                "processing_time": 1.0
            }
            mock_ask.return_value = {
                "answer": "AI stands for Artificial Intelligence.",
                "confidence_score": 0.9,
                "response_time": 0.8,
                "sources": ["test.txt"],
                "retrieved_chunks": 2
            }
            
            # 1. Register
            register_response = client.post("/register", json={
                "email": "test@example.com",
                "password": "password123"
            })
            assert register_response.status_code == 200
            
            # 2. Login  
            with patch('apis.main.verify_password') as mock_verify, \
                 patch('apis.main.get_user_by_email') as mock_get_user:
                
                mock_verify.return_value = True
                mock_get_user.return_value = {
                    "id": 1,
                    "email": "test@example.com",
                    "hashed_password": "hash"
                }
                
                login_response = client.post("/token", data={
                    "username": "test@example.com",
                    "password": "password123"
                })
                assert login_response.status_code == 200
                token = login_response.json()["access_token"]
                
                # 3. Upload document
                with patch('apis.main.get_current_user') as mock_current:
                    mock_current.return_value = {"id": 1, "email": "test@example.com"}
                    
                    with open(test_txt_file, 'rb') as f:
                        upload_response = client.post(
                            "/upload",
                            files={"file": ("test.txt", f, "text/plain")},
                            headers={"Authorization": f"Bearer {token}"}
                        )
                    assert upload_response.status_code == 200
                    
                    # 4. Ask question
                    question_response = client.post(
                        "/ask",
                        json={"question": "What is AI?"},
                        headers={"Authorization": f"Bearer {token}"}
                    )
                    assert question_response.status_code == 200
                    answer_data = question_response.json()
                    assert "AI stands for" in answer_data["answer"]