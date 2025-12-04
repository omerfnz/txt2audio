import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup
import re
from typing import List, Tuple, Optional
from .gutenberg import GutenbergCleaner


def clean_gutenberg_epub(epub_path: str, output_path: str) -> dict:
    """
    Gutenberg EPUB dosyasını temizler.
    
    Args:
        epub_path: Kaynak EPUB dosyası yolu
        output_path: Çıktı EPUB dosyası yolu
        
    Returns:
        dict: Temizleme istatistikleri
    """
    cleaner = GutenbergCleaner()
    
    book = epub.read_epub(epub_path)
    
    # Metadata'yı al
    title_meta = book.get_metadata('DC', 'title')
    author_meta = book.get_metadata('DC', 'creator')
    
    title = title_meta[0][0] if title_meta else None
    author = author_meta[0][0] if author_meta else None
    
    # Yeni kitap oluştur
    cleaned_book = epub.EpubBook()
    
    # Metadata'yı kopyala
    if title:
        cleaned_book.set_identifier(book.get_metadata('DC', 'identifier')[0][0] if book.get_metadata('DC', 'identifier') else 'cleaned-book')
        cleaned_book.set_title(title)
    if author:
        cleaned_book.add_author(author)
    
    stats = {
        'original_items': 0,
        'cleaned_items': 0,
        'removed_items': 0,
        'title': title,
        'author': author
    }
    
    # Tüm bölümleri işle
    items = list(book.get_items_of_type(ebooklib.ITEM_DOCUMENT))
    stats['original_items'] = len(items)
    
    cleaned_chapters = []
    title_found = False
    author_found = False
    
    for i, item in enumerate(items):
        content = item.get_content()
        text = cleaner.clean_html_content(content)
        
        # İlk bölümde başlık ve yazar bilgisini çıkar
        if i == 0 and not title_found:
            soup = BeautifulSoup(content, 'html.parser')
            extracted_title, extracted_author = cleaner.extract_title_and_author(soup)
            if extracted_title and not title:
                title = extracted_title
                cleaned_book.set_title(title)
            if extracted_author and not author:
                author = extracted_author
                cleaned_book.add_author(author)
            title_found = True
            author_found = True
        
        # Bölümü temizle
        cleaned_text = cleaner.clean_text(text, preserve_title_author=(i == 0))
        
        # Bölümü koru mu kontrol et
        if not cleaner.should_keep_item(item, cleaned_text):
            stats['removed_items'] += 1
            continue
        
        # Yeni bölüm oluştur
        chapter = epub.EpubHtml(
            title=f"Chapter {len(cleaned_chapters) + 1}",
            file_name=f"chapter_{len(cleaned_chapters) + 1}.xhtml",
            lang='en'
        )
        chapter.content = f'<html><head><title>Chapter {len(cleaned_chapters) + 1}</title></head><body><p>{cleaned_text.replace(chr(10), "</p><p>")}</p></body></html>'
        cleaned_book.add_item(chapter)
        cleaned_chapters.append(chapter)
        stats['cleaned_items'] += 1
    
    # Spine oluştur
    cleaned_book.spine = cleaned_chapters
    
    # Dosyayı kaydet
    epub.write_epub(output_path, cleaned_book)
    
    return stats

