from sentence_transformers import SentenceTransformer
from src.config import EMBEDDING_MODEL_NAME
from src.utils import get_compute_device
import torch

class EmbeddingFunction:
    def __init__(self):
        device = get_compute_device()
        print(f"Embedding model initialized on: {device.upper()}")
        self.model = SentenceTransformer(EMBEDDING_MODEL_NAME, device=device)

    def __call__(self, input):
        if isinstance(input, str):
            input = [input]
        return self.model.encode(input).tolist()

    def embed_query(self, input):
        return self.__call__(input)
        
    def embed_documents(self, input):
        return self.__call__(input)

# Singleton instance
_embedding_function = None

def get_embedding_function():
    global _embedding_function
    if _embedding_function is None:
        _embedding_function = EmbeddingFunction()
    return _embedding_function
