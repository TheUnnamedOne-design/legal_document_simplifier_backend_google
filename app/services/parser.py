from pypdf import PdfReader
import docx
import io

def parse_pdf_from_content(file_content: bytes) -> str:
    """Parse PDF from binary content"""
    pdf_stream = io.BytesIO(file_content)
    reader = PdfReader(pdf_stream)
    return "\n".join([page.extract_text() or "" for page in reader.pages])

def parse_docx_from_content(file_content: bytes) -> str:
    """Parse DOCX from binary content"""
    docx_stream = io.BytesIO(file_content)
    doc = docx.Document(docx_stream)
    return "\n".join([para.text for para in doc.paragraphs])

def parse_text_from_content(file_content: bytes) -> str:
    """Parse text file from binary content"""
    try:
        # Try UTF-8 first
        return file_content.decode("utf-8")
    except UnicodeDecodeError:
        # Fall back to other encodings
        try:
            return file_content.decode("latin-1")
        except UnicodeDecodeError:
            return file_content.decode("utf-8", errors="ignore")

def parse_document_from_content(file_content: bytes, filename: str) -> str:
    """
    Parse document from binary content based on filename extension.
    
    Args:
        file_content: Binary content of the file
        filename: Original filename to determine file type
    
    Returns:
        Extracted text content as string
    """
    filename_lower = filename.lower()
    
    if filename_lower.endswith(".pdf"):
        return parse_pdf_from_content(file_content)
    elif filename_lower.endswith(".docx"):
        return parse_docx_from_content(file_content)
    elif filename_lower.endswith((".txt", ".text")):
        return parse_text_from_content(file_content)
    else:
        raise ValueError(f"Unsupported file format: {filename}. Use PDF, DOCX, or TXT.")

# Keep the original functions for backward compatibility
def parse_pdf(path: str) -> str:
    """Legacy function - parse PDF from file path"""
    with open(path, "rb") as f:
        file_content = f.read()
    return parse_pdf_from_content(file_content)

def parse_docx(path: str) -> str:
    """Legacy function - parse DOCX from file path"""
    with open(path, "rb") as f:
        file_content = f.read()
    return parse_docx_from_content(file_content)

def parse_text(path: str) -> str:
    """Legacy function - parse text from file path"""
    with open(path, "rb") as f:
        file_content = f.read()
    return parse_text_from_content(file_content)

def parse_document(path: str) -> str:
    """Legacy function - parse document from file path"""
    with open(path, "rb") as f:
        file_content = f.read()
    return parse_document_from_content(file_content, path)