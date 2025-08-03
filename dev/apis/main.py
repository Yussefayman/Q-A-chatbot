from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from jose import JWTError, jwt
from datetime import datetime, timedelta
import sqlite3
import uvicorn
import os
import sys
import hashlib
import secrets
from typing import Optional, List
from passlib.context import CryptContext
# Add parent directory to path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

# Load environment variables
from dotenv import load_dotenv
load_dotenv(os.path.join(parent_dir, '.env'))

# Import your existing services
from services.qa_service import QAService
from config.settings import settings

# Initialize services
qa_service = QAService()

# Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-this-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days

# Password hashing - Alternative implementation if bcrypt fails
try:
    # Try bcrypt first
    pwd_context = CryptContext(
        schemes=["bcrypt"], 
        deprecated="auto",
        bcrypt__rounds=12
    )
    # Test bcrypt
    test_hash = pwd_context.hash("test")
    print("✅ bcrypt working correctly")
except Exception as e:
    print(f"⚠️ bcrypt error: {e}")
    print("Using argon2 as fallback...")
    # Fallback to argon2
    pwd_context = CryptContext(
        schemes=["argon2"],
        deprecated="auto"
    )

# FastAPI app
app = FastAPI(
    title="QuestAI - Question Answering API",
    description="AI-powered question answering service with document upload and vector search",
    version="1.0.0",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class UserCreate(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: int
    email: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

class QuestionRequest(BaseModel):
    question: str

class QuestionResponse(BaseModel):
    question: str
    answer: str
    sources: List[str] = []
    response_time: float
    retrieved_chunks: int = 0
    confidence_score: Optional[float] = None

class DocumentUploadResponse(BaseModel):
    message: str
    document_id: str
    chunks_created: int
    processing_time: float

class HealthCheck(BaseModel):
    status: str
    timestamp: datetime
    version: str
    services: dict

# Database path
DB_PATH = "../dbs/users.db"

def init_db():
    """Initialize SQLite database"""
    os.makedirs("../dbs", exist_ok=True)
    
    conn = None
    try:
        conn = sqlite3.connect('../dbs/users.db', timeout=20.0)
        cursor = conn.cursor()
        
        # Enable WAL mode for better concurrency
        cursor.execute('PRAGMA journal_mode=WAL;')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                hashed_password TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                filename TEXT NOT NULL,
                file_size INTEGER NOT NULL,
                chunks_count INTEGER DEFAULT 0,
                upload_time DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        conn.commit()
        print("Database initialized successfully")
        
    except Exception as e:
        print(f"Error initializing database: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()

def get_db_connection():
    """Get database connection with timeout and lock handling"""
    conn = sqlite3.connect('../dbs/users.db', timeout=20.0)
    conn.row_factory = sqlite3.Row
    # Enable WAL mode for better concurrency
    conn.execute('PRAGMA journal_mode=WAL;')
    return conn

# Password utilities
def verify_password(plain_password, hashed_password):
    """Verify a plain password against a hashed password"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    """Hash a password"""
    return pwd_context.hash(password)

# JWT utilities
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create a JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer())):
    """Verify JWT token"""
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        token_data = TokenData(email=email)
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return token_data

# Database operations
def create_user(email: str, password: str):
    """Create a new user in the database"""
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        hashed_password = get_password_hash(password)
        cursor.execute(
            "INSERT INTO users (email, hashed_password) VALUES (?, ?)",
            (email, hashed_password)
        )
        conn.commit()
        user_id = cursor.lastrowid
        return {"id": user_id, "email": email}
        
    except sqlite3.IntegrityError:
        if conn:
            conn.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    except sqlite3.Error as e:
        if conn:
            conn.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )
    finally:
        if conn:
            conn.close()

def get_user_by_email(email: str):
    """Get user by email from database"""
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
        user = cursor.fetchone()
        
        if user:
            return {
                "id": user["id"],
                "email": user["email"],
                "hashed_password": user["hashed_password"]
            }
        return None
        
    except sqlite3.Error as e:
        print(f"Database error in get_user_by_email: {e}")
        return None
    finally:
        if conn:
            conn.close()

def authenticate_user(email: str, password: str):
    """Authenticate user with email and password"""
    user = get_user_by_email(email)
    if not user:
        return False
    if not verify_password(password, user["hashed_password"]):
        return False
    return user

def get_current_user(token_data: TokenData = Depends(verify_token)):
    """Get current user from token"""
    user = get_user_by_email(token_data.email)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user

# API Endpoints
@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    init_db()
    print("QuestAI API started successfully!")

@app.get("/health", response_model=HealthCheck)
async def health_check():
    """Health check endpoint"""
    return HealthCheck(
        status="healthy",
        timestamp=datetime.utcnow(),
        version="1.0.0",
        services={
            "database": "healthy",
            "auth": "healthy",
            "qa_service": "healthy"
        }
    )

@app.post("/register", response_model=UserResponse)
async def register_user(user: UserCreate):
    """Register a new user"""
    created_user = create_user(user.email, user.password)
    return UserResponse(id=created_user["id"], email=created_user["email"])

@app.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """Login endpoint - returns JWT token"""
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["email"]}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    """Upload and process a document"""
    # Validate file type
    allowed_types = [".txt", ".pdf"]
    file_extension = os.path.splitext(file.filename)[1].lower()
    if file_extension not in allowed_types:
        raise HTTPException(
            status_code=400, 
            detail=f"File type {file_extension} not supported. Allowed: {allowed_types}"
        )
    
    # Validate file size
    content = await file.read()
    max_size = settings.max_file_size_mb * 1024 * 1024
    if len(content) > max_size:
        raise HTTPException(
            status_code=400, 
            detail=f"File size exceeds {settings.max_file_size_mb}MB limit"
        )
    
    # Save file temporarily
    temp_dir = "temp_uploads"
    os.makedirs(temp_dir, exist_ok=True)
    temp_file_path = os.path.join(temp_dir, f"{current_user['id']}_{file.filename}")
    
    with open(temp_file_path, "wb") as f:
        f.write(content)
    
    try:
        # Save document metadata to SQL first
        conn = None
        doc_id = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO documents (user_id, filename, file_size, chunks_count, upload_time)
                VALUES (?, ?, ?, ?, ?)
            """, (current_user['id'], file.filename, len(content), 0, datetime.utcnow().isoformat()))
            doc_id = cursor.lastrowid
            conn.commit()
            print(f"✅ SQL: Created document {doc_id} for user {current_user['id']}")
        except sqlite3.Error as e:
            if conn:
                conn.rollback()
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
        finally:
            if conn:
                conn.close()

        # Process the document using the CORRECT method name
        try:
            result = qa_service.process_document(  # ✅ Changed from process_file to process_document
                file_path=temp_file_path,
                user_id=current_user['id'],
                document_id=doc_id,
                filename=file.filename
            )
            
            if not result["success"]:
                # If processing fails, clean up SQL entry
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("DELETE FROM documents WHERE id = ?", (doc_id,))
                conn.commit()
                conn.close()
                raise HTTPException(status_code=400, detail=result["message"])
            
            # Update the chunks count in SQL database
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE documents SET chunks_count = ? WHERE id = ?", 
                    (result["chunks_created"], doc_id)
                )
                conn.commit()
                conn.close()
            except sqlite3.Error as e:
                print(f"Warning: Could not update chunks count: {e}")
            
            print(f"✅ Document processed: {result['chunks_created']} chunks created")
            
        except Exception as e:
            # If processing fails, clean up SQL entry
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM documents WHERE id = ?", (doc_id,))
            conn.commit()
            conn.close()
            raise HTTPException(status_code=500, detail=f"Document processing failed: {str(e)}")
        
        return DocumentUploadResponse(
            message=result["message"],
            document_id=str(doc_id),
            chunks_created=result["chunks_created"],
            processing_time=result["processing_time"]
        )
        
    finally:
        # Clean up temp file
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)

