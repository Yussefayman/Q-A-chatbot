import os
import sys
import logging
from datetime import datetime
from typing import List, BinaryIO
from docling.document_converter import DocumentConverter
from docling.chunking import HierarchicalChunker
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data_model.schemas import DocumentChunk
from config.settings import settings

logger = logging.getLogger(__name__)

class DocumentService:
    
    def __init__(self):
        self.doc_converter = DocumentConverter()
        self.chunker = HierarchicalChunker()
        self.max_file_size = settings.max_file_size_mb * 1024 * 1024  # Convert to bytes
        logger.info("Document service initialized with Docling")
    
    def process_document(self, file_path: str, original_filename: str = None) -> List[DocumentChunk]:
        """
        Process a document and return chunks
        
        Args:
            file_path: Path to the document file
            original_filename: Original filename (for metadata)
            
        Returns:
            List of DocumentChunk objects
        """
        try:
            # Validate file
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"File not found: {file_path}")
            
            file_size = os.path.getsize(file_path)
            if file_size > self.max_file_size:
                raise ValueError(f"File size ({file_size} bytes) exceeds maximum allowed size ({self.max_file_size} bytes)")
            
            logger.info(f"Processing document: {file_path} (size: {file_size} bytes)")
            
            # Convert document using Docling
            result = self.doc_converter.convert(file_path)
            doc = result.document
            
            logger.info(f"Document converted successfully. Pages: {len(doc.pages)}")
            
            # Use Docling's hierarchical chunker
            chunks = list(self.chunker.chunk(doc))
            
            logger.info(f"Generated {len(chunks)} chunks using Docling")
            
            # Convert to DocumentChunk objects
            doc_chunks = []
            filename = original_filename or os.path.basename(file_path)
            
            for i, chunk in enumerate(chunks):
                chunk_text = self._extract_text_from_chunk(chunk)
                
                if not chunk_text.strip():  # Skip empty chunks
                    continue
                
                chunk_metadata = self._create_chunk_metadata(
                    filename, file_path, i, len(chunks), chunk
                )
                
                doc_chunk = DocumentChunk(
                    text=chunk_text,
                    source=filename,
                    chunk_id=i,
                    metadata=chunk_metadata
                )
                doc_chunks.append(doc_chunk)
            
            logger.info(f"Created {len(doc_chunks)} valid document chunks")
            return doc_chunks
            
        except Exception as e:
            logger.error(f"Error processing document {file_path}: {str(e)}")
            # Try fallback processing
            return self._fallback_processing(file_path, original_filename)
    
    def process_uploaded_file(self, file_content: bytes, filename: str) -> List[DocumentChunk]:
        """
        Process an uploaded file from memory
        
        Args:
            file_content: Binary content of the file
            filename: Original filename
            
        Returns:
            List of DocumentChunk objects
        """
        # Create temporary file
        temp_file_path = f"/tmp/{filename}"
        
        try:
            # Write content to temporary file
            with open(temp_file_path, 'wb') as temp_file:
                temp_file.write(file_content)
            
            # Process the temporary file
            return self.process_document(temp_file_path, filename)
            
        finally:
            # Clean up temporary file
            if os.path.exists(temp_file_path):
                try:
                    os.remove(temp_file_path)
                except Exception as e:
                    logger.warning(f"Failed to remove temporary file {temp_file_path}: {e}")
    
    def _extract_text_from_chunk(self, chunk) -> str:
        """Extract text from a Docling chunk"""
        if hasattr(chunk, 'text'):
            return chunk.text
        elif hasattr(chunk, 'content'):
            return str(chunk.content)
        else:
            return str(chunk)
    
    def _create_chunk_metadata(self, filename: str, file_path: str, chunk_index: int, 
                              total_chunks: int, chunk) -> dict:
        """Create metadata for a document chunk"""
        file_ext = os.path.splitext(filename)[1].lower()
        
        metadata = {
            "source_file": filename,
            "file_type": file_ext,
            "file_path": file_path,
            "chunk_index": chunk_index,
            "total_chunks": total_chunks,
            "created_at": datetime.now().isoformat(),
            "processing_method": "docling",
            "text_length": len(self._extract_text_from_chunk(chunk))
        }
        
        # Add Docling-specific metadata if available
        if hasattr(chunk, 'meta') and chunk.meta:
            metadata["docling_meta"] = chunk.meta
        
        if hasattr(chunk, 'page_no'):
            metadata["page_number"] = chunk.page_no
        
        if hasattr(chunk, 'bbox'):
            metadata["bounding_box"] = chunk.bbox
            
        return metadata
    
    def _fallback_processing(self, file_path: str, original_filename: str = None) -> List[DocumentChunk]:
        """
        Fallback processing when Docling fails
        """
        logger.warning(f"Using fallback processing for {file_path}")
        
        try:
            file_ext = os.path.splitext(file_path)[1].lower()
            filename = original_filename or os.path.basename(file_path)
            
            if file_ext == '.txt':
                return self._process_text_fallback(file_path, filename)
            elif file_ext == '.pdf':
                return self._process_pdf_fallback(file_path, filename)
            else:
                logger.error(f"Unsupported file type for fallback: {file_ext}")
                return []
                
        except Exception as e:
            logger.error(f"Fallback processing failed for {file_path}: {str(e)}")
            return []
    
    def _process_text_fallback(self, file_path: str, filename: str) -> List[DocumentChunk]:
        """Fallback text processing"""
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        
        chunks = self._simple_chunk_text(content)
        doc_chunks = []
        
        for i, chunk in enumerate(chunks):
            if not chunk.strip():
                continue
                
            metadata = {
                "source_file": filename,
                "file_type": ".txt",
                "chunk_index": i,
                "total_chunks": len(chunks),
                "created_at": datetime.now().isoformat(),
                "processing_method": "fallback_text",
                "text_length": len(chunk)
            }
            
            doc_chunk = DocumentChunk(
                text=chunk,
                source=filename,
                chunk_id=i,
                metadata=metadata
            )
            doc_chunks.append(doc_chunk)
        
        return doc_chunks
    
    def _process_pdf_fallback(self, file_path: str, filename: str) -> List[DocumentChunk]:
        """Fallback PDF processing using PyPDF2"""
        try:
            import PyPDF2
            
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                content = ""
                
                for page_num, page in enumerate(pdf_reader.pages):
                    page_text = page.extract_text()
                    content += f"\n--- Page {page_num + 1} ---\n{page_text}\n"
            
            chunks = self._simple_chunk_text(content)
            doc_chunks = []
            
            for i, chunk in enumerate(chunks):
                if not chunk.strip():
                    continue
                    
                metadata = {
                    "source_file": filename,
                    "file_type": ".pdf",
                    "chunk_index": i,
                    "total_chunks": len(chunks),
                    "created_at": datetime.now().isoformat(),
                    "processing_method": "fallback_pdf",
                    "text_length": len(chunk)
                }
                
                doc_chunk = DocumentChunk(
                    text=chunk,
                    source=filename,
                    chunk_id=i,
                    metadata=metadata
                )
                doc_chunks.append(doc_chunk)
            
            return doc_chunks
            
        except ImportError:
            logger.error("PyPDF2 not available for fallback PDF processing")
            return []
    
    def _simple_chunk_text(self, text: str) -> List[str]:
        """Simple text chunking for fallback"""
        chunk_size = settings.chunk_size
        overlap = settings.chunk_overlap
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + chunk_size
            chunk = text[start:end]
            
            # Try to break at sentence boundary
            if end < len(text):
                last_period = chunk.rfind('.')
                last_newline = chunk.rfind('\n')
                break_point = max(last_period, last_newline)
                
                if break_point > start + chunk_size // 2:
                    chunk = text[start:break_point + 1]
                    end = break_point + 1
            
            chunks.append(chunk.strip())
            start = end - overlap
            
            if start >= len(text):
                break
        
        return [chunk for chunk in chunks if chunk.strip()]
    
    def validate_file_type(self, filename: str) -> bool:
        """Validate if file type is supported"""
        supported_extensions = {'.txt', '.pdf'}
        file_ext = os.path.splitext(filename)[1].lower()
        return file_ext in supported_extensions
    
    def health_check(self) -> bool:
        """Check if document service is healthy"""
        try:
            # Test with a simple text conversion
            return hasattr(self.doc_converter, 'convert') and hasattr(self.chunker, 'chunk')
        except Exception as e:
            logger.error(f"Document service health check failed: {str(e)}")
            return False