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
    
    def remove_preface_and_intro(self, body):
        """Önsöz, başlık sayfası ve giriş bölümlerini kaldırır, sadece asıl hikayeyi bırakır."""
        # PREFACE, NOTE TO THE THIRD EDITION, INTRODUCTION gibi bölümleri bul ve kaldır
        intro_keywords = ['preface', 'introduction', 'note to the', 'foreword', 'prologue', 
                         'dedication', 'acknowledgment', 'acknowledgement']
        
        # Tüm h2 başlıklarını kontrol et
        headings_to_remove = []
        for heading in body.find_all(['h1', 'h2', 'h3']):
            text = heading.get_text(strip=True).lower()
            # Eğer başlık önsöz/intro gibi bir şeyse, işaretle
            # Ama "INTRODUCTORY TO" gibi başlıklar asıl hikaye başlangıcı olabilir, kontrol et
            if any(keyword in text for keyword in intro_keywords):
                # "INTRODUCTORY TO" gibi başlıklar asıl hikaye başlangıcı olabilir
                if 'introductory to' in text or 'the custom-house' in text:
                    # Bu asıl hikaye başlangıcı, atla
                    continue
                headings_to_remove.append(heading)
        
        # İşaretlenen başlıkları ve içeriklerini kaldır
        for heading in headings_to_remove:
            # Başlıktan sonraki tüm içeriği kaldır, ta ki CHAPTER I gibi bir şey bulana kadar
            current = heading.next_sibling
            while current:
                next_sibling = current.next_sibling
                
                # Eğer CHAPTER I, PART I, THE CUSTOM-HOUSE gibi bir şey bulursak, dur
                if hasattr(current, 'name'):
                    if current.name in ['h1', 'h2', 'h3', 'h4']:
                        text = current.get_text(strip=True).lower()
                        # CHAPTER I, PART I, THE CUSTOM-HOUSE gibi asıl hikaye başlangıcı
                        if (text.startswith('chapter') or text.startswith('part') or 
                            'the custom-house' in text or 
                            ('introductory to' in text and 'scarlet letter' in text)):
                            # Asıl hikaye başladı, dur
                            break
                    if current.name == 'div' and 'chapter' in current.get('class', []):
                        # Chapter div'i bulundu, dur
                        break
                
                # İçeriği kaldır
                if hasattr(current, 'decompose'):
                    current.decompose()
                
                current = next_sibling
            
            # Başlığı kaldır
            heading.decompose()
        
        # Başlık sayfası elementlerini kaldır (ilk birkaç paragraf)
        # Asıl hikayenin başladığı yeri bul (CHAPTER I, PART I, THE CUSTOM-HOUSE, vb.)
        first_chapter = None
        for heading in body.find_all(['h1', 'h2', 'h3', 'h4']):
            text = heading.get_text(strip=True).lower()
            # CHAPTER I, PART I, THE CUSTOM-HOUSE gibi asıl hikaye başlangıçları
            # "THE CUSTOM-HOUSE" veya "INTRODUCTORY TO" gibi başlıklar asıl hikaye başlangıcı olabilir
            if (text.startswith('chapter') or text.startswith('part') or 
                'the custom-house' in text or 
                ('introductory to' in text and 'scarlet letter' in text)):
                first_chapter = heading
                break
        
        if first_chapter:
            # CHAPTER I'den önceki tüm kardeş elementleri kaldır
            # Önce parent'ı bul
            parent = first_chapter.parent
            if parent:
                # Parent'ın tüm children'ını kontrol et
                for element in list(parent.children):
                    if element == first_chapter:
                        # CHAPTER I'ye ulaştık, dur
                        break
                    if hasattr(element, 'decompose'):
                        element.decompose()
            
            # Ayrıca, CHAPTER I'den önceki tüm div.chapter'ları da kontrol et
            # Eğer CHAPTER I bir div içindeyse, div'den önceki tüm elementleri kaldır
            chapter_div = first_chapter.find_parent('div', class_=re.compile(r'chapter', re.I))
            if not chapter_div:
                # CHAPTER I'nin kendisi bir div içinde olabilir
                chapter_div = first_chapter.find_parent('div')
            
            if chapter_div and chapter_div.parent:
                # Div'in parent'ındaki tüm kardeş elementleri kontrol et
                for element in list(chapter_div.parent.children):
                    if element == chapter_div:
                        break
                    if hasattr(element, 'decompose'):
                        element.decompose()
    
    def _process_title_page(self, body):
        """Başlık sayfasındaki (title page) öğeleri özel işler."""
        # Başlık sayfası genellikle ilk birkaç paragraf veya div içinde
        # <br> taglarını boşlukla değiştir ama title page içinde daha agresif birleştir
        title_page_elements = []
        
        # İlk 500 karakter içindeki tüm <br> taglarını bul (title page genellikle başta)
        for br in body.find_all('br'):
            # Eğer br'nin parent'ı title page gibi görünüyorsa (class="cb", "c" gibi)
            parent = br.parent
            if parent and parent.get('class'):
                classes = ' '.join(parent.get('class', []))
                if any(cls in classes.lower() for cls in ['cb', 'c', 'center', 'title']):
                    br.replace_with(' ')
                else:
                    br.replace_with(' ')
            else:
                br.replace_with(' ')
        
        # Parantez içindeki içeriği birleştir
        for p in body.find_all('p', class_=re.compile(r'c', re.I)):
            # Parantez başlangıcı ve bitişi aynı paragrafta olmalı
            text = p.get_text(separator=' ', strip=True)
            if text.startswith('(') and not text.endswith(')'):
                # Parantez açılmış ama kapanmamış, sonraki elemanla birleştir
                next_elem = p.next_sibling
                if next_elem and hasattr(next_elem, 'get_text'):
                    next_text = next_elem.get_text(strip=True)
                    if next_text.endswith(')'):
                        # Birleştir
                        p_text = p.get_text(separator=' ', strip=True)
                        next_elem_text = next_elem.get_text(separator=' ', strip=True)
                        # İçeriği birleştir
                        combined = p_text + ' ' + next_elem_text
                        p.string = combined
                        next_elem.decompose()
    
    def clean_text_content(self) -> str:
        """Temiz metin içeriğini çıkarır."""
        # Contents'i kaldır
        self.remove_contents()
        
        # Body içeriğini al
        body = self.soup.find('body')
        if not body:
            body = self.soup
        
        # Önsöz ve başlık sayfasını kaldır, sadece asıl hikayeyi bırak
        self.remove_preface_and_intro(body)
        
        # Başlık sayfasını özel işle (eğer kaldırılmadıysa)
        self._process_title_page(body)
        
        # Poem/şiir içeriğini özel işle (br taglarını boşlukla değiştir)
        for poem in body.find_all(['p', 'div'], class_=re.compile(r'poem', re.I)):
            for br in poem.find_all('br'):
                br.replace_with(' ')
        
        # Kalan <br> taglarını boşlukla değiştir
        for br in body.find_all('br'):
            br.replace_with(' ')
        
        # Small taglarını kaldır ama içeriğini koru (unwrap) - önce small'ları işle
        # Small tagları genellikle harfler arasında boşluk oluşturur, bu yüzden boşluksuz birleştir
        for tag in body.find_all('small'):
            # İçeriği al ve birleştir (boşluk olmadan)
            inner_text = tag.get_text(separator='', strip=True)
            if inner_text:
                # Eğer tag'ın parent'ı varsa ve parent'ın içeriği varsa, birleştir
                parent = tag.parent
                if parent and parent.name not in ['script', 'style']:
                    # Small tag'ını içeriğiyle değiştir (boşluk olmadan)
                    tag.replace_with(inner_text)
                else:
                    tag.string = inner_text
                    tag.unwrap()
            else:
                tag.decompose()
        
        # Italik ve bold taglarını kaldır ama içeriğini koru (unwrap)
        # Önce içerikleri birleştir, sonra unwrap et
        for tag in body.find_all(['i', 'b', 'em', 'strong']):
            # İçeriği al ve birleştir
            inner_text = tag.get_text(separator=' ', strip=True)
            if inner_text:
                tag.string = inner_text
            tag.unwrap()
        
        # Metni satır satır çıkar (paragrafları koru)
        text = body.get_text(separator='\n', strip=False)
        
        # HTML entity'lerini düzelt
        text = self._decode_html_entities(text)
        
        # Ellipsis formatını düzelt (. . . -> ...)
        text = re.sub(r'\.\s+\.\s+\.', '...', text)
        text = re.sub(r'\.\s+\.\s+\.', '...', text)  # Tekrar kontrol et
        
        # Tek kelimelik satırları birleştir (ama paragraf yapısını koru)
        text = self._merge_single_word_lines(text)
        
        # Parantez birleştirme (başlık sayfası formatlamasından önce)
        text = self._fix_parentheses(text)
        
        # Başlık sayfası için özel işlem (ilk 200 satır)
        text = self._fix_title_page_formatting(text)
        
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
            
            # Tek kelimelik satır kontrolü (40 karakterden kısa ve tek kelime)
            words = line.split()
            is_single_word = len(words) == 1 and len(line) < 40
            
            # Özel durumlar: noktalama ile biten kısa satırlar (örn: "lat.", "long.")
            if is_single_word and line.endswith(('.', ',', ';', ':', '!', '?', '"', "'")):
                is_single_word = True
            
            # İki kelimelik kısa satırlar da birleştir (örn: "Nature dated" -> "Nature dated")
            if not is_single_word and len(words) == 2 and len(line) < 50:
                # Eğer ikinci kelime küçük harfle başlıyorsa veya noktalama ise, birleştir
                if words[1] and (words[1][0].islower() or words[1] in [',', '.', ';', ':', '!', '?']):
                    is_single_word = True
            
            # Tek kelimelik satırları birleştir
            if is_single_word:
                # Önceki satırla birleştir
                if merged_lines and merged_lines[-1] and merged_lines[-1].strip():
                    # Önceki satırın sonuna ekle
                    prev_line = merged_lines[-1].rstrip()
                    # Eğer önceki satır "of", "in", "the" gibi kelimelerle bitiyorsa birleştir
                    if prev_line and not prev_line[-1] in ['.', ',', ';', ':', '!', '?', '"', "'", '—', '–', '(', '[', '{']:
                        # Önceki satır "of", "in", "the", "in the" gibi kelimelerle bitiyorsa birleştir
                        prev_words = prev_line.split()
                        if prev_words and prev_words[-1].lower() in ['of', 'in', 'the', 'a', 'an', 'to', 'for', 'with', 'by']:
                            merged_lines[-1] = prev_line + ' ' + line
                        elif line[0].isupper() and prev_line[-1].islower():
                            # Büyük harfle başlayan kelime, küçük harfle biten satırdan sonra geliyorsa birleştir
                            merged_lines[-1] = prev_line + ' ' + line
                        else:
                            merged_lines[-1] = prev_line + ' ' + line
                    else:
                        merged_lines[-1] = prev_line + line
                else:
                    # Önceki satır boşsa ama sonraki satır küçük harfle başlıyorsa, birleştir
                    if i + 1 < len(lines):
                        next_line = lines[i + 1].strip()
                        if next_line and next_line[0].islower():
                            # Sonraki satırla birleştir (geçici olarak ekle, sonra işle)
                            merged_lines.append(line)
                        else:
                            merged_lines.append(line)
                    else:
                        merged_lines.append(line)
            else:
                # Normal satır - olduğu gibi ekle
                merged_lines.append(original_line.rstrip())
        
        # İkinci geçiş: Kalan tek kelimelik satırları birleştir (boş satırları atlayarak)
        final_lines = []
        for i, line in enumerate(merged_lines):
            line = line.strip()
            if not line:
                final_lines.append('')
                continue
            
            words = line.split()
            is_single_word = len(words) == 1 and len(line) < 50
            
            # Virgül veya noktalama ile başlayan satırları birleştir
            if line.startswith((',', '.', ';', ':', '!', '?', '"', "'")):
                # Boş satırları atla, gerçek önceki satırı bul
                prev_idx = len(final_lines) - 1
                while prev_idx >= 0 and (not final_lines[prev_idx] or not final_lines[prev_idx].strip()):
                    prev_idx -= 1
                if prev_idx >= 0 and final_lines[prev_idx] and final_lines[prev_idx].strip():
                    prev_line = final_lines[prev_idx].rstrip()
                    # Virgülü birleştir (boşluk olmadan)
                    final_lines[prev_idx] = prev_line + line.lstrip()
                    # Aradaki boş satırları kaldır
                    final_lines = final_lines[:prev_idx+1]
                else:
                    final_lines.append(line)
                continue
            
            if is_single_word:
                # Boş satırları atla, gerçek önceki satırı bul
                prev_idx = len(final_lines) - 1
                while prev_idx >= 0 and (not final_lines[prev_idx] or not final_lines[prev_idx].strip()):
                    prev_idx -= 1
                
                if prev_idx >= 0 and final_lines[prev_idx] and final_lines[prev_idx].strip():
                    prev_line = final_lines[prev_idx].rstrip()
                    prev_words = prev_line.split()
                    should_merge = False
                    
                    # Önceki satır "of", "in", "the", "in the issue of" gibi ifadelerle bitiyorsa birleştir
                    if prev_words:
                        last_word = prev_words[-1].lower()
                        if last_word in ['of', 'in', 'the', 'a', 'an', 'to', 'for', 'with', 'by', 'at', 'on', 'from']:
                            should_merge = True
                        # Önceki satır "issue of", "note in the" gibi ifadelerle bitiyorsa birleştir
                        elif len(prev_words) >= 2 and prev_words[-2].lower() in ['of', 'in', 'the']:
                            should_merge = True
                        # Önceki satır noktalama ile bitmiyorsa ve küçük harfle bitiyorsa birleştir
                        elif prev_line[-1].islower() and prev_line[-1] not in ['.', '!', '?', ':', ';', '—', '–']:
                            should_merge = True
                    
                    if should_merge:
                        # Aradaki boş satırları kaldır ve birleştir
                        final_lines = final_lines[:prev_idx+1]
                        final_lines[-1] = prev_line + ' ' + line
                    else:
                        final_lines.append(line)
                else:
                    final_lines.append(line)
            else:
                final_lines.append(line)
        
        # Üçüncü geçiş: Virgül ve noktalama işaretlerini düzelt
        cleaned_lines = []
        for line in final_lines:
            line = line.strip()
            if not line:
                cleaned_lines.append('')
                continue
            
            # Satır yalnız virgül/noktalama ise birleştir
            if line in [',', '.', ';', ':', '!', '?', '"', "'"]:
                if cleaned_lines and cleaned_lines[-1] and cleaned_lines[-1].strip():
                    cleaned_lines[-1] = cleaned_lines[-1].rstrip() + line
                else:
                    cleaned_lines.append(line)
            # Satır virgül/noktalama ile başlıyorsa birleştir
            elif line.startswith((',', '.', ';', ':', '!', '?', '"', "'")):
                if cleaned_lines and cleaned_lines[-1] and cleaned_lines[-1].strip():
                    cleaned_lines[-1] = cleaned_lines[-1].rstrip() + line
                else:
                    cleaned_lines.append(line)
            # Satır virgül/noktalama ile bitiyorsa ve önceki satırla birleştirilebilirse birleştir
            elif line.endswith((',', '.', ';', ':', '!', '?', '"', "'")) and len(line) < 30:
                # Tek kelimelik satırlar için önceki satırla birleştir
                if cleaned_lines and cleaned_lines[-1] and cleaned_lines[-1].strip():
                    prev_line = cleaned_lines[-1].rstrip()
                    # Önceki satır noktalama ile bitmiyorsa birleştir
                    if prev_line[-1] not in ['.', '!', '?', ':', ';', '—', '–']:
                        cleaned_lines[-1] = prev_line + ' ' + line
                    else:
                        cleaned_lines.append(line)
                else:
                    cleaned_lines.append(line)
            else:
                cleaned_lines.append(line)
        
        return '\n'.join(cleaned_lines)
    
    def _fix_parentheses(self, text: str) -> str:
        """Parantez içindeki içeriği birleştirir."""
        lines = text.split('\n')
        fixed_lines = []
        
        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                fixed_lines.append('')
                continue
            
            # Parantez başlangıcı kontrolü
            if line == '(':
                # Önceki satırla birleştir (boşluk olmadan)
                if fixed_lines and fixed_lines[-1] and fixed_lines[-1].strip():
                    fixed_lines[-1] = fixed_lines[-1].rstrip() + '('
                else:
                    fixed_lines.append('(')
                continue
            
            # Parantez içindeki içerik kontrolü (örn: "Kept in phonograph)")
            if line.startswith('Kept in') and line.endswith(')'):
                # Önceki satır parantez açılışı ise birleştir
                prev_idx = len(fixed_lines) - 1
                while prev_idx >= 0 and (not fixed_lines[prev_idx] or not fixed_lines[prev_idx].strip()):
                    prev_idx -= 1
                
                if prev_idx >= 0 and fixed_lines[prev_idx] and fixed_lines[prev_idx].strip().endswith('('):
                    prev_text = fixed_lines[prev_idx].rstrip()
                    # Parantez açılışından sonra boşluk ekle
                    fixed_lines[prev_idx] = prev_text + ' ' + line
                    fixed_lines = fixed_lines[:prev_idx+1]
                else:
                    fixed_lines.append(line)
                continue
            
            fixed_lines.append(line)
        
        # Fazla boşlukları temizle (örn: "( Kept" -> "(Kept")
        result = '\n'.join(fixed_lines)
        result = re.sub(r'\(\s+', '(', result)  # Parantez açılışından sonraki fazla boşlukları kaldır
        
        return result
    
    def _fix_title_page_formatting(self, text: str) -> str:
        """Başlık sayfasındaki format sorunlarını düzeltir (ilk 200 satır)."""
        lines = text.split('\n')
        fixed_lines = []
        
        # İlk 200 satırı işle (başlık sayfası genellikle burada)
        for i, line in enumerate(lines[:200]):
            line = line.strip()
            if not line:
                fixed_lines.append('')
                continue
            
            words = line.split()
            is_single_word = len(words) == 1 and len(line) < 50
            
            # Parantez başlangıcı kontrolü
            if line == '(':
                # Önceki satırla birleştir (boşluk olmadan)
                if fixed_lines and fixed_lines[-1] and fixed_lines[-1].strip():
                    fixed_lines[-1] = fixed_lines[-1].rstrip() + '('
                else:
                    fixed_lines.append('(')
                continue
            
            # Parantez içindeki içerik kontrolü (örn: "Kept in phonograph)")
            if line.startswith('Kept in') and line.endswith(')'):
                # Önceki satır parantez açılışı ise birleştir
                prev_idx = len(fixed_lines) - 1
                while prev_idx >= 0 and (not fixed_lines[prev_idx] or not fixed_lines[prev_idx].strip()):
                    prev_idx -= 1
                
                if prev_idx >= 0 and fixed_lines[prev_idx] and fixed_lines[prev_idx].strip().endswith('('):
                    fixed_lines[prev_idx] = fixed_lines[prev_idx].rstrip() + ' ' + line
                    fixed_lines = fixed_lines[:prev_idx+1]
                else:
                    fixed_lines.append(line)
                continue
            
            # Tek kelimelik satırları birleştir (başlık sayfasında daha agresif)
            if is_single_word:
                # Önceki satırla birleştir (boş satırları atla)
                prev_idx = len(fixed_lines) - 1
                while prev_idx >= 0 and (not fixed_lines[prev_idx] or not fixed_lines[prev_idx].strip()):
                    prev_idx -= 1
                
                if prev_idx >= 0 and fixed_lines[prev_idx] and fixed_lines[prev_idx].strip():
                    prev_line = fixed_lines[prev_idx].rstrip()
                    # Başlık sayfasında neredeyse her zaman birleştir (sadece cümle sonu değilse)
                    if prev_line and not prev_line[-1] in ['.', '!', '?']:
                        fixed_lines[prev_idx] = prev_line + ' ' + line
                        # Aradaki boş satırları kaldır
                        fixed_lines = fixed_lines[:prev_idx+1]
                    else:
                        fixed_lines.append(line)
                else:
                    fixed_lines.append(line)
            # İki kelimelik kısa satırlar (örn: "P. M.,")
            elif len(words) == 2 and len(line) < 30:
                # Önceki satırla birleştir (boş satırları atla)
                prev_idx = len(fixed_lines) - 1
                while prev_idx >= 0 and (not fixed_lines[prev_idx] or not fixed_lines[prev_idx].strip()):
                    prev_idx -= 1
                
                if prev_idx >= 0 and fixed_lines[prev_idx] and fixed_lines[prev_idx].strip():
                    prev_line = fixed_lines[prev_idx].rstrip()
                    # Eğer önceki satır sayı veya saat ile bitiyorsa birleştir
                    if prev_line and (prev_line[-1].isdigit() or prev_line.endswith(':')):
                        fixed_lines[prev_idx] = prev_line + ' ' + line
                        fixed_lines = fixed_lines[:prev_idx+1]
                    else:
                        fixed_lines.append(line)
                else:
                    fixed_lines.append(line)
            else:
                fixed_lines.append(line)
        
        # Kalan satırları ekle
        fixed_lines.extend(lines[200:])
        return '\n'.join(fixed_lines)
    
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

