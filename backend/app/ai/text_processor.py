import spacy
from typing import List
import sys
import re

from .text_normalizer import AdvancedTextNormalizer

class TextProcessor:
    def __init__(self):
        self.normalizer = AdvancedTextNormalizer()
        self.models = {}  # { 'en': nlp_model, 'tr': nlp_model }


    def _get_model(self, lang: str):
        """Dile göre Spacy modelini getir, yüklü değilse yükle."""
        model_name = "en_core_web_sm" if lang != "tr" else "tr_core_news_sm"
        
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
        
        # Bağlaç regex'i (öncesinde virgül olmayabilir)
        # and, but, or, nor, for, yet, so, because, which, that, who, when, where
        conjunctions = r'\s+(and|but|or|nor|for|yet|so|because|which|that|who|when|where)\s'
        
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
                    search_window = search_area[-min(len(search_area), 150):]
                    conj_matches = list(re.finditer(conjunctions, search_window))
                    
                    if conj_matches:
                        # En son eşleşmeyi al
                        last_match = conj_matches[-1]
                        # search_window içindeki pozisyonunu search_area'ya uyarla
                        window_offset = len(search_area) - len(search_window)
                        # Bağlacın BITTIĞI yerden böl (bağlaç mevcut chunk'ta kalsın)
                        # last_match.end() bağlaçtan sonraki boşluğu da içeriyor (\s... ile başlıyor ama \s ile bitmiyor regex)
                        # Regex: \s+(and|...)\s
                        split_index = window_offset + last_match.end()
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

    def split_into_chunks(self, text: str, max_chars: int = 650, min_chars: int = 80, language: str = "en", normalize: bool = True) -> List[str]:
        """
        Metni mantıklı chunk'lara böler, birden fazla cümleyi birleştirir.
        
        Optimized for XTTS v2 and multi-language:
        - Dinamik Spacy model yükleme
        - Geliştirilmiş normalizasyon
        """
        nlp = self._get_model(language)
            
        # Normalizasyon
        if normalize:
            text = self.normalizer.normalize(text, language)
            
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
