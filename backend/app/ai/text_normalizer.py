import re
from num2words import num2words
from typing import Dict

class AdvancedTextNormalizer:
    """
    Gelişmiş metin normalizasyon sınıfı.
    Sayıları, kısaltmaları ve özel karakterleri okunuşlarına çevirir.
    """
    
    def __init__(self):
        self.abbreviations = {
            "Mr.": "Mister",
            "Mrs.": "Missus",
            "Ms.": "Miss",
            "Dr.": "Doctor",
            "St.": "Saint",
            "No.": "Number",
            "Vs.": "Versus",
            "Prof.": "Professor",
            "Lt.": "Lieutenant",
            "Capt.": "Captain",
            "Jr.": "Junior",
            "Sr.": "Senior",
            "Inc.": "Incorporated",
            "Ltd.": "Limited",
            "Co.": "Company"
        }
        
    def normalize(self, text: str, lang: str = "en") -> str:
        """Dile göre metni normalize eder."""
        if lang == "tr":
            return self.normalize_turkish(text)
        return self.normalize_english(text)
    
    def normalize_english(self, text: str) -> str:
        """İngilizce metin normalizasyonu."""
        if not text:
            return ""
            
        # 1. Fazla boşlukları temizle
        text = re.sub(r'\s+', ' ', text).strip()
        
        # 2. Kısaltmaları genişlet
        for abbr, full in self.abbreviations.items():
            # Kelime sınırlarını kontrol et (örn. "Dr." -> "Doctor" ama "Drive." -> "Drive.")
            pattern = r'\b' + re.escape(abbr)
            text = re.sub(pattern, full, text)
        
        # 3. Para birimleri ($100 -> "one hundred dollars")
        def currency_replacer(match):
            try:
                val = float(match.group(1).replace(',', ''))
                return num2words(val, lang='en', to='currency', currency='USD')
            except:
                return match.group(0)
                
        text = re.sub(r'\$(\d+(?:,\d{3})*)', currency_replacer, text)
        
        # 4. Yılları doğru oku (1990 -> "nineteen ninety")
        # 1000-2029 arası, ama para birimi veya diğer sayıların parçası olmayanlar
        def year_replacer(match):
            try:
                val = int(match.group(1))
                return num2words(val, lang='en', to='year')
            except:
                return match.group(0)

        text = re.sub(r'\b(1[0-9]{3}|20[0-2][0-9])\b', year_replacer, text)
        
        # 5. Sıra sayıları (21st -> "twenty-first")
        def ordinal_replacer(match):
            try:
                val = int(match.group(1))
                return num2words(val, lang='en', to='ordinal')
            except:
                return match.group(0)
                
        text = re.sub(r'\b(\d+)(st|nd|rd|th)\b', ordinal_replacer, text)
        
        # 6. Standart sayılar (tek başına duranlar)
        def number_replacer(match):
            try:
                val = int(match.group(0))
                # Çok uzun sayıları (telefon vb.) olduğu gibi bırak veya tek tek oku
                # Şimdilik 4 basamaktan küçükleri çeviriyoruz
                if len(match.group(0)) < 5:
                    return num2words(val, lang='en')
                return match.group(0)
            except:
                return match.group(0)
                
        text = re.sub(r'\b\d+\b', number_replacer, text)
        
        return text

    def normalize_turkish(self, text: str) -> str:
        """Türkçe metin normalizasyonu."""
        if not text:
            return ""
            
        # 1. Fazla boşlukları temizle
        text = re.sub(r'\s+', ' ', text).strip()
        
        # 2. Para birimleri (100 TL -> "yüz Türk Lirası")
        def tr_currency_replacer(match):
            try:
                val = int(match.group(1).replace('.', ''))
                return num2words(val, lang='tr', to='currency', currency='TRY')
            except:
                return match.group(0)
                
        text = re.sub(r'(\d+(?:\.\d{3})*)\s*(?:TL|tl|TRY)', tr_currency_replacer, text)
        
        # 3. Sayılar
        def tr_number_replacer(match):
            try:
                val = int(match.group(0))
                return num2words(val, lang='tr')
            except:
                return match.group(0)
                
        text = re.sub(r'\b\d+\b', tr_number_replacer, text)
        
        return text
