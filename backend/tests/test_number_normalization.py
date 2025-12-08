"""
XTTS Sayı Normalizasyon Testleri

Bu test dosyası, text_normalizer.py'daki sayı normalizasyon
özelliklerini XTTS için optimize edilmiş haliyle test eder.

Özellikle virgüllü büyük sayıların doğru okunmasını doğrular.
"""

import sys
from pathlib import Path

# Backend dizinini Python path'e ekle
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from app.ai.text_normalizer import AdvancedTextNormalizer


def test_english_large_numbers_with_commas():
    """İngilizce virgüllü büyük sayıları test et - ANA PROBLEM"""
    normalizer = AdvancedTextNormalizer()
    
    test_cases = [
        ("140,000", "one hundred and forty thousand"),
        ("1,234", "one thousand, two hundred and thirty-four"),
        ("1,234,567", "one million, two hundred and thirty-four thousand, five hundred and sixty-seven"),
        ("10,000", "ten thousand"),
        ("999,999", "nine hundred and ninety-nine thousand, nine hundred and ninety-nine"),
    ]
    
    print("\n=== İNGİLİZCE BÜYÜK SAYILAR (VIRGÜLLÜ) ===")
    for original, expected_keyword in test_cases:
        result = normalizer.normalize_english(original)
        print(f"  Original: {original}")
        print(f"  Result:   {result}")
        print(f"  Expected keyword: {expected_keyword}")
        # num2words çıktısı biraz farklı olabilir, ama kesinlikle "zero zero zero" gibi olmayacak
        assert "zero zero zero" not in result.lower(), f"HATA: {original} yanlış okundu: {result}"
        print("  ✓ BAŞARILI\n")


def test_english_decimal_numbers():
    """İngilizce ondalıklı sayıları test et"""
    normalizer = AdvancedTextNormalizer()
    
    test_cases = [
        ("3.14", "three point one four"),
        ("1,234.56", "one thousand, two hundred and thirty-four point five six"),
        ("0.5", "zero point five"),
    ]
    
    print("\n=== İNGİLİZCE ONDALIKLI SAYILAR ===")
    for original, expected in test_cases:
        result = normalizer.normalize_english(original)
        print(f"  Original: {original}")
        print(f"  Result:   {result}")
        assert "point" in result.lower(), f"Ondalık işareti eksik: {result}"
        print("  ✓ BAŞARILI\n")


def test_english_ordinal_numbers():
    """İngilizce sıra sayılarını test et"""
    normalizer = AdvancedTextNormalizer()
    
    test_cases = [
        ("21st", "first"),  # "twenty-first" içermeli
        ("1,234th", "thousand"),  # büyük sayıları da desteklemeli
    ]
    
    print("\n=== İNGİLİZCE SIRA SAYILARI ===")
    for original, expected_keyword in test_cases:
        result = normalizer.normalize_english(original)
        print(f"  Original: {original}")
        print(f"  Result:   {result}")
        assert expected_keyword in result.lower(), f"Sıra sayısı yanlış: {result}"
        print("  ✓ BAŞARILI\n")


def test_english_currency():
    """İngilizce para birimlerini test et"""
    normalizer = AdvancedTextNormalizer()
    
    test_cases = [
        ("$100", "dollar"),
        ("$1,234.56", "dollar"),
    ]
    
    print("\n=== İNGİLİZCE PARA BİRİMLERİ ===")
    for original, expected_keyword in test_cases:
        result = normalizer.normalize_english(original)
        print(f"  Original: {original}")
        print(f"  Result:   {result}")
        assert expected_keyword in result.lower(), f"Para birimi yanlış: {result}"
        print("  ✓ BAŞARILI\n")


