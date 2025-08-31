from sentence_transformers import SentenceTransformer, CrossEncoder

embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
legal_model = SentenceTransformer("nlpaueb/legal-bert-base-uncased")
reranker = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