@app.post("/ask", response_model=QuestionResponse)
async def ask_question(
    request: QuestionRequest,
    current_user: dict = Depends(get_current_user)
):
    """Ask a question and get AI-generated answer from user's documents only"""
    question = request.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="Question cannot be empty")
    
    # Check if user has any documents
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM documents WHERE user_id = ?", (current_user['id'],))
        doc_count = cursor.fetchone()[0]
        
        if doc_count == 0:
            return QuestionResponse(
                question=question,
                answer="I don't have any documents to search through. Please upload some documents first.",
                sources=[],
                response_time=0.1,
                retrieved_chunks=0,
                confidence_score=0.0
            )
    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        if conn:
            conn.close()
    
    try:
        # Pass user_id to ensure only user's documents are searched
        response = qa_service.ask_question(question, user_id=current_user['id'])
        
        return QuestionResponse(
            question=question,
            answer=response["answer"],
            sources=response.get("sources", []),
            response_time=response["response_time"],
            retrieved_chunks=response.get("retrieved_chunks", 0),
            confidence_score=response.get("confidence_score")
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate answer: {str(e)}")

@app.get("/documents")
async def get_user_documents(current_user: dict = Depends(get_current_user)):
    """Get all documents for the current user"""
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, filename, file_size, chunks_count, upload_time
            FROM documents 
            WHERE user_id = ?
            ORDER BY upload_time DESC
        """, (current_user['id'],))
        
        documents = []
        for row in cursor.fetchall():
            documents.append({
                "id": row["id"],
                "filename": row["filename"],
                "file_size": row["file_size"],
                "chunks_count": row["chunks_count"],
                "upload_time": row["upload_time"]
            })
        
        return documents
        
    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        if conn:
            conn.close()

@app.delete("/documents/{document_id}")
async def delete_document(
    document_id: int,
    current_user: dict = Depends(get_current_user)
):
    """Delete a document and its vector embeddings - REDESIGNED"""
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Verify document belongs to user
        cursor.execute("""
            SELECT filename FROM documents 
            WHERE id = ? AND user_id = ?
        """, (document_id, current_user['id']))
        
        document = cursor.fetchone()
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        filename = document["filename"]
        print(f"Deleting document {document_id} ({filename}) for user {current_user['id']}")
        
        # Delete from vector database FIRST
        vector_deleted = 0
        try:
            delete_result = qa_service.delete_document(current_user['id'], document_id)
            vector_deleted = delete_result.get("chunks_deleted", 0)
            print(f"✅ Vector: Deleted {vector_deleted} chunks for document {document_id}")
        except Exception as e:
            print(f"❌ Vector deletion failed: {e}")
            # Continue with SQL deletion even if vector fails

        # Delete from SQL database
        cursor.execute("""
            DELETE FROM documents 
            WHERE id = ? AND user_id = ?
        """, (document_id, current_user['id']))
        
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Document not found")
        
        conn.commit()
        
        return {
            "message": "Document deleted successfully",
            "sql_deleted": cursor.rowcount,
            "vector_chunks_deleted": vector_deleted
        }
        
    except sqlite3.Error as e:
        if conn:
            conn.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        if conn:
            conn.close()

@app.get("/stats")
async def get_user_stats(current_user: dict = Depends(get_current_user)):
    """Get user statistics using NEW QA service method"""
    try:
        stats = qa_service.get_user_stats(current_user['id'])
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch stats: {str(e)}")

@app.get("/users/me", response_model=UserResponse)
async def read_users_me(current_user: dict = Depends(get_current_user)):
    """Get current user info (protected endpoint)"""
    return UserResponse(id=current_user["id"], email=current_user["email"])

@app.delete("/debug/nuclear-reset")
async def nuclear_reset_everything():
    """NUCLEAR OPTION: Reset everything - SQL + Vector databases"""
    try:
        # Reset vector database
        reset_success = qa_service.vector_service.reset_collection()
        
        # Reset SQL databases
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Delete all documents
            cursor.execute("DELETE FROM documents")
            documents_deleted = cursor.rowcount
            
            # Delete all users (optional - uncomment if needed)
            # cursor.execute("DELETE FROM users")
            # users_deleted = cursor.rowcount
            
            conn.commit()
            
        finally:
            if conn:
                conn.close()
        
        return {
            "message": "NUCLEAR RESET COMPLETED",
            "vector_reset": reset_success,
            "sql_documents_deleted": documents_deleted,
            "warning": "ALL DATA HAS BEEN DELETED"
        }
        
    except Exception as e:
        return {"error": str(e)}


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )