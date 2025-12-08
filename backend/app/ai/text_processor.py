import spacy
from typing import List
import sys
import re

from .text_normalizer import AdvancedTextNormalizer

class TextProcessor:
    def __init__(self, model_name="en_core_web_sm"):
        self.nlp = None
        self.normalizer = AdvancedTextNormalizer()
        self._load_model(model_name)

    def _load_model(self, model_name: str):
        """Model yükle, başarısız olursa fallback kullan"""
        try:
            self.nlp = spacy.load(model_name)
            print(f"✓ Model loaded: {model_name}")
        except OSError:
            print(f"⚠ Model {model_name} not found. Attempting download...")
            try:
                from spacy.cli import download
                download(model_name)
                self.nlp = spacy.load(model_name)
                print(f"✓ Model downloaded and loaded: {model_name}")
            except Exception as download_error:
                print(f"✗ Model download failed: {download_error}")
                print(f"⚠ Python version: {sys.version}")
                raise RuntimeError(
                    f"Failed to load Spacy model. "
                    f"Run: python -m spacy download en_core_web_sm"
                ) from download_error
        except Exception as e:
            print(f"✗ Unexpected error loading model: {e}")
            raise

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
        chunk = chunk.replace('“', '"').replace('”', '"').replace("‘", "'").replace("’", "'")
        
        return chunk.strip()
    
    def _smart_split(self, text: str, max_chars: int) -> List[str]:
        """
        Uzun bir metni/cümleyi anlamlı yerlerden (noktalama) bölmeye çalışır.
        """
        if len(text) <= max_chars:
            return [text]
            
        chunks = []
        current_text = text
        
        while len(current_text) > max_chars:
            # Kesme noktası bul
            # Öncelik sırası: 
            # 1. Cümle bitişleri (.!?) - gerçi buraya gelmişse zaten tek cümle olması muhtemel
            # 2. Alt cümle bitişleri (;:)
            # 3. Virgüller (,)
            # 4. Boşluk ( )
            
            # Max limit içindeki son geçerli konumu bulmaya çalışacağız
            search_area = current_text[:max_chars]
            
            # Regex ile en uygun bölme noktasını ara (sondan başa doğru)
            # Noktalı virgül veya iki nokta
            split_match = re.search(r'[;:]\s', search_area[::-1])
            split_index = -1
            
            if split_match:
                # Tersten bulduğumuz için indeksi düzelt
                split_index = len(search_area) - split_match.end() + 1 # +1 to include punctuation
            else:
                # Virgül dene
                comma_match = re.search(r',\s', search_area[::-1])
                if comma_match:
                    split_index = len(search_area) - comma_match.end() + 1
                else:
                    # Boşluk dene (mecburiyet)
                    space_match = re.search(r'\s', search_area[::-1])
                    if space_match:
                        split_index = len(search_area) - space_match.end()
            
            if split_index > 0:
                chunks.append(current_text[:split_index].strip())
                current_text = current_text[split_index:].strip()
            else:
                # Hiçbir bölme noktası bulamadık (tek kelime çok uzun olabilir mi?)
                # Direkt max_chars'dan kes
                chunks.append(current_text[:max_chars].strip())
                current_text = current_text[max_chars:].strip()
                
        if current_text:
            chunks.append(current_text)
            
        return chunks

    def split_into_chunks(self, text: str, max_chars: int = 480, min_chars: int = 50, language: str = "en", normalize: bool = True) -> List[str]:
        """
        Metni mantıklı chunk'lara böler, birden fazla cümleyi birleştirir.
        """
        if not self.nlp:
            raise RuntimeError("NLP model not loaded")
            
        # Normalizasyon
        if normalize:
            text = self.normalizer.normalize(text, language)
            
        doc = self.nlp(text)
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
        
        return chunks if chunks else [""]

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
