from openai import OpenAI
from src.config import EMBEDDING_MODEL_NAME, OPENAI_API_KEY

class EmbeddingFunction:
    def __init__(self):
        print(f"Initializing OpenAI Embedding Model: {EMBEDDING_MODEL_NAME}")
        self.client = OpenAI(api_key=OPENAI_API_KEY)
        self.model_name = EMBEDDING_MODEL_NAME
        
    def __call__(self, input):
        if isinstance(input, str):
            input = [input]
        
        # OpenAI API supports batch processing up to 2048 texts
        # We'll process in batches to avoid rate limits
        batch_size = 100
        all_embeddings = []
        
        for i in range(0, len(input), batch_size):
            batch = input[i:i + batch_size]
            response = self.client.embeddings.create(
                input=batch,
                model=self.model_name
            )
            batch_embeddings = [item.embedding for item in response.data]
            all_embeddings.extend(batch_embeddings)
        
        return all_embeddings

    def embed_query(self, input):
        return self.__call__(input)
        
    def embed_documents(self, input):
        return self.__call__(input)
    
    def name(self):
        """Return the name of the embedding model for ChromaDB"""
        return self.model_name

# Singleton instance
_embedding_function = None

def get_embedding_function():
    global _embedding_function
    if _embedding_function is None:
        _embedding_function = EmbeddingFunction()
    return _embedding_function
