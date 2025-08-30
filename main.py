import os
import re
import uuid
from typing import List, Dict, Any

# Document parsing
from pypdf import PdfReader
import docx

# Embeddings + Vector DB
from sentence_transformers import SentenceTransformer, CrossEncoder
import chromadb

# Google Gemini client
import google.generativeai as genai

# --- Import API Keys ---
from keys import GEMINI_API_KEY

GEMINI_MODEL_NAME = "gemini-2.5-flash"
genai.configure(api_key=GEMINI_API_KEY)

# Embedding + reranker models
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
legal_model = SentenceTransformer('nlpaueb/legal-bert-base-uncased')
reranker = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")

# Chroma DB client
chroma_client = chromadb.Client()
# Use get_or_create to avoid error if it already exists
collection = chroma_client.get_or_create_collection("legal_docs")

def parse_pdf(path: str) -> str:
    reader = PdfReader(path)
    return "\n".join([page.extract_text() or "" for page in reader.pages])

def parse_docx(path: str) -> str:
    doc = docx.Document(path)
    return "\n".join([para.text for para in doc.paragraphs])

def parse_text(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def parse_document(path: str) -> str:
    if path.endswith(".pdf"):
        return parse_pdf(path)
    elif path.endswith(".docx"):
        return parse_docx(path)
    elif path.endswith(".txt"):
        return parse_text(path)
    else:
        raise ValueError("Unsupported file format. Use PDF, DOCX, or TXT.")

def chunk_text(text: str, chunk_size: int = 300, overlap: int = 50) -> List[str]:
    words = text.split()
    chunks, start = [], 0
    while start < len(words):
        end = min(len(words), start + chunk_size)
        chunks.append(" ".join(words[start:end]))
        start += chunk_size - overlap
    return chunks

def ingest_document(path: str, doc_id: str):
    text = parse_document(path)
    chunks = chunk_text(text)

    embeddings = embedding_model.encode(chunks).tolist()

    collection.add(
        documents=chunks,
        embeddings=embeddings,
        ids=[f"{doc_id}_{i}" for i in range(len(chunks))]
    )
    print(f"✅ Document {doc_id} ingested with {len(chunks)} chunks.")

def retrieve_and_rerank(query: str, top_k: int = 5) -> List[str]:
    query_emb = embedding_model.encode([query]).tolist()[0]

    results = collection.query(
        query_embeddings=[query_emb],
        n_results=top_k * 3 # get more, then rerank
    )

    candidates = results["documents"][0]
    scores = reranker.predict([(query, c) for c in candidates])

    reranked = sorted(zip(candidates, scores), key=lambda x: x[1], reverse=True)
    return [doc for doc, _ in reranked[:top_k]]

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
    model = genai.GenerativeModel(GEMINI_MODEL_NAME)
    response = model.generate_content(prompt)
    return response.text

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
    model = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content(prompt)
    return response.text

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
    model = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content(prompt)
    return response.text


if __name__ == "__main__":
    # Example usage:
    # ingest_document("./sample_rental_doc.pdf", doc_id="rental1")
    # print(simplify_clause("termination clause", doc_type="rental agreement"))
    # print(query_for_answer("Who is responsible for repairs?", doc_type="rental agreement"))
    # print(risk_check(doc_type="rental agreement"))
    pass