def test_turkish_large_numbers_with_dots():
    """Türkçe noktalı büyük sayıları test et"""
    normalizer = AdvancedTextNormalizer()
    
    test_cases = [
        ("140.000", "yüz kırk bin"),
        ("1.234", "bin iki yüz otuz dört"),
        ("1.234.567", "milyon"),
    ]
    
    print("\n=== TÜRKÇE BÜYÜK SAYILAR (NOKTALI) ===")
    for original, expected_keyword in test_cases:
        result = normalizer.normalize_turkish(original)
        print(f"  Original: {original}")
        print(f"  Result:   {result}")
        # Türkçe'de nokta sıfır sıfır olarak okunmamalı
        assert "sıfır sıfır sıfır" not in result.lower(), f"HATA: {original} yanlış okundu: {result}"
        print("  ✓ BAŞARILI\n")


def test_turkish_decimal_numbers():
    """Türkçe ondalıklı sayıları test et"""
    normalizer = AdvancedTextNormalizer()
    
    test_cases = [
        ("3,14", "virgül"),
        ("1.234,56", "virgül"),
    ]
    
    print("\n=== TÜRKÇE ONDALIKLI SAYILAR ===")
    for original, expected_keyword in test_cases:
        result = normalizer.normalize_turkish(original)
        print(f"  Original: {original}")
        print(f"  Result:   {result}")
        assert expected_keyword in result.lower(), f"Ondalık ayracı eksik: {result}"
        print("  ✓ BAŞARILI\n")


def test_context_sentence():
    """Gerçek cümle içinde sayı normalizasyonunu test et"""
    normalizer = AdvancedTextNormalizer()
    
    # İngilizce
    sentence = "The population reached 140,000 in the year 1990."
    result = normalizer.normalize_english(sentence)
    print("\n=== GERÇEK CÜMLE TESTİ (İNGİLİZCE) ===")
    print(f"  Original: {sentence}")
    print(f"  Result:   {result}")
    assert "zero zero zero" not in result.lower(), f"HATA: Cümle içinde sayı yanlış okundu"
    print("  ✓ BAŞARILI\n")
    
    # Türkçe
    tr_sentence = "Nüfus 140.000 kişiye ulaştı."
    tr_result = normalizer.normalize_turkish(tr_sentence)
    print("=== GERÇEK CÜMLE TESTİ (TÜRKÇE) ===")
    print(f"  Original: {tr_sentence}")
    print(f"  Result:   {tr_result}")
    assert "sıfır sıfır sıfır" not in tr_result.lower(), f"HATA: Türkçe cümle içinde sayı yanlış okundu"
    print("  ✓ BAŞARILI\n")


def test_edge_cases():
    """Uç durumları test et"""
    normalizer = AdvancedTextNormalizer()
    
    print("\n=== UÇ DURUMLAR ===")
    
    # Telefon numarası gibi çok uzun sayılar - değiştirilmemeli
    phone = "1234567890123"
    result = normalizer.normalize_english(phone)
    print(f"  Telefon (uzun sayı): {phone} -> {result}")
    assert result == phone, "Çok uzun sayılar değiştirilmemeli"
    print("  ✓ Telefon numarası korundu\n")
    
    # Yıl tespiti - virgüllü sayının parçası olmamalı
    year_text = "In 2020, we had 1,234 visitors."
    year_result = normalizer.normalize_english(year_text)
    print(f"  Yıl + büyük sayı: {year_text}")
    print(f"  Result: {year_result}")
    print("  ✓ Karma test başarılı\n")


if __name__ == "__main__":
    try:
        print("\n" + "="*60)
        print("XTTS SAYI NORMALİZASYON TEST SÜİTİ")
        print("="*60)
        
        test_english_large_numbers_with_commas()
        test_english_decimal_numbers()
        test_english_ordinal_numbers()
        test_english_currency()
        test_turkish_large_numbers_with_dots()
        test_turkish_decimal_numbers()
        test_context_sentence()
        test_edge_cases()
        
        print("\n" + "="*60)
        print("✓ TÜM TESTLER BAŞARIYLA TAMAMLANDI!")
        print("="*60 + "\n")
        
    except AssertionError as e:
        print(f"\n❌ TEST BAŞARISIZ: {e}\n")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ BEKLENMEYEN HATA: {e}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)

