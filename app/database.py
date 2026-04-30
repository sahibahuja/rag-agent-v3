import os
from dotenv import load_dotenv
from qdrant_client import QdrantClient

# Load variables from .env
load_dotenv()

# Global variable to hold the client instance for Singleton pattern
_client = None

# CONFIGURATION
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "agent_knowledge_2")
PARENT_COLLECTION_NAME = os.getenv("PARENT_COLLECTION_NAME", "agent_knowledge_parents_2")
# Standardizing names for Phase 3
EMBED_MODEL = os.getenv("EMBED_MODEL", "BAAI/bge-small-en-v1.5") 

def get_client() -> QdrantClient:
    """
    Returns a single instance of the Qdrant client. 
    Initialization happens only when this function is called.
    """
    global _client
    if _client is None:
        db_host = os.getenv("QDRANT_HOST", "localhost")
        
        # Logic to handle both Local Path and Docker/Remote Host
        if db_host.startswith("./") or "/" in db_host or "\\" in db_host:
            _client = QdrantClient(path=db_host)
        else:
            _client = QdrantClient(
                host=db_host, 
                port=int(os.getenv("QDRANT_PORT", 6333))
            )
        
        # Porting your Phase 1 logic: Set the model for FastEmbed
        _client.set_model(EMBED_MODEL)
        
    return _client

def init_db():
    """Ensures the collection exists and handles dimension safety checks"""
    q_client = get_client()
    
    # 1. Initialize Child Collection (Vector Search)
    if q_client.collection_exists(COLLECTION_NAME):
        info = q_client.get_collection(COLLECTION_NAME)
        vector_config = info.config.params.vectors
        
        if vector_config is not None:
            if isinstance(vector_config, dict):
                current_vector = vector_config.get(EMBED_MODEL)
                current_size = current_vector.size if current_vector else None
            else:
                current_size = getattr(vector_config, 'size', None)

            if current_size:
                expected_size = 1024 if "m3" in EMBED_MODEL.lower() or "large" in EMBED_MODEL.lower() else 384
                if current_size != expected_size:
                    print(f"⚠️ Mismatch: Current {current_size} != Expected {expected_size}. Recreating...")
                    q_client.delete_collection(COLLECTION_NAME)

    # 2. Initialize Parent Collection (Full-Text Store - No vectors needed)
    if not q_client.collection_exists(PARENT_COLLECTION_NAME):
        print(f"--- Creating Parent Collection: {PARENT_COLLECTION_NAME} ---")
        # Creating a collection with empty vector config as it will only store payload
        from qdrant_client.http.models import VectorParams, Distance
        q_client.create_collection(
            collection_name=PARENT_COLLECTION_NAME,
            vectors_config={} # No embeddings for parent collection to save space/compute
        )
