# QuestAI - AI-Powered Question Answering System

🤖 **An intelligent document Q&A system built with FastAPI, React, and vector search capabilities.**

## 🎯 Project Overview

QuestAI is a full-stack AI application that allows users to upload documents and ask questions about their content. The system uses advanced language models and vector similarity search to provide accurate, context-aware answers based on uploaded documents.

## ✨ Features

- **🔐 User Authentication**: Secure JWT-based authentication system
- **📄 Document Upload**: Support for PDF and TXT file uploads (up to 10MB)
- **🧠 AI-Powered Q&A**: Uses Groq's LLaMA models for intelligent responses
- **🔍 Vector Search**: ChromaDB integration for semantic document search
- **💬 Interactive Chat**: Real-time chat interface for asking questions
- **📊 Query Logging**: Comprehensive logging of user interactions
- **🔒 User Isolation**: Each user has their own document space
- **⚡ Fast Processing**: Efficient document chunking and embedding generation

## 🏗️ Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   React Frontend │    │  FastAPI Backend │    │   Vector Store   │
│                 │    │                 │    │                 │
│  • Authentication │──▶│  • JWT Auth     │    │  • ChromaDB     │
│  • File Upload   │    │  • File Processing│──▶│  • Embeddings   │
│  • Chat Interface│    │  • Q&A Endpoints│    │  • Similarity   │
│  • Document Mgmt │    │  • SQLite DB    │    │    Search       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │   Groq LLM API  │
                       │                 │
                       │  • LLaMA Models │
                       │  • Text Generation│
                       └─────────────────┘

```

<img width="1216" height="1096" alt="image" src="https://github.com/user-attachments/assets/0e09effa-86ce-4c39-a82b-8de047093a23" />


### Core Components

- **Frontend**: React-based chat interface with document management
- **Backend API**: FastAPI with JWT authentication and file processing
- **Vector Database**: ChromaDB for semantic search and embeddings
- **Language Model**: Groq API with LLaMA 3 models
- **Database**: SQLite for user data and query logging
- **Document Processing**: Text chunking with configurable overlap

## 🛠️ Tech Stack

### Backend
- **FastAPI** - Modern, fast web framework for Python APIs
- **SQLite** - Lightweight database for user management and logging
- **ChromaDB** - Vector database for document embeddings
- **Groq API** - LLM inference with LLaMA models
- **Sentence Transformers** - Text embedding generation
- **PyPDF2** - PDF text extraction
- **passlib** - Password hashing and authentication
- **python-jose** - JWT token handling

### Frontend
- **React** - Component-based UI framework
- **Lucide React** - Icon library
- **CSS3** - Modern styling with animations

### DevOps & Tools
- **uvicorn** - ASGI server for FastAPI
- **python-dotenv** - Environment variable management
- **CORS** - Cross-origin resource sharing

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- Node.js 14+
- Groq API key ([Get one here](https://groq.com))

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/questai.git
cd questai
```

### 2. Backend Setup

```bash
# Navigate to backend directory
cd dev

# Install Python dependencies
pip install -r requirements.txt

# Create environment file
cp .env.example .env

# Add your Groq API key to .env
echo "GROQ_API_KEY=your_groq_api_key_here" >> .env
```

### 3. Frontend Setup

```bash
# Navigate to frontend directory
cd qa-frontend

# Install dependencies
npm install
```

### 4. Run the Application

**Terminal 1 - Backend:**
```bash
cd dev/apis
python start_script.py
# Or manually: python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 - Frontend:**
```bash
cd qa-frontend
npm start
```

### 5. Access the Application

- **Frontend**: http://localhost:3000
- **API Documentation**: http://localhost:8000/docs
- **API Health Check**: http://localhost:8000/health

## 📋 API Reference

### Authentication Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/register` | Register new user |
| POST | `/token` | Login and get JWT token |

### Document Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/upload` | Upload and process document |
| GET | `/documents` | List user documents |

### Question Answering

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/ask` | Ask question about documents |

### Example Usage

```bash
# Register user
curl -X POST "http://localhost:8000/register" \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "secure123"}'

# Login
curl -X POST "http://localhost:8000/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=user@example.com&password=secure123"

# Upload document
curl -X POST "http://localhost:8000/upload" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -F "file=@document.pdf"

# Ask question
curl -X POST "http://localhost:8000/ask" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"question": "What is the main topic of the document?"}'
```

## ⚙️ Configuration

### Environment Variables

Create a `.env` file in the `dev` directory:

```env
# Required
GROQ_API_KEY=your_groq_api_key_here

