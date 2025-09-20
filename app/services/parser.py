from pypdf import PdfReader
import docx
import io

def parse_pdf_from_content(file_content: bytes) -> str:
    """Parse PDF from binary content"""
    pdf_stream = io.BytesIO(file_content)
    reader = PdfReader(pdf_stream)
    return "".join([page.extract_text() or "" for page in reader.pages])

def parse_docx_from_content(file_content: bytes) -> str:
    """Parse DOCX from binary content"""
    docx_stream = io.BytesIO(file_content)
    doc = docx.Document(docx_stream)
    return "".join([para.text for para in doc.paragraphs])

def parse_text_from_content(file_content: bytes) -> str:
    """Parse text file from binary content"""
    try:
        return file_content.decode("utf-8")
    except UnicodeDecodeError:
        try:
            return file_content.decode("latin-1")
        except UnicodeDecodeError:
            return file_content.decode("utf-8", errors="ignore")

def parse_document_from_content(file_content: bytes, filename: str) -> str:
    """
    Parse document from binary content based on filename extension.
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

# Legacy path-based parsers
def parse_pdf(path: str) -> str:
    with open(path, "rb") as f:
        return parse_pdf_from_content(f.read())

def parse_docx(path: str) -> str:
    with open(path, "rb") as f:
        return parse_docx_from_content(f.read())

def parse_text(path: str) -> str:
    with open(path, "rb") as f:
        return parse_text_from_content(f.read())

def parse_document(path: str) -> str:
    with open(path, "rb") as f:
        return parse_document_from_content(f.read(), path)
