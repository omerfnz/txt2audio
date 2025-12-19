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
            "Co.": "Company",
            "Vol.": "Volume",
            "vols.": "volumes",
            "Chap.": "Chapter",
            "Ch.": "Chapter",
            "p.": "page",
            "pp.": "pages",
            "ed.": "edition",
            "etc.": "et cetera",
            "e.g.": "for example",
            "i.e.": "that is",
            "viz.": "namely",
            "Fig.": "Figure",
            "Figs.": "Figures",
            "Rev.": "Reverend",
            "Hon.": "Honorable",
            "Gen.": "General",
            "Col.": "Colonel",
            "Maj.": "Major",
            "Sgt.": "Sergeant",
            "St": "Saint",
            "Mt.": "Mount",
            "Rd.": "Road",
            "Ave.": "Avenue",
            "Blvd.": "Boulevard",
            "Messrs.": "Messieurs",
            "Mlle.": "Mademoiselle",
            "Mme.": "Madame"
        }

        # Grekçe karakter eşleme
        self.greek_map = {
            'Α': 'A', 'Β': 'B', 'Γ': 'G', 'Δ': 'D', 'Ε': 'E', 'Ζ': 'Z', 'Η': 'E', 'Θ': 'Th',
            'Ι': 'I', 'Κ': 'K', 'Λ': 'L', 'Μ': 'M', 'Ν': 'N', 'Ξ': 'X', 'Ο': 'O', 'Π': 'P',
            'Ρ': 'R', 'Σ': 'S', 'Τ': 'T', 'Υ': 'Y', 'Φ': 'Ph', 'Χ': 'Ch', 'Ψ': 'Ps', 'Ω': 'O',
            'α': 'a', 'β': 'b', 'γ': 'g', 'δ': 'd', 'ε': 'e', 'ζ': 'z', 'η': 'e', 'θ': 'th',
            'ι': 'i', 'κ': 'k', 'λ': 'l', 'μ': 'm', 'ν': 'n', 'ξ': 'x', 'ο': 'o', 'π': 'p',
            'ρ': 'r', 'ς': 's', 'σ': 's', 'τ': 't', 'υ': 'y', 'φ': 'ph', 'χ': 'ch', 'ψ': 'ps', 'ω': 'o'
        }


    def roman_to_int(self, roman: str) -> int:
        """Roma rakamını tam sayıya çevirir."""
        roman = roman.upper()
        values = {'I': 1, 'V': 5, 'X': 10, 'L': 50, 'C': 100, 'D': 500, 'M': 1000}
        res = 0
        for i in range(len(roman)):
            if i > 0 and values[roman[i]] > values[roman[i - 1]]:
                res += values[roman[i]] - 2 * values[roman[i - 1]]
            else:
                res += values[roman[i]]
        return res

    def transliterate_greek(self, text: str) -> str:
        """Grekçe karakterleri Latin alfabesine çevirir."""
        return "".join(self.greek_map.get(c, c) for c in text)

    def clean_footnotes(self, text: str) -> str:
        """Metindeki dipnot ve referans numaralarını temizler."""
        # 1. Köşeli parantez içindeki rakamlar [1], [12] - Sadece rakam varsa sil
        text = re.sub(r'\[\d+\]', '', text)
        # 2. Kelime sonuna bitişik rakamlar (örn: parents.2 -> parents.)
        # Sadece sonu nokta veya harf ile biten kelimelerin sonundaki tekil rakamları yakala
        text = re.sub(r'([a-zA-Z\.])\d+\b', r'\1', text)
        return text



    def clean_text_formatting(self, text: str) -> str:
        """
        Metindeki genel format bozukluklarını düzeltir.
        Gereksiz satır sonlarını birleştirir ve özel vurgu işaretlerini temizler.
        """
        if not text:
            return ""

        # 1. İtalik vurguları temizle (_word_ -> word)
        text = re.sub(r'_(.*?)_', r'\1', text)
        
        # 2. Köşeli parantez içindeki teknik notları sil (örn. [Illustration])
        text = re.sub(r'\[.*?\]', '', text)

        # 3. Satır birleştirme (Line Unwrapping)
        text = text.replace('\r', '')
        
        # Paragrafları (çift enter) geçici bir belirteçle koru
        text = re.sub(r'\n\s*\n', '<PARAGRAPH_BREAK>', text)
        
        # Tek satır sonlarını boşlukla değiştir (Cümleleri birleştir)
        text = text.replace('\n', ' ')
        
        # Fazla boşlukları temizle
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Paragrafları geri getir (Seslendirme için paragraf arası önemlidir)
        text = text.replace('<PARAGRAPH_BREAK>', '\n\n')
        
        return text


    def normalize(self, text: str, lang: str = "en") -> str:
        """Dile göre metni normalize eder."""
        if not text:
            return ""

        # 1. Temel temizlikler (Grekçe ve dipnotlar)
        text = self.transliterate_greek(text)
        text = self.clean_footnotes(text)
        
        # 2. Roma rakamlarını ve bölümleri işle
        text = self.normalize_roman_chapters(text, lang)

        # 3. Genel format düzeltmesi yap (Satır sonları vb.)
        text = self.clean_text_formatting(text)
        
        # 4. İngilizce normalizasyonu (Sayılar, kısaltmalar)
        text = self.normalize_english(text)

        # 5. Fazla boşlukları son kez temizle
        text = re.sub(r'\s+', ' ', text).strip()

        return text


    
    def normalize_english(self, text: str) -> str:
        """İngilizce metin normalizasyonu - XTTS için optimize edilmiş."""
        if not text:
            return ""


        # 1. Kısaltmaları genişlet
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
        
        # 8. Özel karakterleri temizle (kitap metinlerinde yaygın olan çizgiler, tireler)
        text = self.clean_special_characters(text)

        # 9. Standart tam sayılar (virgülsüz, küçük sayılar)
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

    def clean_special_characters(self, text: str) -> str:
        """
        Kitap metinlerinde yaygın olan özel karakterleri temizler/dönüştürür.
        TTS'nin yanlış okumaması için.
        """
        if not text:
            return ""

        # Çizgiler ve tireler - boşlukla değiştir (pause etkisi için)
        dash_characters = [
            '—',  # Em dash (U+2014)
            '–',  # En dash (U+2013)
            '―',  # Horizontal bar (U+2015)
            '⸻',  # Three-em dash (U+2E3A)
            '⸻',  # Three-em dash (U+2E3B) - kullanıcının bahsettiği
            '〜',  # Wave dash (U+301C)
            '～',  # Fullwidth tilde (U+FF5E)
            '﹘',  # Small em dash (U+FE58)
            '﹣',  # Small hyphen-minus (U+FE63)
            '－',  # Fullwidth hyphen-minus (U+FF0D)
            '֊',  # Armenian hyphen (U+058A)
            '־',  # Hebrew punctuation maqaf (U+05BE)
            '᐀',  # Canadian syllabics hyphen (U+1400)
            '′',  # Prime symbol (Flatland'de var)
            '″',  # Double prime
            '--', # Alternatif ikili tire
            '---', # Alternatif üçlü tire
            '⁠—', # Zero Width Joiner + Em Dash (Ethan Frome'daki yapı)
        ]


        # Çizgileri boşlukla değiştir (hafif pause etkisi)
        for dash in dash_characters:
            text = text.replace(dash, ' ')

        # Diğer özel Unicode karakterleri de temizle/güncelle
        # Yıldızlar ve süslemeler
        text = re.sub(r'[☆★✩✪✫✬✭✮✯✰✱✲✳✴✵✶✷✸✹✺✻✼✽✾✿❀❁❂❃❄❅❆❇❈❉❊❋*]', '', text)

        # Özel tırnak işaretleri - normal tırnaklara dönüştür
        text = text.replace('"', '"').replace('"', '"').replace('“', '"').replace('”', '"')
        text = text.replace(''', "'").replace(''', "'").replace('‘', "'").replace('’', "'")

        # Elips (...) - üç nokta olarak bırak ama fazla noktaları temizle
        text = re.sub(r'\.{4,}', '...', text)  # 4+ nokta → ...

        # Diğer özel karakterler
        special_replacements = {
            '…': '...',  # Elipsis
            '•': '',     # Bullet point - kaldır
            '○': '',     # White circle - kaldır
            '●': '',     # Black circle - kaldır
            '□': '',     # White square - kaldır
            '■': '',     # Black square - kaldır
            '◇': '',     # White diamond - kaldır
            '◆': '',     # Black diamond - kaldır
            '△': '',     # White triangle - kaldır
            '▲': '',     # Black triangle - kaldır
            '▽': '',     # White triangle down - kaldır
            '▼': '',     # Black triangle down - kaldır
        }

        for char, replacement in special_replacements.items():
            text = text.replace(char, replacement)

        return text

    def normalize_roman_chapters(self, text: str) -> str:
        """
        Roman bölümlerini (Roma rakamları) ve chapter başlıklarını normalize eder.
        """
        if not text:
            return ""

        # 1. Tek başına Roma rakamı bölümler (örn: ^I$ veya I\n)
        def standalone_roman_replacer(match):
            roman = match.group(1).strip()
            if re.match(r'^M{0,4}(CM|CD|D?C{0,3})(XC|XL|L?X{0,3})(IX|IV|V?I{0,3})$', roman):
                try:
                    num = self.roman_to_int(roman)
                    if num > 0:
                        word = num2words(num, lang='en').title()
                        return f"\n\nChapter {word}\n\n"
                except:
                    pass
            return match.group(0)

        text = re.sub(r'(?:^|\n\n)\s*([IVXLCDM]{1,10})\s*(?:\n|$)', standalone_roman_replacer, text, flags=re.MULTILINE)

        # 2. "Chapter X", "Part X", "Section X", "Book X" formatını normalize et (Roma rakamı veya sayı)
        def section_replacer(match):
            prefix = match.group(1).title()
            num_str = match.group(2)
            try:
                if num_str.isdigit():
                    num = int(num_str)
                else:
                    num = self.roman_to_int(num_str)
                
                if num > 0:
                    return f"{prefix} {num2words(num, lang='en').title()}"
            except:
                pass
            return match.group(0)

        pattern = r'\b(Chapter|Part|Section|Book)\s+([IVXLCDM]+|\d+)\b'
        text = re.sub(pattern, section_replacer, text, flags=re.IGNORECASE)

        # 3. Tek başına "X." formatını da yakala (örn: "1." -> "First")
        def numbered_section_replacer(match):
            num_str = match.group(1)
            try:
                num = int(num_str)
                return f"{num2words(num, lang='en', to='ordinal').title()}."
            except:
                return match.group(0)

        text = re.sub(r'\b(\d+)\.(?=\s|$)', numbered_section_replacer, text)

        return text


