#!/usr/bin/env python3
"""
EPUB dosyasını analiz eder ve Gutenberg metinlerini tespit eder.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup
import re

def analyze_epub(epub_path: str):
    """EPUB dosyasını analiz eder ve içeriği gösterir."""
    book = epub.read_epub(epub_path)
    
    # Metadata
    title = book.get_metadata('DC', 'title')
    creator = book.get_metadata('DC', 'creator')
    print("=" * 80)
    print("EPUB METADATA")
    print("=" * 80)
    print(f"Title: {title}")
    print(f"Author: {creator}")
    print()
    
    # Tüm bölümleri analiz et
    items = list(book.get_items_of_type(ebooklib.ITEM_DOCUMENT))
    print(f"Total items: {len(items)}")
    print()
    
    # Gutenberg pattern'leri
    gutenberg_patterns = [
        r'Project Gutenberg',
        r'Gutenberg',
        r'End of.*Project Gutenberg',
        r'End of the Project Gutenberg',
        r'This eBook is for the use',
        r'Copyright laws',
        r'free of copyright restrictions',
        r'www\.gutenberg\.org',
        r'gutenberg\.org',
        r'If you are not located',
        r'United States',
        r'You must comply',
        r'with the terms',
        r'Project Gutenberg-tm',
        r'Project Gutenberg Literary Archive Foundation',
        r'This eBook was produced',
        r'by the Online Distributed Proofreading Team',
        r'End of this Project Gutenberg',
        r'START OF.*PROJECT GUTENBERG',
        r'START OF THE PROJECT GUTENBERG'
    ]
    
    print("=" * 80)
    print("BÖLÜM ANALİZİ")
    print("=" * 80)
    
    for i, item in enumerate(items):
        content = item.get_content()
        soup = BeautifulSoup(content, 'html.parser')
        text = soup.get_text()
        
        # İlk 500 karakteri göster
        preview = text[:500].replace('\n', ' ')
        preview = re.sub(r'\s+', ' ', preview)
        
        # Gutenberg pattern kontrolü
        gutenberg_matches = []
        for pattern in gutenberg_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                gutenberg_matches.append(pattern)
        
        print(f"\n[{i+1}] {item.get_name()}")
        print(f"    Length: {len(text)} characters")
        print(f"    Preview: {preview}...")
        if gutenberg_matches:
            print(f"    ⚠️  GUTENBERG METNİ TESPİT EDİLDİ: {', '.join(gutenberg_matches[:3])}")
        print("-" * 80)
    
    # İlk ve son bölümlerin tam içeriğini göster
    print("\n" + "=" * 80)
    print("İLK BÖLÜM (İlk 2000 karakter)")
    print("=" * 80)
    if items:
        first_content = items[0].get_content()
        first_soup = BeautifulSoup(first_content, 'html.parser')
        first_text = first_soup.get_text()
        print(first_text[:2000])
    
    print("\n" + "=" * 80)
    print("SON BÖLÜM (Son 2000 karakter)")
    print("=" * 80)
    if items:
        last_content = items[-1].get_content()
        last_soup = BeautifulSoup(last_content, 'html.parser')
        last_text = last_soup.get_text()
        print(last_text[-2000:])

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python analyze_epub.py <epub_path>")
        sys.exit(1)
    
    epub_path = sys.argv[1]
    if not os.path.exists(epub_path):
        print(f"Error: File not found: {epub_path}")
        sys.exit(1)
    
    analyze_epub(epub_path)

