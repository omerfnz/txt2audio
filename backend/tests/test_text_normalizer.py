import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.ai.text_normalizer import AdvancedTextNormalizer

def test_english_normalization():
    print("Testing English Normalization...")
    normalizer = AdvancedTextNormalizer()
    
    # 1. Abbreviations
    assert normalizer.normalize("Mr. Smith", "en") == "Mister Smith"
    assert normalizer.normalize("Dr. House", "en") == "Doctor House"
    
    # 2. Currency
    res = normalizer.normalize("It costs $100.", "en")
    print(f"  $100 -> {res}")
    assert "one hundred dollars" in res
    
    # 3. Years
    res = normalizer.normalize("In 1998, we met.", "en")
    print(f"  1998 -> {res}")
    assert "nineteen ninety-eight" in res
    
    # 4. Ordinals
    res = normalizer.normalize("The 21st century.", "en")
    print(f"  21st -> {res}")
    assert "twenty-first" in res
    
    print("✅ English normalization tests passed!")

def test_turkish_normalization():
    print("\nTesting Turkish Normalization...")
    normalizer = AdvancedTextNormalizer()
    
    # 1. Currency
    res = normalizer.normalize("Fiyatı 100 TL.", "tr")
    print(f"  100 TL -> {res}")
    # num2words tr çıktısı "yüz türk lirası" olabilir (küçük harf vs)
    assert "yüz" in res.lower()
    
    # 2. Numbers
    res = normalizer.normalize("5 elma", "tr")
    print(f"  5 -> {res}")
    assert "beş" in res.lower()
    
    print("✅ Turkish normalization tests passed!")

if __name__ == "__main__":
    try:
        test_english_normalization()
        test_turkish_normalization()
        print("\n🎉 All tests passed!")
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
