from typing import List, Optional, Dict, Any
import re
import logging
from io import BytesIO
import docx
from PyPDF2 import PdfReader
from langchain.text_splitter import RecursiveCharacterTextSplitter

logger = logging.getLogger(__name__)


class DocumentPoint:
    """Represents a single point/clause in a document"""
    
    def __init__(self, content: str, point_number: Optional[str] = None, point_type: str = "clause"):
        self.content = content.strip()
        self.point_number = point_number
        self.point_type = point_type  # clause, article, section, etc.
    
    def __str__(self):
        if self.point_number:
            return f"{self.point_number}. {self.content}"
        return self.content


class DocumentParser:
    """Service for parsing various document formats and splitting into points"""
    
    def __init__(self):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=2000,
            chunk_overlap=200,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
    
    def parse_document(self, document_bytes: bytes, filename: Optional[str] = None) -> str:
        """
        Parse document from bytes and extract text content
        Supports PDF and DOCX formats
        """
        try:
            if filename:
                file_extension = filename.lower().split('.')[-1] if '.' in filename else ''
            else:
                # Try to detect format from content
                file_extension = self._detect_file_format(document_bytes)
            
            if file_extension == 'pdf':
                return self._parse_pdf(document_bytes)
            elif file_extension in ['docx', 'doc']:
                return self._parse_docx(document_bytes)
            else:
                # Fallback to text
                return self._parse_text(document_bytes)
                
        except Exception as e:
            logger.error(f"Failed to parse document: {e}")
            # Fallback to text parsing
            return self._parse_text(document_bytes)
    
    def _detect_file_format(self, document_bytes: bytes) -> str:
        """Detect file format from bytes content"""
        if document_bytes.startswith(b'%PDF'):
            return 'pdf'
        elif document_bytes.startswith(b'PK'):  # ZIP-based formats like DOCX
            return 'docx'
        else:
            return 'txt'
    
    def _parse_pdf(self, document_bytes: bytes) -> str:
        """Extract text from PDF bytes"""
        try:
            pdf_file = BytesIO(document_bytes)
            pdf_reader = PdfReader(pdf_file)
            
            text_content = []
            for page in pdf_reader.pages:
                text_content.append(page.extract_text())
            
            return '\n\n'.join(text_content)
        except Exception as e:
            logger.error(f"Failed to parse PDF: {e}")
            raise
    
    def _parse_docx(self, document_bytes: bytes) -> str:
        """Extract text from DOCX bytes"""
        try:
            docx_file = BytesIO(document_bytes)
            doc = docx.Document(docx_file)
            
            text_content = []
            for paragraph in doc.paragraphs:
                if paragraph.text.strip():
                    text_content.append(paragraph.text.strip())
            
            return '\n\n'.join(text_content)
        except Exception as e:
            logger.error(f"Failed to parse DOCX: {e}")
            raise
    
    def _parse_text(self, document_bytes: bytes) -> str:
        """Parse as plain text with various encoding attempts"""
        encodings = ['utf-8', 'cp1251', 'latin-1']
        
        for encoding in encodings:
            try:
                return document_bytes.decode(encoding)
            except UnicodeDecodeError:
                continue
        
        # If all encodings fail, use utf-8 with error handling
        return document_bytes.decode('utf-8', errors='replace')
    
    def split_into_points(self, document_text: str) -> List[DocumentPoint]:
        """
        Split document text into logical points/clauses
        Uses various patterns to identify contract clauses and legal points
        """
        points = []
        
        # First try to split by numbered points/articles
        numbered_points = self._split_by_numbered_points(document_text)
        if numbered_points:
            return numbered_points
        
        # If no numbered points found, try other splitting strategies
        bullet_points = self._split_by_bullet_points(document_text)
        if bullet_points:
            return bullet_points
        
        # Fallback to paragraph-based splitting
        return self._split_by_paragraphs(document_text)
    
    def _split_by_numbered_points(self, text: str) -> List[DocumentPoint]:
        """Split by numbered points (1., 2., 1.1., etc.)"""
        points = []
        
        # Pattern for numbered points: "1.", "1.1.", "Article 1.", etc.
        patterns = [
            r'^\d+\.\s+',  # 1. 2. 3.
            r'^\d+\.\d+\.\s+',  # 1.1. 1.2.
            r'^(?:Статья|Article|Пункт|п\.|п)\s*\d+[\.\s]',  # Article 1, Статья 1, п. 1
            r'^\d+\)\s+',  # 1) 2) 3)
        ]
        
        for pattern in patterns:
            matches = list(re.finditer(pattern, text, re.MULTILINE | re.IGNORECASE))
            if len(matches) > 1:  # Found multiple numbered points
                for i, match in enumerate(matches):
                    start_pos = match.start()
                    end_pos = matches[i + 1].start() if i + 1 < len(matches) else len(text)
                    
                    point_content = text[start_pos:end_pos].strip()
                    point_number = match.group().strip()
                    
                    if len(point_content) > 20:  # Filter out very short points
                        points.append(DocumentPoint(
                            content=point_content,
                            point_number=point_number,
                            point_type="numbered_clause"
                        ))
                
                if points:
                    return points
        
        return []
    
    def _split_by_bullet_points(self, text: str) -> List[DocumentPoint]:
        """Split by bullet points or dashes"""
        points = []
        
        # Split by lines that start with bullets or dashes
        lines = text.split('\n')
        current_point = []
        
        for line in lines:
            line = line.strip()
            if re.match(r'^[-•·*]\s+', line):
                # Save previous point if exists
                if current_point:
                    content = '\n'.join(current_point).strip()
                    if len(content) > 20:
                        points.append(DocumentPoint(
                            content=content,
                            point_type="bullet_point"
                        ))
                
                # Start new point
                current_point = [line]
            elif current_point and line:
                # Continue current point
                current_point.append(line)
            elif not line and current_point:
                # Empty line might end current point, but continue for now
                current_point.append(line)
        
        # Don't forget the last point
        if current_point:
            content = '\n'.join(current_point).strip()
            if len(content) > 20:
                points.append(DocumentPoint(
                    content=content,
                    point_type="bullet_point"
                ))
        
        return points if len(points) > 1 else []
    
    def _split_by_paragraphs(self, text: str) -> List[DocumentPoint]:
        """Fallback: split by paragraphs using langchain text splitter"""
        chunks = self.text_splitter.split_text(text)
        
        points = []
        for i, chunk in enumerate(chunks):
            if len(chunk.strip()) > 50:  # Filter very short chunks
                points.append(DocumentPoint(
                    content=chunk.strip(),
                    point_number=f"Раздел {i + 1}",
                    point_type="paragraph"
                ))
        
        return points
    
    def extract_document_metadata(self, text: str) -> Dict[str, Any]:
        """Extract basic metadata from document text"""
        metadata = {
            "total_length": len(text),
            "word_count": len(text.split()),
            "paragraph_count": len([p for p in text.split('\n\n') if p.strip()]),
        }
        
        # Try to extract title (first substantial line)
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        if lines:
            metadata["title"] = lines[0][:200]  # First line as title, max 200 chars
        
        return metadata


# Global document parser instance
document_parser = DocumentParser() 