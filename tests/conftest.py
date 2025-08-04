import pytest
import os
import tempfile
import sqlite3
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient

# Add parent directory to path for imports
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'dev'))

from apis.main import app

@pytest.fixture
def client():
    """FastAPI test client"""
    with TestClient(app) as c:
        yield c

@pytest.fixture
def test_user():
    """Test user data"""
    return {
        "email": "test@example.com",
        "password": "testpassword123"
    }

@pytest.fixture
def test_file_content():
    """Sample file content for testing"""
    return "This is a test document about artificial intelligence and machine learning. AI is transforming industries."

@pytest.fixture
def test_txt_file(test_file_content):
    """Create a temporary test text file"""
    fd, path = tempfile.mkstemp(suffix='.txt')
    with os.fdopen(fd, 'w') as f:
        f.write(test_file_content)
    yield path
    os.unlink(path)

@pytest.fixture
def mock_db_user():
    """Mock database user"""
    return {
        "id": 1,
        "email": "test@example.com",
        "hashed_password": "$2b$12$test.hash.here"
    }

@pytest.fixture(autouse=True)
def setup_test_env():
    """Set up test environment variables"""
    os.environ["GROQ_API_KEY"] = "test-api-key"
    os.environ["SECRET_KEY"] = "test-secret-key"
    yield