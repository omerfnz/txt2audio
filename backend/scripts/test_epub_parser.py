#!/usr/bin/env python3
"""
EPUB parser'ı test eder - Gutenberg temizleme ile.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.utils.epub_parser import extract_text_from_epub

def main():
    epub_path = "storage/uploads/test_pg4.epub"
    
    print("=" * 80)
    print("EPUB PARSER TEST - GUTENBERG TEMİZLEME")
    print("=" * 80)
    print(f"Dosya: {epub_path}")
    print()
    
    try:
        # Temizlenmiş metin
        cleaned_text = extract_text_from_epub(epub_path, clean_gutenberg=True)
        
        print("✅ Temizleme tamamlandı!")
        print()
        print(f"Toplam karakter sayısı: {len(cleaned_text)}")
        print(f"Toplam satır sayısı: {len(cleaned_text.splitlines())}")
        print()
        print("=" * 80)
        print("İLK 1000 KARAKTER:")
        print("=" * 80)
        print(cleaned_text[:1000])
        print()
        print("=" * 80)
        print("SON 1000 KARAKTER:")
        print("=" * 80)
        print(cleaned_text[-1000:])
        
        # Dosyaya kaydet
        output_path = "storage/uploads/test_pg4_cleaned.txt"
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(cleaned_text)
        print()
        print(f"✅ Temizlenmiş metin kaydedildi: {output_path}")
        
    except Exception as e:
        print(f"❌ Hata: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()

