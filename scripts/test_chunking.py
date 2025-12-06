#!/usr/bin/env python3
"""
TXT dosyasını backend'deki chunk fonksiyonuyla test eder.
"""

import sys
from pathlib import Path

# Backend modüllerini import etmek için path ekle
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from app.ai.text_processor import TextProcessor


def test_chunking(txt_file_path: str):
    """TXT dosyasını chunk'lara ayırır ve analiz eder."""
    print(f"📖 TXT dosyası okunuyor: {txt_file_path}")
    
    # Dosyayı oku
    with open(txt_file_path, 'r', encoding='utf-8') as f:
        full_text = f.read()
    
    print(f"   Toplam karakter: {len(full_text):,}")
    print(f"   Toplam satır: {len(full_text.splitlines()):,}")
    
    # TextProcessor'ı başlat
    print("\n🔧 TextProcessor başlatılıyor...")
    try:
        processor = TextProcessor()
    except Exception as e:
        print(f"❌ TextProcessor başlatılamadı: {e}")
        return
    
    print("\n📝 Chunk'lar oluşturuluyor...")
    chunks = processor.split_into_chunks(full_text, language="en")
    
    # Analiz
    print(f"\n📊 CHUNK ANALİZİ:")
    print(f"   Toplam chunk sayısı: {len(chunks):,}")
    
    if not chunks:
        print("❌ Hiç chunk oluşturulmadı!")
        return
    
    # Chunk uzunlukları
    chunk_lengths = [len(chunk) for chunk in chunks]
    avg_length = sum(chunk_lengths) / len(chunk_lengths)
    min_length = min(chunk_lengths)
    max_length = max(chunk_lengths)
    
    print(f"   Ortalama uzunluk: {avg_length:.1f} karakter")
    print(f"   Minimum uzunluk: {min_length} karakter")
    print(f"   Maksimum uzunluk: {max_length} karakter")
    
    # Uzunluk dağılımı
    too_short = sum(1 for l in chunk_lengths if l < 20)
    good = sum(1 for l in chunk_lengths if 20 <= l <= 280)
    too_long = sum(1 for l in chunk_lengths if l > 280)
    
    print(f"\n   Uzunluk dağılımı:")
    print(f"      Çok kısa (<20): {too_short} ({too_short/len(chunks)*100:.1f}%)")
    print(f"      İyi (20-280): {good} ({good/len(chunks)*100:.1f}%)")
    print(f"      Çok uzun (>280): {too_long} ({too_long/len(chunks)*100:.1f}%)")
    
    # İlk 10 chunk'ı göster
    print(f"\n📋 İLK 10 CHUNK ÖRNEĞİ:")
    for i, chunk in enumerate(chunks[:10], 1):
        preview = chunk[:80].replace('\n', ' ') + "..." if len(chunk) > 80 else chunk.replace('\n', ' ')
        print(f"   {i}. [{len(chunk)} char] {preview}")
    
    # Son 5 chunk'ı göster
    print(f"\n📋 SON 5 CHUNK ÖRNEĞİ:")
    for i, chunk in enumerate(chunks[-5:], len(chunks)-4):
        preview = chunk[:80].replace('\n', ' ') + "..." if len(chunk) > 80 else chunk.replace('\n', ' ')
        print(f"   {i}. [{len(chunk)} char] {preview}")
    
    # Sorunlu chunk'ları bul
    print(f"\n⚠️  SORUNLU CHUNK'LAR:")
    problem_chunks = []
    for i, chunk in enumerate(chunks, 1):
        issues = []
        if len(chunk) < 10:
            issues.append(f"Çok kısa ({len(chunk)} char)")
        if len(chunk) > 280:
            issues.append(f"Çok uzun ({len(chunk)} char)")
        if not chunk.strip():
            issues.append("Boş")
        if issues:
            problem_chunks.append((i, chunk, issues))
    
    if problem_chunks:
        print(f"   {len(problem_chunks)} sorunlu chunk bulundu:")
        for idx, chunk, issues in problem_chunks[:10]:  # İlk 10'unu göster
            preview = chunk[:60].replace('\n', ' ') + "..." if len(chunk) > 60 else chunk.replace('\n', ' ')
            print(f"      Chunk {idx}: {', '.join(issues)} - {preview}")
    else:
        print("   ✅ Sorunlu chunk bulunamadı!")
    
    # Format sorunları
    print(f"\n🔍 FORMAT KONTROLÜ:")
    lines = full_text.splitlines()
    single_word_lines = [line for line in lines if line.strip() and len(line.strip().split()) == 1 and len(line.strip()) < 20]
    
    if single_word_lines:
        print(f"   ⚠️  Tek kelimelik satırlar bulundu ({len(single_word_lines)} adet):")
        unique_single_words = list(set(single_word_lines[:20]))
        print(f"      Örnekler: {', '.join(unique_single_words[:10])}")
    else:
        print("   ✅ Tek kelimelik satır sorunu yok")
    
    # Boş satır kontrolü
    empty_lines = sum(1 for line in lines if not line.strip())
    print(f"   Boş satır sayısı: {empty_lines} ({empty_lines/len(lines)*100:.1f}%)")
    
    print(f"\n✅ Analiz tamamlandı!")


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Kullanım: python scripts/test_chunking.py <txt_file_path>")
        print("\nÖrnek:")
        print('  python scripts/test_chunking.py "txt/Twenty Thousand Leagues under the Sea by Jules Verne.txt"')
        sys.exit(1)
    
    txt_file = Path(sys.argv[1])
    if not txt_file.exists():
        print(f"❌ Dosya bulunamadı: {txt_file}")
        sys.exit(1)
    
    test_chunking(str(txt_file))

