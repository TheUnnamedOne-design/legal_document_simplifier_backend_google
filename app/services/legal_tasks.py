from app.services.parser import parse_document
from app.services.chunker import chunk_text
from app.services.embeddings import embedding_model
from app.services.database import collection
from app.services.retrieval import retrieve_and_rerank
from app.services.gemini_client import generate_response

def ingest_document(path: str, doc_id: str):
    text = parse_document(path)
    chunks = chunk_text(text)

    embeddings = embedding_model.encode(chunks).tolist()

    # Pinecone upsert expects list of (id, vector, metadata)
    vectors = [
        {
            "id": f"{doc_id}_{i}",
            "values": emb,
            "metadata": {"text": chunk}
        }
        for i, (emb, chunk) in enumerate(zip(embeddings, chunks))
    ]
    collection.upsert(vectors)

    print(f"✅ Document {doc_id} ingested with {len(chunks)} chunks.")



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
