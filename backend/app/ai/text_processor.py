import spacy
from typing import List
import sys

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
        """Chunk'ın noktalama ile bittiğini garanti eder ve özel karakterleri korur."""
        chunk = chunk.strip()
        
        if not chunk:
            return chunk
        
        # Ellipsis (...) ve em-dash (—) gibi özel karakterleri koru
        # Bu karakterler kitaplarda sıkça kullanılır ve anlamsal olarak önemlidir
        
        # Cümle sonu noktalama kontrolü - genişletilmiş
        valid_endings = (
            '.', '!', '?',           # Standart noktalama
            '...', '…',              # Ellipsis (3 nokta veya Unicode)
            '.\"', '!\"', '?\"',     # Tırnak içinde biten
            '.\'', '!\'', '?\'',     # Tek tırnak ile biten
            '.)', '!)', '?)',        # Parantez içinde biten
            '."', '!"', '?"',        # Çift tırnak (farklı encoding)
            '.—', '!—', '?—',        # Em-dash ile biten
            '—', '–',                # Sadece dash (cümle kesilmesi)
        )
        
        if not chunk.endswith(valid_endings):
            # Son karakter alfanumerik ise nokta ekle
            if chunk[-1].isalnum():
                chunk += "."
            # Virgül ile bitiyorsa (cümle ortası), nokta ekle
            elif chunk[-1] == ',':
                chunk += "."
        
        return chunk
    
    def split_into_chunks(self, text: str, max_chars: int = 800, min_chars: int = 100, language: str = "en", normalize: bool = True) -> List[str]:
        """
        Metni mantıklı chunk'lara böler, birden fazla cümleyi birleştirir.
        CÜMLE SINIRLARINI KORUR - cümle ortasında bölme yapmaz.
        
        Args:
            max_chars: Maksimum chunk uzunluğu (varsayılan: 800)
            min_chars: Minimum chunk uzunluğu (varsayılan: 100)
            language: Dil kodu
            normalize: Metin normalizasyonu yapılsın mı
            
        Not:
            - XTTS v2, yaklaşık 400 token civarında bir üst limite sahiptir.
            - Metin normalizasyonu (sayısal ifadelerin uzaması vb.) sonrası
              gerçek token sayısı karakter sayısından çok daha yüksek olabilir.
            - 800 karakter güvenli bir üst sınır (normalizasyon sonrası ~350-400 token)
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

            # Tek bir cümle max_chars'ı aşıyorsa - cümle ortasında bölme yapma!
            # Bu durumda cümleyi olduğu gibi bir chunk olarak al
            if len(sentence) > max_chars:
                # Mevcut chunk'ı kaydet
                if current_chunk:
                    chunks.append(self.validate_chunk(current_chunk.strip()))
                    current_chunk = ""
                
                # Uzun cümleyi tek başına chunk olarak ekle
                # Cümle ortasında bölme yapmıyoruz - cümle sınırlarını koruyoruz
                chunks.append(self.validate_chunk(sentence))
            else:
                # Cümleyi mevcut chunk'a eklemeyi dene
                potential_chunk = current_chunk + " " + sentence if current_chunk else sentence
                
                if len(potential_chunk) <= max_chars:
                    # Ekle, hala limit içinde
                    current_chunk = potential_chunk
                else:
                    # Mevcut chunk'ı kaydet ve yeni chunk başlat
                    if current_chunk:
                        chunks.append(self.validate_chunk(current_chunk.strip()))
                    current_chunk = sentence
        
        # Son chunk'ı ekle (minimum uzunluk kontrolü ile)
        if current_chunk:
            current_chunk = current_chunk.strip()
            if len(current_chunk) >= min_chars:
                chunks.append(self.validate_chunk(current_chunk))
            else:
                # Çok kısa chunk'ı önceki chunk'a ekle (varsa)
                if chunks:
                    chunks[-1] = self.validate_chunk(chunks[-1] + " " + current_chunk)
                else:
                    # Hiç chunk yoksa, yine de ekle
                    chunks.append(self.validate_chunk(current_chunk))

        return chunks if chunks else [""] # En az 1 chunk döndür


if __name__ == "__main__":
    try:
        processor = TextProcessor()
        sample_text = "This is a test sentence. Here is another one that is slightly longer. " * 5
        chunks = processor.split_into_chunks(sample_text)
        print(f"\nTotal chunks: {len(chunks)}")
        for i, chunk in enumerate(chunks):
            print(f"{i+1}: {chunk[:50]}... (Len: {len(chunk)})")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
