"""
Gutenberg EPUB temizleme mantığını içeren ortak modül.
"""
import re
from typing import List, Tuple, Optional
from bs4 import BeautifulSoup
import ebooklib

class GutenbergCleaner:
    """Gutenberg EPUB dosyalarını temizler."""
    
    # Gutenberg pattern'leri - bu metinler kaldırılacak
    GUTENBERG_PATTERNS = [
        r'Project Gutenberg',
        r'Gutenberg',
        r'END OF.*PROJECT GUTENBERG',
        r'END OF THE PROJECT GUTENBERG',
        r'START OF.*PROJECT GUTENBERG',
        r'START OF THE PROJECT GUTENBERG',
        r'This ebook is for the use',
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
        r'Updated editions will replace',
        r'Creating the works from print editions',
        r'no one owns a United States copyright',
        r'can copy and distribute it',
        r'without permission and without paying',
        r'copyright royalties',
        r'Special rules',
        r'General Terms of Use',
        r'Release date:',
        r'Most recently updated:',
        r'Language:',
        r'eBook #\d+',
        r'\[eBook #\d+\]',
    ]
    
    # Bu metinler başlık/yazar bilgisinden sonra gelirse içerik başlangıcı olarak kabul edilir
    CONTENT_START_MARKERS = [
        r'\*\*\* START OF',
        r'START OF',
        r'Title:',
        r'Author:',
    ]
    
    def __init__(self):
        """Gutenberg temizleyiciyi başlatır."""
        self.compiled_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in self.GUTENBERG_PATTERNS]
        self.content_start_markers = [re.compile(marker, re.IGNORECASE) for marker in self.CONTENT_START_MARKERS]
    
    def is_gutenberg_text(self, text: str) -> bool:
        """Metnin Gutenberg metni olup olmadığını kontrol eder."""
        if not text:
            return False
        for pattern in self.compiled_patterns:
            if pattern.search(text):
                return True
        return False
    
    def extract_title_and_author(self, soup: BeautifulSoup) -> Tuple[Optional[str], Optional[str]]:
        """HTML'den başlık ve yazar bilgisini çıkarır."""
        title = None
        author = None
        
        # Metadata'dan al
        title_tags = soup.find_all(['h1', 'h2', 'h3', 'title'])
        for tag in title_tags:
            text = tag.get_text().strip()
            if text and not self.is_gutenberg_text(text):
                # "Title:" ile başlayan metinleri temizle
                if text.startswith('Title:'):
                    title = text.replace('Title:', '').strip()
                elif 'Title:' in text:
                    parts = text.split('Title:')
                    if len(parts) > 1:
                        title = parts[1].strip()
                elif not title and len(text) < 200:  # Çok uzun değilse başlık olabilir
                    title = text
                break
        
        # Yazar bilgisini ara
        author_patterns = [
            r'Author:\s*(.+)',
            r'By\s+(.+)',
            r'Written by\s+(.+)',
        ]
        text_content = soup.get_text()
        for pattern in author_patterns:
            match = re.search(pattern, text_content, re.IGNORECASE)
            if match:
                author = match.group(1).strip()
                # Gutenberg metinlerini temizle
                for gutenberg_pattern in self.compiled_patterns:
                    author = gutenberg_pattern.sub('', author).strip()
                if author:
                    break
        
        return title, author
    
    def clean_text(self, text: str, preserve_title_author: bool = True) -> str:
        """Metni Gutenberg metinlerinden temizler."""
        if not text:
            return ""
            
        lines = text.split('\n')
        cleaned_lines = []
        content_started = False
        title_found = False
        author_found = False
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Başlık ve yazar bilgisini koru (sadece ilk kez)
            if preserve_title_author:
                if not title_found and ('Title:' in line or (len(line) < 200 and not self.is_gutenberg_text(line))):
                    # Başlık olabilir
                    clean_title = re.sub(r'Title:\s*', '', line, flags=re.IGNORECASE).strip()
                    if clean_title and not self.is_gutenberg_text(clean_title):
                        cleaned_lines.append(clean_title)
                        title_found = True
                        continue
                
                if not author_found and ('Author:' in line or line.startswith('By ') or 'Written by' in line):
                    # Yazar bilgisi
                    clean_author = re.sub(r'(Author:|By |Written by )\s*', '', line, flags=re.IGNORECASE).strip()
                    if clean_author and not self.is_gutenberg_text(clean_author):
                        cleaned_lines.append(clean_author)
                        author_found = True
                        continue
            
            # Gutenberg metinlerini kontrol et
            if self.is_gutenberg_text(line):
                # "START OF" gibi marker'ları içerik başlangıcı olarak kabul et
                if any(marker.search(line) for marker in self.content_start_markers):
                    content_started = True
                    continue
                # Diğer Gutenberg metinlerini atla
                continue
            
            # İçerik başladı mı kontrol et
            if not content_started:
                # Hala başlık/yazar bölümündeyiz, içerik başlangıcını ara
                if any(marker.search(line) for marker in self.content_start_markers):
                    content_started = True
                    continue
                # Çok kısa satırlar genellikle başlık/yazar bilgisidir
                if len(line) < 100:
                    continue
            
            # Normal içerik satırı
            cleaned_lines.append(line)
        
        return '\n\n'.join(cleaned_lines)
    
    def clean_html_content(self, html_content: bytes) -> str:
        """HTML içeriğini temizler ve sadece metni döndürür."""
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Script ve style tag'lerini kaldır
        for script in soup(["script", "style", "meta", "link"]):
            script.decompose()
        
        # Metni çıkar
        text = soup.get_text(separator='\n')
        
        # Fazla boşlukları temizle
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        text = '\n'.join(lines)
        
        return text
    
    def should_keep_item(self, item, text: str) -> bool:
        """Bu bölümün korunup korunmayacağını belirler."""
        # Çok kısa bölümler genellikle gereksizdir
        if len(text) < 100:
            return False
        
        # Tamamen Gutenberg metni olan bölümleri atla
        lines = text.split('\n')
        if not lines:
            return False
            
        gutenberg_line_count = sum(1 for line in lines if self.is_gutenberg_text(line.strip()))
        if gutenberg_line_count > len(lines) * 0.8:  # %80'den fazlası Gutenberg metni
            return False
        
        return True