# Optional - Authentication
SECRET_KEY=your-secret-key-change-this-in-production

# Optional - Model Configuration
GROQ_MODEL=llama3-8b-8192
GROQ_TEMPERATURE=0.1
GROQ_MAX_TOKENS=1000

# Optional - Document Processing
MAX_FILE_SIZE_MB=10
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
MAX_CHUNKS_FOR_CONTEXT=3

# Optional - Vector Database
CHROMA_PERSIST_DIRECTORY=./chroma_db
CHROMA_COLLECTION_NAME=documents
EMBEDDING_MODEL_NAME=all-MiniLM-L6-v2
```

### Supported File Types

- **PDF** (.pdf) - Automatically extracts text content
- **Text** (.txt) - Plain text files

### Processing Limits

- **File Size**: 10MB maximum (configurable)
- **Chunk Size**: 500 characters (configurable)
- **Context Window**: 3 most relevant chunks per query

## 🧪 Testing

QuestAI includes a comprehensive test suite built with **pytest** to ensure reliability and maintain code quality. The tests cover all major functionality including API endpoints, authentication, document processing, and integration workflows.

### Test Coverage

| Component | Test Classes | Coverage |
|-----------|-------------|----------|
| **API Endpoints** | `TestHealthEndpoint`, `TestDocumentUpload`, `TestQuestionAnswering` | Health check, file upload, Q&A endpoints |
| **Authentication** | `TestAuthentication`, `TestAuthenticationUtilities` | Registration, login, JWT tokens, password hashing |
| **Document Processing** | `TestDocumentService` | Text extraction, PDF parsing, chunking |
| **Core Services** | `TestQAService` | Document processing, question answering logic |
| **Integration** | `TestIntegration` | End-to-end user workflows |

### Key Test Scenarios

**✅ Authentication & Security**
- User registration and login
- JWT token generation and validation
- Password hashing and verification
- Unauthorized access prevention

**✅ Document Management**
- File upload validation (type, size limits)
- PDF and TXT file processing
- Text chunking and embedding generation
- User document isolation

**✅ Question Answering**
- Successful Q&A with context retrieval
- Handling empty or invalid questions
- No documents available scenarios
- Error handling and recovery

**✅ Integration Workflows**
- Complete user journey: register → login → upload → ask
- Cross-component functionality
- Database operations and consistency

### API Testing with Postman

Import the provided Postman collection or use the interactive docs at `http://localhost:8000/docs`.

## 📁 Project Structure

```
questai/
├── dev/                          # Backend application
│   ├── apis/
│   │   ├── main.py              # FastAPI application
│   │   └── start_script.py      # Server startup script
│   ├── services/
│   │   └── qa_service.py        # Core Q&A logic
│   ├── config/
│   │   └── settings.py          # Application settings
│   ├── dbs/                     # SQLite database files
│   ├── chroma_db/               # Vector database storage
│   ├── temp_uploads/            # Temporary file storage
│   ├── example.py               # Quick test script
│   └── .env                     # Environment configuration
├── qa-frontend/                  # React frontend
│   ├── src/
│   │   ├── App.js              # Main application component
│   │   ├── ChatPage.js         # Chat interface
│   │   ├── LoginPage.js        # Authentication
│   │   └── Chat.css            # Styling
│   ├── public/
│   └── package.json
└── README.md                    # This file
```

## 🔧 Known Limitations

- **Context Window**: Limited to 3 document chunks per query
- **Groq API Limit**: Groq limits LLM the application for 30 API call per minute
- **File Types**: Currently supports only PDF and TXT files
- **Concurrent Users**: SQLite may have limitations with high concurrency.
- **Memory Usage**: Large documents may require significant memory for processing
- **Language Support**: Optimized for English text content

## 🚀 Deployment Options

### Local Development
- Use the provided startup scripts
- Suitable for testing and development


## 🎯 Future Enhancements

- **Multiple File Formats**: Support for DOCX, HTML, and more
- **Dockerization**: Add docker files for containerization of Frontend, Backend, App, DBs
- **Better Chuncking Strategy**: Using better and more smart based on trees chunking strategy
- **Advanced Search**: Semantic search with filtering options
- **Conversation Memory**: Multi-turn conversation support and history
- **API Rate Limiting**: Enhanced security and resource management
- **Elasticsearch Integration**: Alternative vector database option
- **Deployment on Render**: Deploying the Docker containers on Render

---
