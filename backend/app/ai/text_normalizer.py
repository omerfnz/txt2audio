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
        """İngilizce metin normalizasyonu - XTTS için optimize edilmiş."""
        if not text:
            return ""
            
        # 0. Satır sonu iyileştirmesi: Paragraf boşluklarını cümle sonu olarak işaretle
        # Bu, nokta konulmadan alt satıra geçilen metinlerde Spacy'nin cümleyi tanımasını sağlar
        text = text.replace('\r\n', '\n').replace('\r', '\n')
        # Eğer bir satır harf/rakam ile bitip çift enter ile ayrılıyorsa, nokta ekle
        text = re.sub(r'(?<=[a-zA-Z0-9])\n\n+', '.\n', text)
            
        # 1. Fazla boşlukları temizle
        text = re.sub(r'\s+', ' ', text).strip()
        
        # 2. Kısaltmaları genişlet
        for abbr, full in self.abbreviations.items():
            # Kelime sınırlarını kontrol et (örn. "Dr." -> "Doctor" ama "Drive." -> "Drive.")
            pattern = r'\b' + re.escape(abbr)
            text = re.sub(pattern, full, text)
        
        # 3. Para birimleri - virgüllü ve ondalıklı sayıları destekler
        # $1,234.56 -> "one thousand, two hundred and thirty-four dollars and fifty-six cents"
        def currency_replacer(match):
            try:
                val = float(match.group(1).replace(',', ''))
                return num2words(val, lang='en', to='currency', currency='USD')
            except:
                return match.group(0)
                
        text = re.sub(r'\$(\d{1,3}(?:,\d{3})*(?:\.\d{1,2})?)', currency_replacer, text)
        
        # 4. Yılları doğru oku (1990 -> "nineteen ninety")
        # Yıl tespiti: 1000-2099 arası, ama virgüllü sayıların parçası olmayan
        # Negatif lookbehind/lookahead ile virgül içeren sayıları atla
        def year_replacer(match):
            try:
                val = int(match.group(1))
                return num2words(val, lang='en', to='year')
            except:
                return match.group(0)

        # Önce yılları işle (virgül olmayan 4 basamaklı sayılar)
        text = re.sub(r'(?<!,)\b(1[0-9]{3}|20[0-9]{2})\b(?!,)', year_replacer, text)
        
        # 5. Sıra sayıları - virgüllü büyük sayıları da destekler
        # 1,234th -> "one thousand, two hundred and thirty-fourth"
        def ordinal_replacer(match):
            try:
                val = int(match.group(1).replace(',', ''))
                return num2words(val, lang='en', to='ordinal')
            except:
                return match.group(0)
                
        text = re.sub(r'\b(\d{1,3}(?:,\d{3})*)(st|nd|rd|th)\b', ordinal_replacer, text)
        
        # 6. Ondalıklı sayılar - virgüllü büyük ondalık sayıları da destekler
        # 1,234.56 -> "one thousand, two hundred and thirty-four point five six"
        def decimal_replacer(match):
            try:
                # Virgülleri temizle
                num_str = match.group(0).replace(',', '')
                
                # Ondalık kısmı ayır
                parts = num_str.split('.')
                integer_part = int(parts[0])
                decimal_part = parts[1]
                
                # Tam sayı kısmını çevir
                result = num2words(integer_part, lang='en')
                result += " point"
                
                # Ondalık kısmını basamak basamak oku
                for digit in decimal_part:
                    result += " " + num2words(int(digit), lang='en')
                
                return result
            except:
                return match.group(0)
        
        text = re.sub(r'\b\d{1,3}(?:,\d{3})*\.\d+\b', decimal_replacer, text)
        
        # 7. Virgüllü büyük tam sayılar - EN ÖNEMLİ FİX!
        # 140,000 veya 1,234,567 gibi virgülle ayrılmış sayılar
        # Bu, XTTS'nin "one hundred forty zero zero zero" demesini önler
        def large_number_replacer(match):
            try:
                # Virgülleri temizle ve sayıya çevir
                num_str = match.group(0).replace(',', '')
                val = int(num_str)
                
                # XTTS için sayıyı kelimeye çevir
                return num2words(val, lang='en')
            except:
                return match.group(0)
        
        # Virgüllü sayıları yakala (örn: 1,234 veya 140,000)
        # En az bir virgül içeren, doğru formatta yazılmış sayılar
        text = re.sub(r'\b\d{1,3}(?:,\d{3})+\b', large_number_replacer, text)
        
        # 8. Standart tam sayılar (virgülsüz, küçük sayılar)
        # Telefon numaraları ve çok uzun sayı dizilerini atla
        def number_replacer(match):
            try:
                num_str = match.group(0)
                
                # Çok uzun sayı dizilerini atla (telefon, ID vb. olabilir)
                if len(num_str) > 10:
                    return match.group(0)
                
                val = int(num_str)
                
                # Sayıyı kelimeye çevir
                return num2words(val, lang='en')
            except:
                return match.group(0)
        
        # Virgül içermeyen, henüz işlenmemiş standart sayılar
        text = re.sub(r'\b\d+\b', number_replacer, text)
        
        return text

    def normalize_turkish(self, text: str) -> str:
        """Türkçe metin normalizasyonu - XTTS için optimize edilmiş."""
        if not text:
            return ""
            
        # 0. Satır sonu iyileştirmesi
        text = text.replace('\r\n', '\n').replace('\r', '\n')
        text = re.sub(r'(?<=[a-zA-Z0-9])\n\n+', '.\n', text)
            
        # 1. Fazla boşlukları temizle
        text = re.sub(r'\s+', ' ', text).strip()
        
        # 2. Para birimleri - noktalı büyük sayıları destekler
        # 1.234 TL veya 140.000 TL -> Türkçe okunuşa çevir
        def tr_currency_replacer(match):
            try:
                # Türkçe'de binlik ayracı nokta
                val = int(match.group(1).replace('.', ''))
                return num2words(val, lang='tr', to='currency', currency='TRY')
            except:
                return match.group(0)
                
        text = re.sub(r'(\d{1,3}(?:\.\d{3})*(?:,\d{1,2})?)\s*(?:TL|tl|TRY)', tr_currency_replacer, text)
        
        # 3. Sıra sayıları - Türkçe
        # 1. -> "birinci", 21. -> "yirmi birinci"
        # Noktalı büyük sayıları da destekler: 1.234. -> "bin iki yüz otuz dördüncü"
        def tr_ordinal_replacer(match):
            try:
                val = int(match.group(1).replace('.', ''))
                return num2words(val, lang='tr', to='ordinal')
            except:
                return match.group(0)
        
        text = re.sub(r'\b(\d{1,3}(?:\.\d{3})*)\.(?=\s|$)', tr_ordinal_replacer, text)
        
        # 4. Ondalıklı sayılar - Türkçe'de virgül kullanılır
        # 3,14 -> "üç virgül on dört"
        def tr_decimal_replacer(match):
            try:
                # Binlik ayracı noktaları temizle
                num_str = match.group(0).replace('.', '')
                
                # Ondalık ayracı virgülü ayır
                parts = num_str.split(',')
                integer_part = int(parts[0])
                decimal_part = parts[1]
                
                # Tam sayı kısmını çevir
                result = num2words(integer_part, lang='tr')
                result += " virgül"
                
                # Ondalık kısmını basamak basamak oku
                for digit in decimal_part:
                    result += " " + num2words(int(digit), lang='tr')
                
                return result
            except:
                return match.group(0)
        
        # Türkçe'de ondalık ayracı virgül, binlik ayracı nokta
        # Örn: 1.234,56
        text = re.sub(r'\b\d{1,3}(?:\.\d{3})*,\d+\b', tr_decimal_replacer, text)
        
        # 5. Noktalı büyük tam sayılar - EN ÖNEMLİ FİX!
        # Türkçe'de binlik ayıracı nokta: 140.000, 1.234.567
        # Bu, XTTS'nin sayıları yanlış okumasını önler
        def tr_large_number_replacer(match):
            try:
                # Noktaları temizle ve sayıya çevir
                num_str = match.group(0).replace('.', '')
                val = int(num_str)
                
                # XTTS için Türkçe kelimeye çevir
                return num2words(val, lang='tr')
            except:
                return match.group(0)
        
        # Noktalı sayıları yakala (örn: 1.234 veya 140.000)
        # En az bir nokta içeren, doğru formatta yazılmış sayılar
        # Ancak cümle sonu noktalarıyla karıştırma!
        text = re.sub(r'\b\d{1,3}(?:\.\d{3})+\b(?!\.)', tr_large_number_replacer, text)
        
        # 6. Standart tam sayılar (noktasız, küçük sayılar)
        # Telefon numaraları ve çok uzun sayı dizilerini atla
        def tr_number_replacer(match):
            try:
                num_str = match.group(0)
                
                # Çok uzun sayı dizilerini atla (telefon, ID vb. olabilir)
                if len(num_str) > 10:
                    return match.group(0)
                
                val = int(num_str)
                
                # Sayıyı Türkçe kelimeye çevir
                return num2words(val, lang='tr')
            except:
                return match.group(0)
        
        # Nokta içermeyen, henüz işlenmemiş standart sayılar
        text = re.sub(r'\b\d+\b', tr_number_replacer, text)
        
        return text
