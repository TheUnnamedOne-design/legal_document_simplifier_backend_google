from app.services.embeddings import embedding_model, reranker
from app.services.database import collection
from typing import List

def retrieve_and_rerank(query: str, top_k: int = 5) -> List[str]:
    query_emb = embedding_model.encode([query]).tolist()[0]

    results = collection.query(
        vector=query_emb,
        top_k=top_k * 3,
        include_metadata=True
    )

    candidates = [match['metadata']['text'] for match in results['matches']]
    scores = reranker.predict([(query, c) for c in candidates])

    reranked = sorted(zip(candidates, scores), key=lambda x: x[1], reverse=True)
    return [doc for doc, _ in reranked[:top_k]]
