from flask import Blueprint, request, jsonify
from app.services.legal_tasks import (
    simplify_clause, 
    query_for_answer, 
    risk_check, 
    ingest_document_from_content, 
    summarize_document_from_content,
    summarize_document_from_content2
)
from app.services.parser import parse_document_from_content
from werkzeug.utils import secure_filename
import io
import re
from typing import Dict, List, Tuple
import google.generativeai as genai
import time

legal_bp = Blueprint("legal", __name__)

@legal_bp.route("/simplify", methods=["POST"])
def simplify():
    data = request.json
    clause = data.get("clause", "")
    simplified = simplify_clause(clause)
    return jsonify({"simplified": simplified})

@legal_bp.route("/query", methods=["POST"])
def query():
    data = request.json
    question = data.get("question", "")
    answer = query_for_answer(question)
    return jsonify({"answer": answer})

@legal_bp.route("/risk", methods=["POST"])
def risk():
    data = request.json
    text = data.get("text", "")
    risks = risk_check(text)
    return jsonify({"risks": risks})

@legal_bp.route("/ingest", methods=["POST"])
def ingest():
    """
    Expects a file upload with form data:
    - file: the document file (PDF, DOCX, or TXT)
    - doc_id: unique identifier for the document
    
    Returns the extracted text content along with success message
    """
    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400
    
    file = request.files['file']
    doc_id = request.form.get('doc_id')
    
    if not doc_id:
        return jsonify({"error": "'doc_id' is required"}), 400
    
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400

    try:
        # Read file content
        file_content = file.read()
        filename = secure_filename(file.filename)
        
        # Parse document content based on file extension
        text_content = parse_document_from_content(file_content, filename)
        
        # Ingest the document
        ingest_document_from_content(text_content, doc_id)
        
        # Return success message along with extracted text content
        return jsonify({
            "message": f"Document {doc_id} ingested successfully.",
            "doc_id": doc_id,
            "filename": filename,
            "text_content": text_content,
            "content_length": len(text_content)
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    


@legal_bp.route("/ingest_json", methods=["POST"])
def ingest_json():
    """
    Alternative endpoint that accepts JSON with base64 encoded file content:
    {
        "file_content": "base64_encoded_content",
        "filename": "document.pdf",
        "doc_id": "unique_id_for_document"
    }
    
    Returns the extracted text content along with success message
    """
    data = request.json
    file_content_b64 = data.get("file_content")
    filename = data.get("filename")
    doc_id = data.get("doc_id")

    if not all([file_content_b64, filename, doc_id]):
        return jsonify({"error": "file_content, filename, and doc_id are all required"}), 400

    try:
        import base64
        file_content = base64.b64decode(file_content_b64)
        
        # Parse document content
        text_content = parse_document_from_content(file_content, filename)
        
        # Ingest the document
        ingest_document_from_content(text_content, doc_id)
        
        # Return success message along with extracted text content
        return jsonify({
            "message": f"Document {doc_id} ingested successfully.",
            "doc_id": doc_id,
            "filename": filename,
            "text_content": text_content,
            "content_length": len(text_content)
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    

    

@legal_bp.route("/summarise_document", methods=["POST"])
def summarise_document_route():
    """
    Expects a file upload:
    - file: the document file (PDF, DOCX, or TXT)
    """
    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400

    try:
        # Read file content
        file_content = file.read()
        filename = secure_filename(file.filename)
        
        # Parse document content
        #print("Calling successfully1")
        text_content = parse_document_from_content(file_content, filename)
        # Summarize the document
        #print("Calling successfully2")
        #print(text_content)
        summary = summarize_document_from_content2(text_content)
        #print("Calling successfully")
        return jsonify({"Summary": summary}), 200
    except Exception as e:
        print("Calling unsuccessfully")
        return jsonify({"error": str(e)}), 500
    


@legal_bp.route("/summarise_document_json", methods=["POST"])
def summarise_document_json():
    """
    Alternative endpoint that accepts JSON with base64 encoded file content:
    {
        "file_content": "base64_encoded_content",
        "filename": "document.pdf"
    }
    """
    data = request.json
    file_content_b64 = data.get("file_content")
    filename = data.get("filename")

    if not file_content_b64 or not filename:
        return jsonify({"error": "Both file_content and filename are required"}), 400

    try:
        import base64
        file_content = base64.b64decode(file_content_b64)
        
        # Parse document content
        text_content = parse_document_from_content(file_content, filename)
        
        # Summarize the document
        summary = summarize_document_from_content(text_content)
        
        return jsonify({"Summary": summary})
    except Exception as e:
        return jsonify({"error": str(e)}), 500