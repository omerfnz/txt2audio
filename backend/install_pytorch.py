"""
PyTorch GPU/CPU Otomatik Kurulum Scripti
"""
import subprocess
import sys
import platform

def check_cuda():
    """CUDA kurulumu kontrol et"""
    try:
        result = subprocess.run(
            ["nvidia-smi"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            print("✓ NVIDIA GPU bulundu!")
            output = result.stdout
            if "12." in output:
                return "cu121"  # CUDA 12.1
            elif "11." in output:
                return "cu118"  # CUDA 11.8
            else:
                return "cu121"  # Default latest
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    
    return None

def install_pytorch():
    """PyTorch'u kur"""
    print("🔍 PyTorch kurulum başladı...\n")
    
    cuda_version = check_cuda()
    
    if cuda_version:
        print(f"✓ GPU (CUDA {cuda_version.upper()}) için PyTorch kuruluyor...\n")
        index_url = f"https://download.pytorch.org/whl/{cuda_version}"
    else:
        print("✓ CPU için PyTorch kuruluyor...\n")
        index_url = "https://download.pytorch.org/whl/cpu"
    
    cmd = [
        sys.executable,
        "-m",
        "pip",
        "install",
        "torch",
        "torchvision",
        "torchaudio",
        "--index-url",
        index_url
    ]
    
    print(f"📦 Komut: {' '.join(cmd)}\n")
    result = subprocess.run(cmd)
    
    if result.returncode == 0:
        print("\n✅ PyTorch başarıyla kuruldu!")
        return True
    else:
        print("\n❌ PyTorch kurulumunda hata!")
        return False

if __name__ == "__main__":
    install_pytorch()
