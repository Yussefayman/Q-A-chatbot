import os
import logging
import warnings
from typing import List

# Disable telemetry
os.environ.update({
    "ANONYMIZED_TELEMETRY": "False",
    "CHROMA_TELEMETRY": "False",
    "DOCLING_TELEMETRY": "False"
})
warnings.filterwarnings("ignore", message=".*telemetry.*")

logger = logging.getLogger(__name__)

class DocumentChunk:
    """Simple document chunk"""
    def __init__(self, text: str, source: str, chunk_id: int):
        self.text = text
        self.source = source
        self.chunk_id = chunk_id

class DocumentService:
    """Simple document processing service"""
    
    def __init__(self, chunk_size: int = 200, chunk_overlap: int = 100):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
    
    def process_file(self, file_path: str) -> List[DocumentChunk]:
        """Process a file and return chunks"""
        
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        filename = os.path.basename(file_path)
        file_ext = os.path.splitext(filename)[1].lower()
        
        print(f"Processing {filename}...")
        
        if file_ext == '.txt':
            content = self._read_text_file(file_path)
        elif file_ext == '.pdf':
            content = self._read_pdf_file(file_path)
        else:
            # Try to read as text
            try:
                content = self._read_text_file(file_path)
            except:
                raise ValueError(f"Unsupported file type: {file_ext}")
        
        # Split into chunks
        text_chunks = self._chunk_text(content)
        
        # Create DocumentChunk objects
        doc_chunks = []
        for i, chunk_text in enumerate(text_chunks):
            if chunk_text.strip():
                doc_chunks.append(DocumentChunk(
                    text=chunk_text.strip(),
                    source=filename,
                    chunk_id=i
                ))
        
        print(f"Created {len(doc_chunks)} chunks")
        return doc_chunks
    
    def _read_text_file(self, file_path: str) -> str:
        """Read text file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except UnicodeDecodeError:
            # Try different encoding
            with open(file_path, 'r', encoding='latin-1') as f:
                return f.read()
    
    def _read_pdf_file(self, file_path: str) -> str:
        """Read PDF file using PyPDF2"""
        try:
            import PyPDF2
            
            content = ""
            with open(file_path, 'rb') as f:
                pdf_reader = PyPDF2.PdfReader(f)
                
                for page_num, page in enumerate(pdf_reader.pages):
                    try:
                        page_text = page.extract_text()
                        if page_text.strip():
                            content += f"\n{page_text}\n"
                    except:
                        print(f"Warning: Could not read page {page_num + 1}")
            
            if not content.strip():
                raise ValueError("No text found in PDF")
            
            return content
            
        except ImportError:
            raise ValueError("PyPDF2 not installed. Install with: pip install PyPDF2")
    
    def _chunk_text(self, text: str) -> List[str]:
        """Split text into chunks"""
        if not text.strip():
            return []
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + self.chunk_size
            chunk = text[start:end]
            
            # Try to break at sentence boundary
            if end < len(text):
                last_period = chunk.rfind('.')
                last_newline = chunk.rfind('\n')
                break_point = max(last_period, last_newline)
                
                if break_point > start + self.chunk_size // 2:
                    chunk = text[start:break_point + 1]
                    end = break_point + 1
            
            chunks.append(chunk)
            start = end - self.chunk_overlap
            
            if start >= len(text):
                break
        
        return chunks