from flask import Flask, request, jsonify
import os
import re
from typing import Dict
from pypdf import PdfReader
import google.generativeai as genai

# 🔹 Configure Gemini
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
print(os.environ.get("GEMINI_API_KEY"))
app = Flask(__name__)

UPLOAD_FOLDER = "./uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# ---------- PDF Parsing ----------
def parse_document(path: str) -> str:
    """Extract text from a PDF file using pypdf."""
    text = []
    reader = PdfReader(path)
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text.append(page_text)
    return "\n".join(text)


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
        # Detect headings (very simple heuristic)
        if re.match(r"^(\d+(\.\d+)*)\s", line_stripped) or line_stripped.isupper():
            if buffer:
                sections[current_heading] = "\n".join(buffer).strip()
                buffer = []
            current_heading = line_stripped
        else:
            buffer.append(line_stripped)

    if buffer:
        sections[current_heading] = "\n".join(buffer).strip()

    return sections


def summarize_section(title: str, text: str) -> str:
    """
    Summarize one section into bullet points (if relevant).
    Skips if section is empty or trivial.
    """
    if not text.strip() or len(text.split()) < 20:
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
    model = genai.GenerativeModel("gemini-2.5-flash")
    response = model.generate_content(prompt).text
    return response


def summarize_document(path: str) -> Dict[str, str]:
    """
    Parse document → split into sections → summarize each with Gemini.
    Returns a dict {heading: bullets}
    """
    text = parse_document(path)
    sections = split_by_headings(text)

    summaries = {}
    for title, content in sections.items():
        summary = summarize_section(title, content)
        if summary and "No important points" not in summary:
            summaries[title] = summary

    return summaries


# ---------- API Route ----------
@app.route("/api/upload_pdf", methods=["POST"])
def upload_pdf():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]
    path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(path)

    try:
        summaries = summarize_document(path)
    except Exception as e:
        return jsonify({"error": f"Summarization failed: {str(e)}"}), 500

    return jsonify({
        "summary": summaries,
        "doc_id": os.path.splitext(file.filename)[0]  # use filename as doc_id
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
