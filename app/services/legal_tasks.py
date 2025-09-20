from app.services.chunker import chunk_text
from app.services.embeddings import embedding_model
from app.services.database import collection
from app.services.retrieval import retrieve_and_rerank
from app.services.gemini_client import generate_response
import google.generativeai as genai
from typing import List, Dict, Any, Tuple
import re
import time


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


def batch_sections(sections: List[Tuple[str, str]], max_sections_per_batch: int) -> List[List[Tuple[str, str]]]:
    batches = []
    for i in range(0, len(sections), max_sections_per_batch):
        batches.append(sections[i:i+max_sections_per_batch])
    return batches


def summarize_batch(sections_batch: List[Tuple[str, str]], model: genai.GenerativeModel) -> Dict[str, str]:
    # Build combined prompt for multiple sections
    prompt_parts = []
    for title, text in sections_batch:
        if text.strip() and len(text.split()) >= 20:
            prompt_parts.append(f'Section: "{title}"\n{text}\n')

    if not prompt_parts:
        return {}

    prompt = (
        "You are a legal assistant. Summarize each section into 3–5 clear bullet points.\n"
        "Use the given section headings exactly as they appear.\n"
        "If no meaningful points exist, respond with 'No important points' under that heading.\n\n"
        + "\n".join(prompt_parts) +
        "\n\nOutput format:\nSection: [heading]\n- point 1\n- point 2\n..."
    )

    response_text = model.generate_content(prompt).text

    # Parse the response to separate section summaries by headings
    summaries = {}
    sections_resp = re.split(r'Section:\s*"(.*?)"', response_text)
    for i in range(1, len(sections_resp), 2):
        heading = sections_resp[i].strip()
        summary = sections_resp[i + 1].strip()
        if summary and "No important points" not in summary:
            summaries[heading] = summary

    return summaries


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
    #print("DEBUG: Starting summarize_document_from_content")
    
    sections = split_by_headings(content)
    #print(f"DEBUG: Sections extracted: {list(sections.keys())}")

    summaries = {}
    for title, section_content in sections.items():
        #print(f"DEBUG: Summarizing section '{title}' (length: {len(section_content)} characters)")
        try:
            summary = summarize_section(title, section_content)
            #print(f"DEBUG: Summary for '{title}': {summary[:50]}...")  # print first 50 chars
            if summary and "No important points" not in summary:
                summaries[title] = summary
        except Exception as e:
            #print(f"ERROR: Failed to summarize section '{title}': {e}")
            summaries[title] = "Error generating summary for this section."

    #print(f"DEBUG: Total summaries generated: {len(summaries)}")
    return summaries



def summarize_document_from_content2(
    content: str,
    model_name: str = "gemini-2.5-flash",
    batch_size: int = 8
) -> Dict[str, str]:
    """
    Split document content into sections and summarize each with Gemini.
    Returns a dict {heading: bullets}
    """
    print("DEBUG: Starting summarize_document_from_content2")
    print(f"DEBUG: Using model: {model_name}, batch size: {batch_size}")

    sections = list(split_by_headings(content).items())
    print(f"DEBUG: Total sections extracted: {len(sections)}")
    print(f"DEBUG: Section titles: {[title for title, _ in sections]}")

    batches = batch_sections(sections, batch_size)
    print(f"DEBUG: Created {len(batches)} batches")

    # instantiate model once
    try:
        model = genai.GenerativeModel(model_name)
        print("DEBUG: Gemini model instantiated successfully")
    except Exception as e:
        print(f"ERROR: Failed to load Gemini model '{model_name}': {e}")
        return {"Error": f"Model initialization failed: {e}"}

    final_summaries = {}
    total_batches = len(batches)
    print("total_batches")
    for i, batch in enumerate(batches, 1):
        start_time = time.time()
        print(f"\n--- Processing batch {i}/{total_batches} ---")
        print(f"DEBUG: Batch {i} contains {len(batch)} sections: {[title for title, _ in batch]}")

        try:
            batch_summary = summarize_batch(batch, model)
            print(f"DEBUG: Batch {i} summary keys: {list(batch_summary.keys())}")
            final_summaries.update(batch_summary)
        except Exception as e:
            print(f"ERROR: Failed to summarize batch {i}: {e}")
            for title, _ in batch:
                final_summaries[title] = "Error generating summary for this section."

        elapsed = time.time() - start_time
        print(f"Completed batch {i} in {elapsed:.2f} seconds")

    print("\nAll batches processed.")
    print(f"DEBUG: Final summaries generated for {len(final_summaries)} sections")
    return final_summaries





def summarize_section(title: str, text: str) -> str:
    if not text.strip() or len(text.split()) < 20:
        #print(f"DEBUG: Skipping short or empty section '{title}'")
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

    #print(f"DEBUG: Prompt prepared for section '{title}' (length {len(prompt)} chars)")

    try:
        summary = generate_response(prompt)  # your Gemini API call
        #print(f"DEBUG: Summary received for section '{title}': {summary[:50]}...")
        return summary
    except Exception as e:
        #print(f"ERROR: Failed to summarize section '{title}': {e}")
        return "Error generating summary for this section."


    response = generate_response(prompt, model_name="gemini-1.5-flash")
    return response