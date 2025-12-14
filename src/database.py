import chromadb
from chromadb.config import Settings
from src.config import CHROMA_PATH
from src.embeddings import get_embedding_function

class VectorDB:
    def __init__(self):
        self.client = chromadb.PersistentClient(path=CHROMA_PATH, settings=Settings(allow_reset=True))
        self.embedding_fn = get_embedding_function()

    def get_or_create_collection(self, name):
        return self.client.get_or_create_collection(
            name=name,
            embedding_function=self.embedding_fn
        )
    
    def reset(self):
        self.client.reset()

def get_db():
    return VectorDB()
