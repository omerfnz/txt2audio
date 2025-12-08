import torch
import sys

def check_gpu():
    print(f"Python: {sys.version}")
    print(f"Torch: {torch.__version__}")
    print(f"CUDA Available: {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        print(f"Device Name: {torch.cuda.get_device_name(0)}")
        print(f"CUDA Version: {torch.version.cuda}")
        props = torch.cuda.get_device_properties(0)
        print(f"Total VRAM: {props.total_memory / 1e9:.2f} GB")
        
        # Test a small tensor operation
        try:
            x = torch.rand(1000, 1000).cuda()
            y = torch.matmul(x, x)
            print("CUDA tensor operation successful.")
        except Exception as e:
            print(f"CUDA operation failed: {e}")
    else:
        print("Running on CPU.")

if __name__ == "__main__":
    check_gpu()

