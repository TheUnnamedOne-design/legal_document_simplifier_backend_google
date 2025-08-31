from flask import Blueprint, request, jsonify
from app.services.legal_tasks import simplify_clause, query_for_answer, risk_check

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
