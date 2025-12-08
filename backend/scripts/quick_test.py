"""
Hızlı Test Script - XTTS Sayı Normalizasyonu

Kullanım:
    cd backend
    ..\venv\Scripts\activate
    python scripts/quick_test.py
"""

import sys
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from app.ai.text_normalizer import AdvancedTextNormalizer

def main():
    normalizer = AdvancedTextNormalizer()
    
    print("\n" + "="*60)
    print("XTTS SAYI OKUMA - HIZLI TEST")
    print("="*60)
    
    # Problem örneği
    print("\n🔴 PROBLEM ÖRNEĞİ:")
    problem_text = "The population was 140,000 in the year 1990."
    print(f"Giriş:  {problem_text}")
    print(f"Çıkış:  {normalizer.normalize_english(problem_text)}")
    
    # Daha fazla örnek
    test_cases = [
        ("There are 1,234,567 people in the city.", "en"),
        ("The price is $140,000 for the house.", "en"),
        ("Pi is approximately 3.14159.", "en"),
        ("Nüfus 140.000 kişiye ulaştı.", "tr"),
        ("Fiyat 1.234.567 TL olarak belirlendi.", "tr"),
    ]
    
    print("\n✅ DİĞER ÖRNEKLER:")
    for text, lang in test_cases:
        print(f"\n[{lang.upper()}] Giriş:  {text}")
        if lang == "en":
            result = normalizer.normalize_english(text)
        else:
            result = normalizer.normalize_turkish(text)
        print(f"       Çıkış:  {result}")
    
    print("\n" + "="*60)
    print("✓ TEST TAMAMLANDI")
    print("="*60 + "\n")

if __name__ == "__main__":
    main()

