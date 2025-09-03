from pinecone import Pinecone, ServerlessSpec
from app.config import settings

# Initialize Pinecone client
pc = Pinecone(api_key=settings.PINECONE_API_KEY)

# Ensure the index exists
if settings.PINECONE_INDEX_NAME not in [i["name"] for i in pc.list_indexes()]:
    pc.create_index(
        name=settings.PINECONE_INDEX_NAME,
        dimension=384,  # ✅ match your embedding model dimension
        metric="cosine",
        spec=ServerlessSpec(
            cloud="aws",   # or "gcp" if you’re using GCP
            region=settings.PINECONE_ENV
        )
    )

# Connect to the index
index = pc.Index(settings.PINECONE_INDEX_NAME)
collection = index  # keep for compatibility with rest of code
