import spacy
from typing import List
import sys

class TextProcessor:
    def __init__(self, model_name="en_core_web_sm"):
        self.nlp = None
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

    def split_into_chunks(self, text: str, max_chars: int = 400) -> List[str]:
        """
        Metni mantıklı cümlelere böler ve her parçanın max_chars sınırını aşmamasını sağlar.
        Optimized: Set to 400 to stay within XTTS token limit (402 tokens max).
        XTTS can only generate text with a maximum of 400 tokens, so we use 400 chars
        as a safe limit (approximately 100-150 tokens depending on text complexity).
        """
        if not self.nlp:
            raise RuntimeError("NLP model not loaded")
            
        doc = self.nlp(text)
        sentences = [sent.text.strip() for sent in doc.sents if sent.text.strip()]
        
        chunks = []
        current_chunk = ""

        for sentence in sentences:
            # Eğer tek bir cümle bile limitten büyükse, basit bölme yap
            if len(sentence) > max_chars:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                    current_chunk = ""
                # Uzun cümleyi zorla böl (word-wrap stili)
                words = sentence.split()
                temp_chunk = ""
                for word in words:
                    if len(temp_chunk) + len(word) + 1 <= max_chars:
                        temp_chunk += word + " "
                    else:
                        if temp_chunk:
                            chunks.append(temp_chunk.strip())
                        temp_chunk = word + " "
                if temp_chunk:
                    chunks.append(temp_chunk.strip())
                continue

            if len(current_chunk) + len(sentence) + 1 <= max_chars:
                current_chunk += sentence + " "
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence + " "
        
        if current_chunk.strip():
            chunks.append(current_chunk.strip())
            
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
