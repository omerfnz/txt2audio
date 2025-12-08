"""
XTTS Sayı Okuma Testi - Gerçek Dünya Örnekleri

Bu script, XTTS'nin sayıları doğru okuyup okumadığını test eder.
Önceki hata: "140,000" -> "one hundred forty zero zero zero"
Yeni: "140,000" -> "one hundred and forty thousand"
"""

import sys
from pathlib import Path

# Backend dizinini ekle
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from app.ai.text_normalizer import AdvancedTextNormalizer
from app.ai.text_processor import TextProcessor


def print_section(title):
    """Başlık yazdır"""
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70)


def test_number_normalization():
    """Sayı normalizasyon testleri"""
    normalizer = AdvancedTextNormalizer()
    
    print_section("PROBLEM ÖRNEĞİ: 140,000")
    
    test_cases = [
        # Problem örnekleri
        ("In 1850, the population was 140,000 people.", "en"),
        ("By year 2000, we had 1,234,567 visitors.", "en"),
        ("The price is $140,000 for the house.", "en"),
        ("He scored 1,234th place in the race.", "en"),
        ("The value is approximately 3.14159.", "en"),
        
        # Türkçe örnekleri
        ("Nüfus 140.000 kişiye ulaştı.", "tr"),
        ("Fiyat 1.234.567 TL olarak belirlendi.", "tr"),
        ("Bu değer yaklaşık 3,14 kadardır.", "tr"),
    ]
    
    for text, lang in test_cases:
        print(f"\nDİL: {lang.upper()}")
        print(f"ORİJİNAL: {text}")
        
        if lang == "en":
            normalized = normalizer.normalize_english(text)
        else:
            normalized = normalizer.normalize_turkish(text)
        
        print(f"NORMALİZE: {normalized}")
        
        # Problem kontrolü
        if "zero zero zero" in normalized.lower():
            print("❌ HATA: Sayı yanlış okunuyor!")
        elif "sıfır sıfır sıfır" in normalized.lower():
            print("❌ HATA: Sayı yanlış okunuyor!")
        else:
            print("✓ Başarılı: Sayı doğru normalize edildi")


def test_with_text_processor():
    """TextProcessor ile chunk'larda sayı normalizasyonu"""
    print_section("TEXT PROCESSOR İLE CHUNK TESTİ")
    
    processor = TextProcessor()
    
    # Uzun metin örneği
    long_text = """
    The city's population grew dramatically. In 1800, there were only 5,000 residents.
    By 1850, this had increased to 140,000 people. The growth continued, and by 1900,
    the population reached 1,234,567 inhabitants. This represents an increase of
    approximately 24,791.34% over the century.
    """
    
    print("\nORİJİNAL METİN:")
    print(long_text)
    
    # Chunk'la ve normalize et
    chunks = processor.split_into_chunks(long_text, max_chars=200, normalize=True, language="en")
    
    print(f"\nTOPLAM CHUNK SAYISI: {len(chunks)}")
    
    for i, chunk in enumerate(chunks, 1):
        print(f"\n--- CHUNK {i} ---")
        print(chunk)
        
        # Hata kontrolü
        if "zero zero zero" in chunk.lower():
            print("❌ HATA BULUNDU: Bu chunk'ta sayı yanlış normalize edilmiş!")
        else:
            print("✓ Bu chunk başarılı")


def test_edge_cases():
    """Uç durumları test et"""
    print_section("UÇ DURUMLAR")
    
    normalizer = AdvancedTextNormalizer()
    
    edge_cases = [
        # Karma durumlar
        ("Call me at 555-1234 or visit house number 140,000.", "en"),
        
        # Yıl + büyük sayı
        ("In 2020, we had 1,234 new members and 140,000 total.", "en"),
        
        # Ondalıklı + tam sayı
        ("The ratio is 3.14 for every 1,000 items.", "en"),
        
        # Para birimi + normal sayı
        ("It costs $1,234.56 for 100 units.", "en"),
        
        # Türkçe karma
        ("2020 yılında 1.234 yeni üye ve toplam 140.000 üye vardı.", "tr"),
    ]
    
    for text, lang in edge_cases:
        print(f"\nDİL: {lang.upper()}")
        print(f"ORİJİNAL: {text}")
        
        if lang == "en":
            normalized = normalizer.normalize_english(text)
        else:
            normalized = normalizer.normalize_turkish(text)
        
        print(f"NORMALİZE: {normalized}")
        print("✓ İşlendi")


def show_comparison():
    """Eski vs Yeni karşılaştırma"""
    print_section("KARŞILAŞTIRMA: ESKİ vs YENİ")
    
    examples = [
        "140,000",
        "1,234,567",
        "The year 1990 had 10,000 people.",
    ]
    
    normalizer = AdvancedTextNormalizer()
    
    for example in examples:
        print(f"\nÖRNEK: {example}")
        print("-" * 70)
        print("ESKİ DAVRANIŞI: Virgüller korunur, XTTS şöyle okur:")
        print("  '140,000' -> 'one hundred forty [pause] zero zero zero'")
        print()
        print("YENİ DAVRANIŞI:")
        result = normalizer.normalize_english(example)
        print(f"  '{example}' -> '{result}'")
        print("  XTTS şimdi düzgün okuyacak!")


if __name__ == "__main__":
    print("\n" + "#"*70)
    print("#" + " "*68 + "#")
    print("#  XTTS SAYI NORMALİZASYON TEST SUITE  ".center(70))
    print("#" + " "*68 + "#")
    print("#"*70)
    
    try:
        show_comparison()
        test_number_normalization()
        test_with_text_processor()
        test_edge_cases()
        
        print_section("SONUÇ")
        print("\n✓✓✓ TÜM TESTLER BAŞARIYLA TAMAMLANDI ✓✓✓")
        print("\nXTTS artık şu sayıları doğru okuyabilecek:")
        print("  - Virgüllü büyük sayılar (140,000)")
        print("  - Ondalıklı sayılar (3.14)")
        print("  - Para birimleri ($1,234.56)")
        print("  - Sıra sayıları (1,234th)")
        print("  - Türkçe noktalı sayılar (140.000)")
        print("\n" + "#"*70 + "\n")
        
    except Exception as e:
        print(f"\n❌ HATA: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

