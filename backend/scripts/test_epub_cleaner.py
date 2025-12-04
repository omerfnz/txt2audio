#!/usr/bin/env python3
"""
EPUB temizleme scriptini test eder.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.utils.epub_cleaner import clean_gutenberg_epub

def main():
    input_path = "storage/uploads/test_pg4.epub"
    output_path = "storage/uploads/test_pg4_cleaned.epub"
    
    print("=" * 80)
    print("GUTENBERG EPUB TEMİZLEME TESTİ")
    print("=" * 80)
    print(f"Giriş dosyası: {input_path}")
    print(f"Çıkış dosyası: {output_path}")
    print()
    
    try:
        stats = clean_gutenberg_epub(input_path, output_path)
        
        print("✅ Temizleme tamamlandı!")
        print()
        print("İstatistikler:")
        print(f"  - Orijinal bölüm sayısı: {stats['original_items']}")
        print(f"  - Temizlenen bölüm sayısı: {stats['cleaned_items']}")
        print(f"  - Kaldırılan bölüm sayısı: {stats['removed_items']}")
        print(f"  - Kitap başlığı: {stats['title']}")
        print(f"  - Yazar: {stats['author']}")
        print()
        print(f"Temizlenmiş dosya: {output_path}")
        
    except Exception as e:
        print(f"❌ Hata: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()

