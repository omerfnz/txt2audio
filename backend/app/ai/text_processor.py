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
        # Tekrar eden noktalamalar (tek nokta hariç)
        chunk = re.sub(r'([!?,;:])\1+', r'\1', chunk)
        
        # Noktalama öncesi boşlukları sil ( , -> ,)
        chunk = re.sub(r'\s+([!?,;:])', r'\1', chunk)
        
        # Tırnak işaretlerini düzelt
        chunk = chunk.replace('"', '"').replace('"', '"').replace("'", "'").replace("'", "'")
        
        return chunk.strip()
    
    def _smart_split(self, text: str, max_chars: int) -> List[str]:
        """
        Uzun bir metni/cümleyi anlamlı yerlerden (noktalama, bağlaç) bölmeye çalışır.
        """
        if len(text) <= max_chars:
            return [text]
            
        chunks = []
        current_text = text
        
        # Bağlaç regex'i (Anlamlı bölme noktaları için)
        # and, but, or, nor, for, yet, so, because, which, that, who, when, where
        # although, though, while, unless, since, if (Edebi metinler için eklendi)
        conjunctions = r'\s+(and|but|or|nor|for|yet|so|because|which|that|who|when|where|although|though|while|unless|since|if)\s'
        
        while len(current_text) > max_chars:
            # Kesme noktası bul
            # Öncelik sırası: 
            # 1. Alt cümle bitişleri (;:)
            # 2. Virgüller (,)
            # 3. Bağlaçlar (and, but, which...)
            # 4. Boşluk ( )
            
            # Max limit içindeki son geçerli konumu bulmaya çalışacağız
            search_area = current_text[:max_chars]
            
            # Regex ile en uygun bölme noktasını ara (sondan başa doğru)
            split_index = -1
            
            # 1. Noktalı virgül veya iki nokta
            split_match = re.search(r'[;:]\s', search_area[::-1])
            if split_match:
                split_index = len(search_area) - split_match.end() + 1
            else:
                # 2. Virgül dene
                comma_match = re.search(r',\s', search_area[::-1])
                if comma_match:
                    split_index = len(search_area) - comma_match.end() + 1
                else:
                    # 3. Bağlaç dene (En azından cümlenin ortasında rastgele kesmeyelim)
                    # search_area üzerinde normal arama yapıp en sonuncuyu bulalım (reverse regex zor olabilir)
                    # Son 100 karakter içinde arayalım ki çok geriye gitmeyelim
                    window_offset = len(search_area) - min(len(search_area), 150)
                    search_window = search_area[window_offset:]
                    conj_matches = list(re.finditer(conjunctions, search_window))
                    
                    if conj_matches:
                        # En son eşleşmeyi al
                        last_match = conj_matches[-1]
                        # search_window içindeki pozisyonunu search_area'ya uyarla
                        # Bağlacın BAŞLADIĞI yerden böl (bağlaç yeni chunk'ta kalsın, daha doğal bir akış sağlar)
                        split_index = window_offset + last_match.start()
                    else:
                        # 4. Boşluk dene (mecburiyet)
                        space_match = re.search(r'\s', search_area[::-1])
                        if space_match:
                            split_index = len(search_area) - space_match.end()
            
            if split_index > 0:
                chunks.append(current_text[:split_index].strip())
                current_text = current_text[split_index:].strip()
            else:
                # Hiçbir bölme noktası bulamadık
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
                # Son parça hariç hepsini chunks'a ekle, son parçayı current_chunk yap (birleştirme şansı için)
                if sub_chunks:
                    chunks.extend([self.validate_chunk(sc) for sc in sub_chunks[:-1]])
                    current_chunk = sub_chunks[-1] # Son parça elde kalsın
                
            else:
                # Cümleyi mevcut chunk'a eklemeyi dene
                # Araya boşluk koy
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
            # Eğer son parça çok kısaysa ve önceki chunk varsa, birleştirmeyi dene (limit aşılsa bile son parça için esneme yapılabilir mi? Hayır, güvenli kalalım)
            # Ama min_chars kontrolü yapabiliriz
            chunks.append(self.validate_chunk(current_chunk))

        # Boş chunkları temizle
        chunks = [c for c in chunks if c]
        
        # Problematic chunk'ları tespit et ve daha küçük parçalara böl
        final_chunks = []
        for chunk in chunks:
            if self.is_chunk_problematic(chunk) and len(chunk) > 100:
                # Problematic chunk'ı yarıya böl
                print(f"⚠ Problematic chunk detected (len={len(chunk)}), splitting smaller...")
                smaller_max = max_chars // 2  # Yarı boyutta chunk'lar
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
        
        Args:
            text: Normalize edilmiş metin
            chapters: Tespit edilmiş chapter'lar
            max_chars: Maksimum chunk uzunluğu
            min_chars: Minimum chunk uzunluğu
            nlp: Spacy NLP model
            
        Returns:
            Chapter sınırlarına uygun chunk'lar
        """
        # Chapter pozisyonlarını sıralı set olarak sakla (hızlı lookup için)
        chapter_positions = sorted([ch.position for ch in chapters])
        
        # Metni cümlelere böl
        doc = nlp(text)
        sentences = [sent.text.strip() for sent in doc.sents if sent.text.strip()]
        
        if not sentences:
            return [""]
        
        chunks: List[str] = []
        current_chunk = ""
        current_text_pos = 0  # Normalize edilmiş metindeki mevcut pozisyon
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            
            # Cümlenin metindeki pozisyonunu bul
            sentence_start_pos = text.find(sentence, current_text_pos)
            if sentence_start_pos == -1:
                # Cümle bulunamadı, normal akışa devam et
                sentence_start_pos = current_text_pos
            
            # Bu cümle bir chapter başlangıcı mı kontrol et
            is_chapter_start = False
            for chapter_pos in chapter_positions:
                # Chapter pozisyonu bu cümlenin içinde veya hemen öncesinde mi?
                if chapter_pos >= sentence_start_pos and chapter_pos < sentence_start_pos + len(sentence):
                    is_chapter_start = True
                    # Eğer chapter pozisyonu cümlenin ortasında ise, cümleyi böl
                    if chapter_pos > sentence_start_pos:
                        # Cümleyi chapter pozisyonunda böl
                        before_chapter = sentence[:chapter_pos - sentence_start_pos].strip()
                        after_chapter = sentence[chapter_pos - sentence_start_pos:].strip()
                        
                        # Önceki chunk'ı kaydet (eğer varsa)
                        if current_chunk:
                            chunks.append(self.validate_chunk(current_chunk))
                            current_chunk = ""
                        
                        # Chapter öncesi kısmı ekle (eğer varsa)
                        if before_chapter:
                            chunks.append(self.validate_chunk(before_chapter))
                        
                        # Chapter sonrası kısmı yeni chunk olarak başlat
                        current_chunk = after_chapter
                        current_text_pos = chapter_pos + len(after_chapter)
                    else:
                        # Chapter cümlenin başında, mevcut chunk'ı kaydet ve yeni chunk başlat
                        if current_chunk:
                            chunks.append(self.validate_chunk(current_chunk))
                        current_chunk = sentence
                        current_text_pos = sentence_start_pos + len(sentence)
                    break
            
            if is_chapter_start:
                continue
            
            # Normal chunking mantığı
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
                
                current_text_pos = sentence_start_pos + len(sentence)
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
                
                current_text_pos = sentence_start_pos + len(sentence)
        
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
