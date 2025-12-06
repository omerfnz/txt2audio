#!/usr/bin/env python3
"""
HTML e-kitap dosyasını temizleyip TXT formatına dönüştüren script.

Kullanım:
    python scripts/html_to_txt.py <input_html_file> [output_txt_file]
    
Örnek:
    python scripts/html_to_txt.py "txt/Twenty Thousand Leagues under the Sea by Jules Verne.html"
"""

import sys
import re
from pathlib import Path
from bs4 import BeautifulSoup
from typing import Optional


class HTMLToTXTConverter:
    """HTML e-kitap dosyalarını temizleyip TXT formatına dönüştürür."""
    
    def __init__(self):
        self.soup = None
        self.title = None
        self.author = None
    
    def read_html(self, file_path: Path) -> str:
        """HTML dosyasını okur."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            print(f"❌ Dosya okuma hatası: {e}")
            sys.exit(1)
    
    def parse_html(self, html_content: str):
        """HTML içeriğini BeautifulSoup ile parse eder."""
        self.soup = BeautifulSoup(html_content, 'lxml')
    
    def extract_metadata(self):
        """Kitap adı ve yazar adını HTML'den çıkarır."""
        # Title'ı bul - önce span içinde
        title_elem = self.soup.find('span', {'id': 'pg-title-no-subtitle'})
        if title_elem:
            self.title = title_elem.get_text(strip=True)
        
        # Author'ı bul - pg-header-authlist içinde
        auth_list = self.soup.find('div', {'id': 'pg-header-authlist'})
        if auth_list:
            auth_p = auth_list.find('p')
            if auth_p:
                auth_text = auth_p.get_text(strip=True)
                if ':' in auth_text:
                    self.author = auth_text.split(':', 1)[1].strip()
        
        # Alternatif: pg-machine-header içinde
        if not self.title or not self.author:
            machine_header = self.soup.find('div', {'id': 'pg-machine-header'})
            if machine_header:
                # Title'ı bul
                if not self.title:
                    title_p = machine_header.find('p', string=re.compile(r'Title', re.I))
                    if title_p:
                        title_text = title_p.get_text(strip=True)
                        if ':' in title_text:
                            self.title = title_text.split(':', 1)[1].strip()
                
                # Author'ı bul
                if not self.author:
                    auth_p = machine_header.find('p', string=re.compile(r'Author', re.I))
                    if auth_p:
                        auth_text = auth_p.get_text(strip=True)
                        if ':' in auth_text:
                            self.author = auth_text.split(':', 1)[1].strip()
        
        # Son çare: h1 ve h2'den al
        if not self.title:
            h1 = self.soup.find('h1')
            if h1:
                self.title = h1.get_text(strip=True)
        
        if not self.author:
            # h2'de "by" ile başlayan
            for h2 in self.soup.find_all('h2'):
                h2_text = h2.get_text(strip=True)
                if re.match(r'^by\s+', h2_text, re.I):
                    self.author = re.sub(r'^by\s+', '', h2_text, flags=re.I).strip()
                    break
    
    def remove_header_footer(self):
        """Project Gutenberg header ve footer'ını kaldırır."""
        # Metadata'yı önce çıkar
        self.extract_metadata()
        
        # Header'ı kaldır
        pg_header = self.soup.find('section', {'id': 'pg-header'})
        if pg_header:
            pg_header.decompose()
        
        # Footer'ı kaldır
        pg_footer = self.soup.find('section', {'id': 'pg-footer'})
        if pg_footer:
            pg_footer.decompose()
        
        # Start separator'ı kaldır
        start_sep = self.soup.find('div', {'id': 'pg-start-separator'})
        if start_sep:
            start_sep.decompose()
        
        # End separator'ı kaldır
        end_sep = self.soup.find('div', {'id': 'pg-end-separator'})
        if end_sep:
            end_sep.decompose()
        
        # Script ve style taglarını kaldır
        for tag in self.soup.find_all(['script', 'style']):
            tag.decompose()
    
    def remove_contents(self):
        """Contents (içindekiler) ve List of Illustrations bölümünü kaldırır."""
        # "Contents" veya "List of Illustrations" başlığını bul
        contents_headings = []
        for heading in self.soup.find_all(['h1', 'h2', 'h3']):
            text = heading.get_text(strip=True).lower()
            if any(keyword in text for keyword in ['contents', 'table of contents', 'list of illustrations', 'illustrations']):
                contents_headings.append(heading)
        
        # Her bir başlığı ve içeriğini kaldır
        for contents_heading in contents_headings:
            # Contents başlığından sonraki tüm içeriği bul
            # Genellikle bir tablo veya liste olur
            current = contents_heading.next_sibling
            
            # Contents başlığını ve sonrasındaki tabloyu/listeyi kaldır
            # Bir sonraki bölüm başlığına kadar (h1, h2, div.chapter vb.)
            while current:
                next_sibling = current.next_sibling
                
                # Eğer bir bölüm başlığı veya chapter div'i bulursak, dur
                if hasattr(current, 'name'):
                    if current.name in ['h1', 'h2', 'h3']:
                        text = current.get_text(strip=True).lower()
                        # PART, CHAPTER gibi bölüm başlıkları
                        if 'part' in text or 'chapter' in text or (current.name == 'h1' and len(text) > 10):
                            # Bölüm başlığı bulundu, dur
                            break
                    if current.name == 'div' and 'chapter' in current.get('class', []):
                        # Chapter div'i bulundu, dur
                        break
                    if current.name in ['table', 'ul', 'ol']:
                        # İçindekiler tablosu/listesi, kaldır
                        current.decompose()
                
                current = next_sibling
            
            # Contents başlığını kaldır
            contents_heading.decompose()
        
        # Contents'ten önceki boş h1 ve h2'leri de kaldır (kitap adı, yazar)
        for tag in self.soup.find_all(['h1', 'h2']):
            text = tag.get_text(strip=True).lower()
            if 'by' in text and len(text) < 50:
                # Yazar satırı
                tag.decompose()
            elif tag.name == 'h1' and len(text) < 100 and not any(word in text for word in ['part', 'chapter']):
                # Kitap adı (ama PART veya CHAPTER değilse)
                tag.decompose()
        
        # HR taglarını kaldır
        for hr in self.soup.find_all('hr'):
            hr.decompose()
    
    def clean_text_content(self) -> str:
        """Temiz metin içeriğini çıkarır."""
        # Contents'i kaldır
        self.remove_contents()
        
        # Body içeriğini al
        body = self.soup.find('body')
        if not body:
            body = self.soup
        
        # Italik ve bold taglarını kaldır ama içeriğini koru (unwrap)
        for tag in body.find_all(['i', 'b', 'em', 'strong']):
            tag.unwrap()
        
        # Metni satır satır çıkar (paragrafları koru)
        text = body.get_text(separator='\n', strip=False)
        
        # HTML entity'lerini düzelt
        text = self._decode_html_entities(text)
        
        # Tek kelimelik satırları birleştir (ama paragraf yapısını koru)
        text = self._merge_single_word_lines(text)
        
        # Fazla boşlukları temizle
        text = self._clean_whitespace(text)
        
        # Paragrafları düzenle
        text = self._format_paragraphs(text)
        
        # Başa header ekle
        header = self._create_header()
        if header:
            text = header + '\n\n' + text
        
        return text
    
    def _merge_single_word_lines(self, text: str) -> str:
        """Tek kelimelik satırları birleştirir (paragraf yapısını korur)."""
        lines = text.split('\n')
        merged_lines = []
        
        for i, line in enumerate(lines):
            original_line = line
            line = line.strip()
            
            # Boş satır - paragraf sonu, koru
            if not line:
                merged_lines.append('')
                continue
            
            # Tek kelimelik satır kontrolü (25 karakterden kısa ve tek kelime)
            words = line.split()
            is_single_word = len(words) == 1 and len(line) < 25
            
            # Özel durumlar: noktalama ile biten kısa satırlar (örn: "lat.", "long.")
            if is_single_word and line.endswith(('.', ',', ';', ':', '!', '?', '"', "'")):
                is_single_word = True
            
            if is_single_word:
                # Önceki satırla birleştir (ama boş satır varsa birleştirme)
                if merged_lines and merged_lines[-1] and merged_lines[-1].strip():
                    # Önceki satırın sonuna ekle
                    merged_lines[-1] = merged_lines[-1].rstrip() + ' ' + line
                else:
                    # Önceki satır boşsa, yeni satır olarak ekle
                    merged_lines.append(line)
            else:
                # Normal satır - olduğu gibi ekle
                merged_lines.append(original_line.rstrip())
        
        return '\n'.join(merged_lines)
    
    def _create_header(self) -> str:
        """Dosya başına eklenecek header'ı oluşturur."""
        header_lines = []
        
        # "From the library of Archive.org."
        header_lines.append("From the library of Archive key.")
        
        # Kitap adı ve yazar
        if self.title and self.author:
            header_lines.append(f"{self.title} by {self.author}.")
        elif self.title:
            header_lines.append(f"{self.title}.")
        elif self.author:
            header_lines.append(f"by {self.author}.")
        
        return '\n'.join(header_lines)
    
    def _decode_html_entities(self, text: str) -> str:
        """HTML entity'lerini düzeltir."""
        # BeautifulSoup zaten decode ediyor ama yine de kontrol edelim
        import html
        text = html.unescape(text)
        
        # Yaygın karakter sorunlarını düzelt
        replacements = {
            'â€"': '—',  # em dash
            'â€"': '–',  # en dash
            'â€™': "'",  # right single quotation mark
            'â€œ': '"',  # left double quotation mark
            'â€': '"',  # right double quotation mark
            'â€¢': '•',  # bullet
            'â€¦': '...',  # ellipsis
        }
        for entity, char in replacements.items():
            text = text.replace(entity, char)
        return text
    
    def _clean_whitespace(self, text: str) -> str:
        """Fazla boşlukları temizler."""
        # Birden fazla boş satırı tek boş satıra indir
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        # Satır başındaki ve sonundaki boşlukları temizle
        lines = []
        for line in text.split('\n'):
            line = line.rstrip()
            if line or (lines and lines[-1]):  # Boş satırları koru ama fazlasını kaldır
                lines.append(line)
        
        return '\n'.join(lines)
    
    def _format_paragraphs(self, text: str) -> str:
        """Paragrafları düzenler."""
        lines = text.split('\n')
        formatted_lines = []
        
        for line in lines:
            line = line.strip()
            if not line:
                # Boş satır - paragraf sonu
                if formatted_lines and formatted_lines[-1]:
                    formatted_lines.append('')
                continue
            
            # Başlık kontrolü (büyük harfle başlayan ve kısa satırlar)
            if line.isupper() and len(line) < 100:
                if formatted_lines and formatted_lines[-1]:
                    formatted_lines.append('')
                formatted_lines.append(line)
                formatted_lines.append('')
            else:
                # Normal paragraf
                formatted_lines.append(line)
        
        return '\n'.join(formatted_lines).strip()
    
    def _generate_output_filename(self, input_path: Path) -> Path:
        """Kitap adından dosya adı oluşturur (boşluklar tire ile değiştirilir)."""
        # Önce metadata'dan title'ı al
        if self.title:
            # Title'dan dosya adı oluştur
            filename = self.title.strip()
            # Özel karakterleri temizle ve boşlukları tire ile değiştir
            filename = re.sub(r'[^\w\s-]', '', filename)  # Özel karakterleri kaldır
            filename = re.sub(r'\s+', '-', filename)  # Boşlukları tire ile değiştir
            filename = re.sub(r'-+', '-', filename)  # Birden fazla tireyi tek tire yap
            filename = filename.strip('-')  # Baştan ve sondan tireleri kaldır
            filename = filename.lower()  # Küçük harfe çevir
            output_path = input_path.parent / f"{filename}.txt"
        else:
            # Title bulunamadıysa, input dosya adını kullan
            filename = input_path.stem
            filename = re.sub(r'\s+', '-', filename)  # Boşlukları tire ile değiştir
            output_path = input_path.parent / f"{filename}.txt"
        
        return output_path
    
    def convert(self, input_path: Path, output_path: Optional[Path] = None) -> Path:
        """HTML dosyasını TXT'ye dönüştürür."""
        print(f"📖 HTML dosyası okunuyor: {input_path}")
        
        # HTML'i oku ve parse et
        html_content = self.read_html(input_path)
        self.parse_html(html_content)
        
        print("🧹 Header ve footer temizleniyor...")
        self.remove_header_footer()
        
        print("📝 Metin içeriği çıkarılıyor...")
        text_content = self.clean_text_content()
        
        # Çıktı dosyası yolu belirle
        if output_path is None:
            output_path = self._generate_output_filename(input_path)
        
        # TXT dosyasına yaz
        print(f"💾 TXT dosyasına yazılıyor: {output_path}")
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(text_content)
        
        print(f"✅ Dönüştürme tamamlandı!")
        print(f"   Girdi: {input_path} ({len(html_content):,} karakter)")
        print(f"   Çıktı: {output_path} ({len(text_content):,} karakter)")
        
        return output_path


def main():
    """Ana fonksiyon."""
    if len(sys.argv) < 2:
        print("Kullanım: python scripts/html_to_txt.py <input_html_file> [output_txt_file]")
        print("\nÖrnek:")
        print('  python scripts/html_to_txt.py "txt/Twenty Thousand Leagues under the Sea by Jules Verne.html"')
        sys.exit(1)
    
    input_path = Path(sys.argv[1])
    
    if not input_path.exists():
        print(f"❌ Dosya bulunamadı: {input_path}")
        sys.exit(1)
    
    if not input_path.suffix.lower() in ['.html', '.htm']:
        print(f"⚠️  Uyarı: Dosya HTML formatında görünmüyor: {input_path}")
    
    output_path = None
    if len(sys.argv) >= 3:
        output_path = Path(sys.argv[2])
    
    converter = HTMLToTXTConverter()
    converter.convert(input_path, output_path)


if __name__ == '__main__':
    main()

