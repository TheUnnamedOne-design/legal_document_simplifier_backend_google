from pinecone import Pinecone, ServerlessSpec
from app.config import settings

pc = Pinecone(api_key=settings.PINECONE_API_KEY)

# Ensure index exists
if settings.PINECONE_INDEX_NAME not in [i['name'] for i in pc.list_indexes()]:
    pc.create_index(
        name=settings.PINECONE_INDEX_NAME,
        dimension=1024,  # Change to your embedding dimension
        metric="cosine",
        spec=ServerlessSpec(
            cloud="aws",  # or "gcp" if using GCP
            region=settings.PINECONE_ENV
        )
    )

index = pc.Index(settings.PINECONE_INDEX_NAME)
collection = index  # for compatibility with rest of codebase
