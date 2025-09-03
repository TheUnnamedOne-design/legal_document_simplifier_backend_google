from flask import Blueprint, request, jsonify
from app.services.legal_tasks import simplify_clause, query_for_answer, risk_check, ingest_document

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
    Expects JSON:
    {
        "path": "path/to/document.pdf",
        "doc_id": "unique_id_for_document"
    }
    """
    data = request.json
    path = data.get("path")
    doc_id = data.get("doc_id")

    if not path or not doc_id:
        return jsonify({"error": "Both 'path' and 'doc_id' are required"}), 400

    try:
        ingest_document(path, doc_id)
        return jsonify({"message": f"Document {doc_id} ingested successfully."})
    except Exception as e:
        return jsonify({"error": str(e)}), 500