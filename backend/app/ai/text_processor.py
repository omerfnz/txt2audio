import spacy
from typing import List, Optional
import sys
import re

from .text_normalizer import AdvancedTextNormalizer
from .chapter_detector import ChapterDetector, ChapterInfo

class TextProcessor:
    def __init__(self):
        self.normalizer = AdvancedTextNormalizer()
        self.models = {}  # { 'en': nlp_model, 'tr': nlp_model }
        self.chapter_detector = ChapterDetector()


    def _get_model(self):
        """Spacy İngilizce modelini getir, yüklü değilse yükle."""
        model_name = "en_core_web_sm"
        
        if model_name in self.models:
            return self.models[model_name]

        try:
            nlp = spacy.load(model_name)
            self.models[model_name] = nlp
            print(f"✓ Model loaded: {model_name}")
            return nlp
        except OSError:
            print(f"⚠ Model {model_name} not found. Attempting download...")
            try:
                from spacy.cli import download
                download(model_name)
                nlp = spacy.load(model_name)
                self.models[model_name] = nlp
                print(f"✓ Model downloaded and loaded: {model_name}")
                return nlp
            except Exception as download_error:
                print(f"✗ Model download failed: {download_error}")
                raise RuntimeError(
                    f"Failed to load Spacy model {model_name}."
                ) from download_error


    def is_chunk_problematic(self, chunk: str) -> bool:
        """
        Sorunlu chunk'ları tespit et (XTTS için optimize edilmiş).
        Bu chunk'lar daha küçük parçalara bölünmelidir.
        """
        if not chunk or len(chunk) < 10:
            return False
        
        # 1. Çok fazla sayı içeren chunk'lar (XTTS sayılarda zorlanır)
        digit_count = sum(c.isdigit() for c in chunk)
        digit_ratio = digit_count / len(chunk)
        if digit_ratio > 0.4:  # %40'tan fazla rakam (esnetildi: %30 -> %40)
            return True
        
        # 2. Çok fazla büyük harf (ALL CAPS metinler)
        upper_count = sum(c.isupper() for c in chunk if c.isalpha())
        alpha_count = sum(c.isalpha() for c in chunk)
        if alpha_count > 20 and upper_count / max(alpha_count, 1) > 0.8:  # %80'den fazla büyük (esnetildi)
            return True
        
        # 3. Çok fazla özel karakter
        special_chars = sum(1 for c in chunk if not c.isalnum() and c not in ' .,!?;:-\'"')
        special_ratio = special_chars / len(chunk)
        if special_ratio > 0.3:  # %30'dan fazla özel karakter (esnetildi)
            return True
        
        # 4. Çok uzun kelimeler (okunamayan terimler olabilir)
        words = chunk.split()
        if any(len(word) > 25 for word in words):  # 25+ karakter kelime
            return True
        
        return False
    
    def validate_chunk(self, chunk: str) -> str:
        """
        Chunk'ı temizler.
        Eskiden nokta ekliyordu, artık eklemiyor çünkü cümle ortasında bölünmüş olabilir.
        F5-TTS ve XTTS noktasız metinleri de işleyebilir.
        """
        # "dext" ve benzeri halüsinasyonları önlemek için ekstra temizlik
        # Tekrar eden noktalama (tek nokta hariç)
        chunk = re.sub(r'([!?,;:])\1+', r'\1', chunk)
        
        # Noktalama öncesi boşlukları sil ( , -> ,)
        chunk = re.sub(r'\s+([!?,;:])', r'\1', chunk)
        
        # Tırnak işaretlerini düzelt
        chunk = chunk.replace('"', '"').replace('"', '"').replace("'", "'").replace("'", "'")
        
        return chunk.strip()
    
    def _smart_split(self, text: str, max_chars: int) -> List[str]:
        """
        Uzun bir metni/cümleyi SADECE noktalama işaretlerinde böler.
        Kelime sınırlarında değil, sadece noktalama işaretlerinde böl.
        """
        if len(text) <= max_chars:
            return [text]
            
        chunks = []
        current_text = text
        
        while len(current_text) > max_chars:
            # Max limit içindeki son noktalama işaretini bul
            search_area = current_text[:max_chars]
            
            # Öncelik sırası: Noktalama işaretleri (sondan başa doğru)
            # 1. Cümle bitişleri: . ! ? (nokta, ünlem, soru işareti)
            # 2. Alt cümle bitişleri: ; : (noktalı virgül, iki nokta)
            # 3. Virgül: ,
            # 4. Hiçbiri yoksa: Mecbur kelime sınırında böl (ama bu çok nadir olmalı)
            
            split_index = -1
            
            # 1. Cümle bitişleri: . ! ? (en öncelikli)
            # Sondan başa doğru arama yapıyoruz - rfind kullanarak
            last_period = search_area.rfind('. ')
            last_exclamation = search_area.rfind('! ')
            last_question = search_area.rfind('? ')
            
            # En son noktalama işaretini bul
            sentence_end_pos = max(last_period, last_exclamation, last_question)
            
            if sentence_end_pos > max_chars * 0.5:  # En azından yarısından sonra böl
                # Noktalama işaretinden SONRA böl (noktalama ilk chunk'ta kalsın)
                split_index = sentence_end_pos + 2  # +2 for ". " or "! " or "? "
            else:
                # 2. Alt cümle bitişleri: ; :
                last_semicolon = search_area.rfind('; ')
                last_colon = search_area.rfind(': ')
                semicolon_pos = max(last_semicolon, last_colon)
                
                if semicolon_pos > max_chars * 0.5:
                    split_index = semicolon_pos + 2  # +2 for "; " or ": "
                else:
                    # 3. Virgül: ,
                    last_comma = search_area.rfind(', ')
                    if last_comma > max_chars * 0.5:
                        split_index = last_comma + 2  # +2 for ", "
                    else:
                        split_index = -1
            
            if split_index > 0:
                chunks.append(current_text[:split_index].strip())
                current_text = current_text[split_index:].strip()
            else:
                # Hiçbir noktalama işareti bulamadık - mecbur kelime sınırında böl
                # Son boşluğu bul (kelime ortasından bölmemek için)
                last_space = search_area.rfind(' ')
                if last_space > max_chars * 0.5:  # En azından yarısından sonra böl
                    split_index = last_space
                    chunks.append(current_text[:split_index].strip())
                    current_text = current_text[split_index:].strip()
                else:
                    # Gerçekten hiç boşluk yok (çok uzun kelime), mecbur böl
                    chunks.append(current_text[:max_chars].strip())
                    current_text = current_text[max_chars:].strip()
                
        if current_text:
            chunks.append(current_text)
            
        return chunks

    def split_into_chunks(
        self, 
        text: str, 
        max_chars: int = 650, 
        min_chars: int = 80, 
        language: str = "en", 
        normalize: bool = True,
        chapters: Optional[List[ChapterInfo]] = None
    ) -> List[str]:
        """
        Metni mantıklı chunk'lara böler, birden fazla cümleyi birleştirir.
        
        Optimized for XTTS v2:
        - İngilizce NLP model kullanımı
        - Geliştirilmiş normalizasyon
        - Chapter-aware chunking (chapter başlangıçları chunk başlangıcı olur)
        
        Args:
            text: Metin içeriği
            max_chars: Maksimum chunk uzunluğu
            min_chars: Minimum chunk uzunluğu
            language: Dil kodu
            normalize: Normalizasyon yapılsın mı
            chapters: Tespit edilmiş chapter'lar (None ise otomatik tespit edilir)
        """
        # Chapter'ları tespit et (eğer verilmemişse)
        if chapters is None:
            chapters = self.detect_chapters(text)
        
        nlp = self._get_model()
            
        # Normalizasyon
        if normalize:
            text = self.normalizer.normalize(text, lang="en")
            # Normalizasyon sonrası chapter pozisyonlarını yeniden hesapla
            # (normalizasyon metin uzunluğunu değiştirebilir)
            if chapters:
                chapters = self._recalculate_chapter_positions(chapters, text)
            
        # Chapter-aware chunking
        if chapters:
            return self._split_with_chapter_boundaries(text, chapters, max_chars, min_chars, nlp)
        
        # Normal chunking (chapter yoksa)
        return self._normal_chunking(text, max_chars, min_chars, nlp)
    
    def _normal_chunking(
        self,
        text: str,
        max_chars: int,
        min_chars: int,
        nlp
    ) -> List[str]:
        """
        Normal chunking (chapter-aware değil).
        Helper method for _split_with_chapter_boundaries.
        """
        doc = nlp(text)
        sentences = [sent.text.strip() for sent in doc.sents if sent.text.strip()]
        
        if not sentences:
            return [""]
        
        chunks: List[str] = []
        current_chunk = ""
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            
            # Eğer tek bir cümle limitin üzerindeyse, akıllı bölme yap
            if len(sentence) > max_chars:
                # Önce eldeki chunk'ı kaydet
                if current_chunk:
                    chunks.append(self.validate_chunk(current_chunk))
                    current_chunk = ""
                
                # Cümleyi alt parçalara böl
                sub_chunks = self._smart_split(sentence, max_chars)
                
                # Alt parçaları ekle
                if sub_chunks:
                    chunks.extend([self.validate_chunk(sc) for sc in sub_chunks[:-1]])
                    current_chunk = sub_chunks[-1]
            else:
                # Cümleyi mevcut chunk'a eklemeyi dene
                separator = " " if current_chunk else ""
                potential_chunk = current_chunk + separator + sentence
                
                if len(potential_chunk) <= max_chars:
                    current_chunk = potential_chunk
                else:
                    # Sığmıyor, mevcut chunk'ı kaydet
                    if current_chunk:
                        chunks.append(self.validate_chunk(current_chunk))
                    current_chunk = sentence
        
        # Kalan son parçayı ekle
        if current_chunk:
            chunks.append(self.validate_chunk(current_chunk))
        
        # Boş chunkları temizle
        chunks = [c for c in chunks if c]
        
        # Problematic chunk'ları tespit et ve daha küçük parçalara böl
        final_chunks = []
        for chunk in chunks:
            if self.is_chunk_problematic(chunk) and len(chunk) > 100:
                print(f"⚠ Problematic chunk detected (len={len(chunk)}), splitting smaller...")
                smaller_max = max_chars // 2
                sub_chunks = self._smart_split(chunk, smaller_max)
                final_chunks.extend([self.validate_chunk(sc) for sc in sub_chunks])
            else:
                final_chunks.append(chunk)
        
        return final_chunks if final_chunks else [""]
    
    def _recalculate_chapter_positions(
        self, 
        chapters: List[ChapterInfo], 
        normalized_text: str
    ) -> List[ChapterInfo]:
        """
        Normalizasyon sonrası chapter pozisyonlarını yeniden hesapla.
        
        Normalizasyon metin uzunluğunu değiştirebileceği için, normalize edilmiş
        metinde chapter'ları yeniden tespit eder.
        
        Args:
            chapters: Orijinal metinde tespit edilmiş chapter'lar
            normalized_text: Normalize edilmiş metin
            
        Returns:
            Normalize edilmiş metinde tespit edilmiş chapter'lar
        """
        # Normalize edilmiş metinde chapter'ları yeniden tespit et
        # (normalizasyon "II." -> "Chapter Two" gibi değişiklikler yapıyor)
        return self.detect_chapters(normalized_text)
    
    def _split_with_chapter_boundaries(
        self,
        text: str,
        chapters: List[ChapterInfo],
        max_chars: int,
        min_chars: int,
        nlp
    ) -> List[str]:
        """
        Chapter-aware chunking: Chapter başlangıçlarını chunk başlangıcı olarak zorla.
        
        Metni chapter pozisyonlarına göre böler, her bölümü ayrı ayrı chunk'lara böler.
        Bu şekilde chapter başlıkları her zaman chunk başlangıcında olur.
        
        Args:
            text: Normalize edilmiş metin
            chapters: Tespit edilmiş chapter'lar (pozisyonlar normalize edilmiş metindeki)
            max_chars: Maksimum chunk uzunluğu
            min_chars: Minimum chunk uzunluğu
            nlp: Spacy NLP model
            
        Returns:
            Chapter sınırlarına uygun chunk'lar
        """
        if not chapters:
            # Chapter yoksa normal chunking yap
            return self._normal_chunking(text, max_chars, min_chars, nlp)
        
        # Chapter pozisyonlarını sırala
        chapter_positions = sorted(set([ch.position for ch in chapters]))
        
        all_chunks: List[str] = []
        last_pos = 0
        
        # Metni chapter pozisyonlarına göre böl
        for chapter_pos in chapter_positions:
            # Chapter'dan önceki bölümü işle
            if chapter_pos > last_pos:
                section_text = text[last_pos:chapter_pos].strip()
                if section_text:
                    # Bu bölümü normal chunking ile işle
                    section_chunks = self._normal_chunking(section_text, max_chars, min_chars, nlp)
                    all_chunks.extend(section_chunks)
            
            # Bu chapter'dan sonraki chapter'a kadar olan bölümü bul
            next_chapter_pos = None
            for ch in chapters:
                if ch.position > chapter_pos:
                    next_chapter_pos = ch.position
                    break
            
            if next_chapter_pos:
                chapter_section = text[chapter_pos:next_chapter_pos].strip()
            else:
                chapter_section = text[chapter_pos:].strip()
            
            if chapter_section:
                # Chapter başlığını bul (ilk satır veya ilk cümle)
                lines = chapter_section.split('\n', 1)
                if len(lines) > 1:
                    chapter_title = lines[0].strip()
                    chapter_content = lines[1].strip()
                else:
                    # Cümle bazlı bul - ama chapter başlığı genellikle kısa olur
                    # "Chapter One", "Chapter Two" gibi - bunları ayırt et
                    doc = nlp(chapter_section)
                    sentences = [sent.text.strip() for sent in doc.sents if sent.text.strip()]
                    if sentences:
                        first_sentence = sentences[0]
                        # Eğer ilk cümle "Chapter X" formatındaysa, sadece o kadar al
                        # Aksi halde ilk cümleyi al
                        if re.match(r'^Chapter\s+(One|Two|Three|Four|Five|Six|Seven|Eight|Nine|Ten|\d+)[.!?]?\s*$', first_sentence, re.IGNORECASE):
                            chapter_title = first_sentence
                            chapter_content = ' '.join(sentences[1:]) if len(sentences) > 1 else ""
                        else:
                            # İlk cümle chapter başlığı değil, muhtemelen içerikle birleşmiş
                            # "Chapter X" kısmını bul
                            chapter_match = re.search(r'^(Chapter\s+(?:One|Two|Three|Four|Five|Six|Seven|Eight|Nine|Ten|\d+))[.!?]?\s+', first_sentence, re.IGNORECASE)
                            if chapter_match:
                                chapter_title = chapter_match.group(1)
                                chapter_content = first_sentence[len(chapter_match.group(0)):].strip()
                                if len(sentences) > 1:
                                    chapter_content += ' ' + ' '.join(sentences[1:])
                            else:
                                chapter_title = first_sentence
                                chapter_content = ' '.join(sentences[1:]) if len(sentences) > 1 else ""
                    else:
                        # Fallback: ilk 100 karakter
                        chapter_title = chapter_section[:100].strip()
                        chapter_content = chapter_section[100:].strip()
                
                # İlk chunk: chapter başlığı (veya başlık + biraz içerik)
                if chapter_title:
                    # Chapter başlığının sonuna nokta ekle (eğer yoksa)
                    # Bu TTS'in nefes alması için bir duraklama sağlar
                    if not chapter_title.rstrip().endswith(('.', '!', '?', ':', ';')):
                        chapter_title = chapter_title.rstrip() + "."
                    
                    # Chapter başlığını ayrı bir chunk olarak ekle (içerikle birleştirme)
                    all_chunks.append(self.validate_chunk(chapter_title))
                    
                    # Kalan içeriği normal chunking ile işle
                    if chapter_content:
                        content_chunks = self._normal_chunking(chapter_content, max_chars, min_chars, nlp)
                        all_chunks.extend(content_chunks)
                else:
                    # Başlık bulunamadı, tüm bölümü normal chunking ile işle
                    section_chunks = self._normal_chunking(chapter_section, max_chars, min_chars, nlp)
                    all_chunks.extend(section_chunks)
            
            last_pos = next_chapter_pos if next_chapter_pos else len(text)
        
        # Son kalan metni işle
        if last_pos < len(text):
            remaining_text = text[last_pos:].strip()
            if remaining_text:
                remaining_chunks = self._normal_chunking(remaining_text, max_chars, min_chars, nlp)
                all_chunks.extend(remaining_chunks)
        
        # Boş chunkları temizle
        all_chunks = [c for c in all_chunks if c]
        
        # Problematic chunk'ları kontrol et
        final_chunks = []
        for chunk in all_chunks:
            if self.is_chunk_problematic(chunk) and len(chunk) > 100:
                print(f"⚠ Problematic chunk detected (len={len(chunk)}), splitting smaller...")
                smaller_max = max_chars // 2
                sub_chunks = self._smart_split(chunk, smaller_max)
                final_chunks.extend([self.validate_chunk(sc) for sc in sub_chunks])
            else:
                final_chunks.append(chunk)
        
        return final_chunks if final_chunks else [""]
    
    def detect_chapters(self, text: str) -> List[ChapterInfo]:
        """
        Detect chapters in text before processing.
        
        This should be called before split_into_chunks to identify
        chapter boundaries.
        
        Args:
            text: Raw text content (before normalization)
            
        Returns:
            List of detected chapters
        """
        return self.chapter_detector.detect_chapters(text)

if __name__ == "__main__":
    try:
        processor = TextProcessor()
        sample_text = "This is a test sentence. " * 5 + "Here is a very long sentence that definitely needs to be split because it goes on and on and on, perhaps with a comma here, and another clause there, just to make sure it exceeds the limit effectively."
        chunks = processor.split_into_chunks(sample_text, max_chars=100)
        print(f"\nTotal chunks: {len(chunks)}")
        for i, chunk in enumerate(chunks):
            print(f"{i+1}: [{chunk}] (Len: {len(chunk)})")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
