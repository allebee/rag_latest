from sentence_transformers import SentenceTransformer
from src.config import EMBEDDING_MODEL_NAME
from src.utils import get_compute_device
import torch

class EmbeddingFunction:
    def __init__(self):
        device = get_compute_device()
        print(f"Embedding model initialized on: {device.upper()}")
        
        try:
            self.model = SentenceTransformer(EMBEDDING_MODEL_NAME, device=device)
        except Exception as e:
            if device == "cuda":
                print(f"Failed to load model on CUDA: {e}")
                print("Retrying with CPU...")
                device = "cpu"
                self.model = SentenceTransformer(EMBEDDING_MODEL_NAME, device=device)
            else:
                raise e

    def __call__(self, input):
        if isinstance(input, str):
            input = [input]
        return self.model.encode(input).tolist()

    def embed_query(self, input):
        return self.__call__(input)
        
    def embed_documents(self, input):
        return self.__call__(input)
    
    def name(self):
        """Return the name of the embedding model for ChromaDB"""
        return EMBEDDING_MODEL_NAME

# Singleton instance
_embedding_function = None

def get_embedding_function():
    global _embedding_function
    if _embedding_function is None:
        _embedding_function = EmbeddingFunction()
    return _embedding_function
