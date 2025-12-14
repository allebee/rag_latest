import torch
import os

def get_compute_device():
    """
    Returns the best available compute device.
    Priority: CUDA (NVIDIA) > MPS (Apple Silicon) > CPU
    """
    # Check if CPU mode is forced via environment variable
    if os.environ.get('FORCE_CPU', '0') == '1':
        print("FORCE_CPU enabled, using CPU")
        return "cpu"
    
    if torch.cuda.is_available():
        try:
            # Try to perform a simple operation to verify CUDA actually works
            test_tensor = torch.zeros(1, device="cuda")
            del test_tensor
            torch.cuda.empty_cache()
            return "cuda"
        except Exception as e:
            print(f"CUDA is available but not working properly: {e}")
            print("Falling back to CPU")
            return "cpu"
    elif torch.backends.mps.is_available():
        return "mps"
    else:
        return "cpu"

def print_device_info():
    """
    Prints detailed information about the available hardware.
    """
    device = get_compute_device()
    print(f"Selected Compute Device: {device.upper()}")
    
    print("-" * 30)
    print(f"PyTorch Version: {torch.__version__}")
    
    if device == "cuda":
        print(f"CUDA Available: Yes")
        print(f"CUDA Device Name: {torch.cuda.get_device_name(0)}")
        print(f"CUDA Device Count: {torch.cuda.device_count()}")
    elif device == "mps":
        print(f"MPS (Apple Metal) Available: Yes")
    else:
        print("No GPU acceleration detected. Using CPU.")
    print("-" * 30)
