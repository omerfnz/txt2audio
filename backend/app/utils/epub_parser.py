import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup
import warnings
import re
from typing import Optional, Tuple
from .gutenberg import GutenbergCleaner

# Ignore ebooklib warnings about future changes
warnings.filterwarnings('ignore', category=UserWarning, module='ebooklib')
warnings.filterwarnings('ignore', category=FutureWarning, module='ebooklib')


def extract_text_from_epub(epub_path: str, clean_gutenberg: bool = True) -> str:
    """
    Extracts text content from an EPUB file.
    Optionally cleans Gutenberg-specific text.
    
    Args:
        epub_path (str): Path to the EPUB file.
        clean_gutenberg (bool): If True, removes Gutenberg-specific text.
        
    Returns:
        str: Extracted text content.
    """
    try:
        book = epub.read_epub(epub_path)
        full_text = []
        cleaner = GutenbergCleaner() if clean_gutenberg else None

        for i, item in enumerate(book.get_items()):
            if item.get_type() == ebooklib.ITEM_DOCUMENT:
                # Get HTML content
                content = item.get_content()
                
                if cleaner:
                    # Use cleaner's HTML processing
                    text = cleaner.clean_html_content(content)
                    
                    # Bölümü koru mu kontrol et
                    if not cleaner.should_keep_item(item, text):
                        continue
                        
                    # Metni temizle (ilk bölümde başlık/yazar koru)
                    text = cleaner.clean_text(text, preserve_title_author=(i == 0))
                    
                    if not text or len(text.strip()) < 50:
                        continue
                else:
                    # Basic extraction if no cleaning requested
                    soup = BeautifulSoup(content, 'html.parser')
                    for script in soup(["script", "style", "meta", "link"]):
                        script.decompose()
                    text = soup.get_text(separator='\n\n')
                    text = '\n'.join(line.strip() for line in text.splitlines() if line.strip())
                
                full_text.append(text)
        
        result = '\n\n'.join(full_text)
        
        # Son bir temizlik - fazla boşlukları kaldır
        result = re.sub(r'\n{3,}', '\n\n', result)
        
        result = result.strip()
        
        # Add branding intro as a separate, clean sentence so that
        # sentence-based chunking always keeps it as its own chunk.
        intro_text = "From the library of The Archive Key."
        if result:
            result = f"{intro_text}\n\n{result}"
        else:
            result = intro_text
            
        return result
        
    except Exception as e:
        raise Exception(f"Failed to parse EPUB file: {str(e)}")
