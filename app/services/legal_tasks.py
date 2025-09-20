from app.services.chunker import chunk_text
from app.services.embeddings import embedding_model
from app.services.database import collection
from app.services.retrieval import retrieve_and_rerank
from app.services.gemini_client import generate_response

from typing import List, Dict, Any
import re


def ingest_document_from_content(content: str, doc_id: str):
    """
    Ingest document from text content instead of file path.
    """
    # 🔥 Clear the index before adding new data
    collection.delete(delete_all=True)

    chunks = chunk_text(content)
    embeddings = embedding_model.encode(chunks).tolist()

    vectors = [
        {
            "id": f"{doc_id}_{i}",
            "values": emb,
            "metadata": {"text": chunk}
        }
        for i, (emb, chunk) in enumerate(zip(embeddings, chunks))
    ]
    collection.upsert(vectors)

    print(f"✅ Document {doc_id} ingested with {len(chunks)} chunks (previous data cleared).")


def simplify_clause(clause_query: str, doc_type: str = "contract") -> str:
    retrieved_chunks = retrieve_and_rerank(clause_query)
    context = "\n".join(retrieved_chunks)

    prompt = f"""
    You are a legal simplifier. The user provided a {doc_type}.
    Clause/query: {clause_query}

    Relevant context from the document:
    {context}

    Simplify this clause into plain English so a non-lawyer can understand.
    """
    return generate_response(prompt)


def query_for_answer(question: str, doc_type: str = "contract") -> str:
    retrieved_chunks = retrieve_and_rerank(question)
    context = "\n".join(retrieved_chunks)

    prompt = f"""
    You are assisting with understanding a {doc_type}.
    Question: {question}

    Relevant context from the document:
    {context}

    Answer the question in plain English, clearly and concisely.
    """
    return generate_response(prompt, model_name="gemini-1.5-flash")


def risk_check(doc_type: str = "contract") -> str:
    retrieved_chunks = retrieve_and_rerank("potential risks or penalties", top_k=8)
    context = "\n".join(retrieved_chunks)

    prompt = f"""
    You are a legal risk detector. The user uploaded a {doc_type}.
    Relevant document context:
    {context}

    Identify any clauses that may be risky or unfavorable (penalties, hidden fees, unilateral rights, etc.).
    Return a short checklist in plain English.
    If no risks are found, say: "No significant risks detected."
    """
    return generate_response(prompt, model_name="gemini-1.5-flash")


def split_by_headings(text: str) -> Dict[str, str]:
    """
    Split document text into sections based on headings.
    Headings are assumed to be lines in ALL CAPS or numbered like 1., 2.1, etc.
    """
    sections = {}
    current_heading = "Introduction"
    buffer = []

    lines = text.splitlines()
    for line in lines:
        line_stripped = line.strip()
        if re.match(r"^(\d+(\.\d+)*)\s", line_stripped) or line_stripped.isupper():
            if buffer:
                sections[current_heading] = "\n".join(buffer).strip()
                buffer = []
            current_heading = line_stripped
        else:
            buffer.append(line_stripped)

    # Add last section
    if buffer:
        sections[current_heading] = "\n".join(buffer).strip()

    return sections


def simplify_summarize_section(title: str, text: str) -> str:
    """
    Summarize one section into bullet points (simplified, easy to understand).
    Skips if section is empty or trivial.
    """
    if not text.strip() or len(text.split()) < 20:  # skip too short sections
        return ""

    prompt = f"""
    You are an assistant that explains documents in simple language.
    Summarize the following section into 3–5 short, clear bullet points.

    Rules:
    - Use plain English (avoid jargon or legalese).
    - Write as if explaining to someone with no legal/technical background.
    - Keep sentences short and direct.
    - If the section has no meaningful information, output "No important points."

    Section Title: "{title}"

    Section Text:
    {text}

    Output format:
    - simple point 1
    - simple point 2
    ...
    """
    
    response = generate_response(prompt, model_name="gemini-1.5-flash")
    return response


def summarize_document_from_content(content: str) -> Dict[str, str]:
    """
    Split document content into sections and summarize each with Gemini.
    Returns a dict {heading: bullets}
    """
    sections = split_by_headings(content)

    summaries = {}
    for title, section_content in sections.items():
        summary = summarize_section(title, section_content)
        if summary and "No important points" not in summary:
            summaries[title] = summary

    return summaries


def summarize_section(title: str, text: str) -> str:
    """
    Summarize one section into bullet points (if relevant).
    Skips if section is empty or trivial.
    """
    if not text.strip() or len(text.split()) < 20:  # skip too short sections
        return ""

    prompt = f"""
    You are a legal assistant. Summarize the following section into 3–5 clear bullet points.
    Do not invent a title, use the given one: "{title}".
    If no meaningful points exist, return "No important points."

    Section Text:
    {text}

    Output format:
    - point 1
    - point 2
    ...
    """

    response = generate_response(prompt, model_name="gemini-1.5-flash")
    return response