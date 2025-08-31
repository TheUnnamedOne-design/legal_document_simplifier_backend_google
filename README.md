```
legal-ai-backend/
│── app/
│   │── __init__.py
│   │── main.py                 # FastAPI/Flask entry point
│   │
│   ├── config/
│   │   │── __init__.py
│   │   │── settings.py         # Environment variables, Gemini model name
│   │
│   ├── services/
│   │   │── __init__.py
│   │   │── parser.py           # parse_pdf, parse_docx, parse_text, parse_document
│   │   │── chunker.py          # chunk_text
│   │   │── embeddings.py       # embedding_model, legal_model, reranker init
│   │   │── database.py         # ChromaDB client & collection
│   │   │── retrieval.py        # retrieve_and_rerank
│   │   │── gemini_client.py    # genai.configure + Gemini wrapper
│   │   │── legal_tasks.py      # ingest_document, simplify_clause, query_for_answer, risk_check
│   │
│   ├── routes/
│   │   │── __init__.py
│   │   │── legal.py            # API endpoints for uploading docs, querying, simplification, risk-check
│
│── env/
│   │── .env                    # GEMINI_API_KEY and configs
│
│── requirements.txt            # Dependencies
│── README.md                   # Documentation
│── .gitignore
```
