from src.utils import print_device_info, get_compute_device
from sentence_transformers import SentenceTransformer
import time

def check_hardware_speed():
    print_device_info()
    
    device = get_compute_device()
    print("\nRunning quick benchmark...")
    
    # Load small model
    model = SentenceTransformer("all-MiniLM-L6-v2", device=device)
    sentences = ["This is a test sentence for benchmarking."] * 1000
    
    start_time = time.time()
    model.encode(sentences)
    end_time = time.time()
    
    print(f"Encoded 1000 sentences in {end_time - start_time:.4f} seconds on {device.upper()}")

if __name__ == "__main__":
    check_hardware_speed()
