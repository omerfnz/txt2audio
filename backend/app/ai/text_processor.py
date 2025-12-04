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
        """Chunk'ın noktalama ile bittiğini garanti eder."""
        chunk = chunk.strip()
        
        if not chunk:
            return chunk
        
        # Cümle sonu noktalama kontrolü
        if not chunk.endswith(('.', '!', '?', '...', '."', '!"', '?"', '."', '.)', '!)', '?)')):
            # Son karakter alfanumerik ise nokta ekle
            if chunk[-1].isalnum():
                chunk += "."
        
        return chunk
    
    def split_into_chunks(self, text: str, max_chars: int = 280, language: str = "en", normalize: bool = True) -> List[str]:
        """
        Metni mantıklı cümlelere böler ve her parçanın max_chars sınırını aşmamasını sağlar.

        Not:
            - XTTS v2, yaklaşık 400 token civarında bir üst limite sahiptir.
            - Metin normalizasyonu (sayısal ifadelerin uzaması vb.) sonrası
              gerçek token sayısı karakter sayısından çok daha yüksek olabilir.

        Bu nedenle varsayılan olarak daha konservatif bir sınır kullanılır:
            max_chars = 280 (özellikle İngilizce metinler için güvenli seviye).
        """
        if not self.nlp:
            raise RuntimeError("NLP model not loaded")
            
        # Normalizasyon
        if normalize:
            text = self.normalizer.normalize(text, language)
            
        doc = self.nlp(text)
        sentences = [sent.text.strip() for sent in doc.sents if sent.text.strip()]
        
        chunks: List[str] = []

        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue

            # Her cümleyi mümkün olduğunca kendi başına bir chunk olarak üret.
            # Sadece tek bir cümle max_chars sınırını aşıyorsa word-wrap ile böl.
            if len(sentence) > max_chars:
                words = sentence.split()
                temp_chunk = ""
                for word in words:
                    if len(temp_chunk) + len(word) + 1 <= max_chars:
                        temp_chunk += word + " "
                    else:
                        if temp_chunk:
                            chunks.append(self.validate_chunk(temp_chunk.strip()))
                        temp_chunk = word + " "
                if temp_chunk:
                    chunks.append(self.validate_chunk(temp_chunk.strip()))
            else:
                chunks.append(self.validate_chunk(sentence))

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
