import torch

def get_compute_device():
    """
    Returns the best available compute device.
    Priority: CUDA (NVIDIA) > MPS (Apple Silicon) > CPU
    """
    if torch.cuda.is_available():
        return "cuda"
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
