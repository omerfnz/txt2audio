# 📊 Chunk Oluşturma Optimizasyon Raporu

## 📋 İçindekiler
1. [Mevcut Durum Analizi](#mevcut-durum-analizi)
2. [Sorunların Tespiti](#sorunların-tespiti)
3. [Performans Etkisi](#performans-etkisi)
4. [Optimizasyon Önerileri](#optimizasyon-önerileri)
5. [Uygulama Planı](#uygulama-planı)
6. [Beklenen İyileştirmeler](#beklenen-iyileştirmeler)

---

## 🔍 Mevcut Durum Analizi

### Chunk Oluşturma Mantığı

Projede chunk oluşturma işlemi `backend/app/ai/text_processor.py` dosyasındaki `split_into_chunks` fonksiyonu tarafından gerçekleştirilmektedir.

**Mevcut Algoritma:**
```python
def split_into_chunks(self, text: str, max_chars: int = 280, language: str = "en", normalize: bool = True) -> List[str]:
    # 1. Metin Spacy NLP ile cümlelere ayrılır
    doc = self.nlp(text)
    sentences = [sent.text.strip() for sent in doc.sents if sent.text.strip()]
    
    # 2. Her cümle ayrı bir chunk olarak oluşturulur
    for sentence in sentences:
        if len(sentence) > max_chars:
            # Sadece çok uzun cümleler word-wrap ile bölünür
            # ... word-wrap logic ...
        else:
            chunks.append(self.validate_chunk(sentence))  # Her cümle = 1 chunk
```

### Mevcut Parametreler

- **max_chars**: 280 karakter (varsayılan)
- **Chunk stratejisi**: Her cümle = 1 chunk
- **Minimum chunk uzunluğu**: Yok
- **Cümle birleştirme**: Yok

### İşlem Akışı

1. **Proje Oluşturma** (`backend/app/routers/projects.py:246-258`):
   - Metin dosyası okunur
   - Gutenberg formatı kontrol edilir
   - `text_processor.split_into_chunks()` çağrılır
   - Her chunk veritabanına kaydedilir

2. **Ses Üretimi** (`backend/app/services/audio_service.py:181-398`):
   - Her chunk için ayrı TTS çağrısı yapılır
   - Her chunk için ayrı WAV dosyası oluşturulur
   - Tüm chunk'lar birleştirilir

---

## ⚠️ Sorunların Tespiti

### 1. **Her Cümle Ayrı Chunk Oluşturuluyor**

**Sorun:**
- Mevcut kod her cümleyi ayrı bir chunk olarak oluşturuyor
- Uzun kitaplarda (örn. 100,000+ kelime) bu yaklaşım 4000-6000 chunk oluşmasına neden oluyor

**Kod Referansı:**
```92:112:backend/app/ai/text_processor.py
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
```

**Etki:**
- Her chunk için ayrı TTS model çağrısı
- Her chunk için ayrı dosya I/O işlemi
- Her chunk için ayrı memory allocation
- Toplam işlem süresi: `chunk_sayısı × (TTS_süresi + I/O_süresi)`

### 2. **max_chars Çok Düşük**

**Sorun:**
- Varsayılan `max_chars = 280` çok konservatif
- XTTS v2'nin gerçek token limiti yaklaşık 400 token
- Normalizasyon sonrası bu yaklaşık 1000-1200 karaktere denk gelebilir

**Kod Referansı:**
```68:79:backend/app/ai/text_processor.py
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
```

**Etki:**
- Potansiyel kapasite kullanılmıyor
- Daha fazla chunk oluşuyor
- Daha fazla TTS çağrısı gerekiyor

### 3. **Cümle Birleştirme Mantığı Yok**

**Sorun:**
- Birden fazla kısa cümleyi birleştirerek daha büyük chunk'lar oluşturma mantığı yok
- Kısa cümleler (örn. 20-50 karakter) tek başına chunk oluyor
- Bu da gereksiz chunk sayısına neden oluyor

**Örnek Senaryo:**
```
Cümle 1: "Hello." (6 karakter) → Chunk 1
Cümle 2: "How are you?" (12 karakter) → Chunk 2
Cümle 3: "I'm fine." (9 karakter) → Chunk 3
```

Bu 3 cümle tek bir chunk olabilir: `"Hello. How are you? I'm fine."` (27 karakter)

### 4. **Minimum Chunk Uzunluğu Kontrolü Yok**

**Sorun:**
- Çok kısa chunk'lar (örn. 5-10 karakter) oluşabiliyor
- Bu chunk'lar için TTS çağrısı yapılması verimsiz

---

## 📈 Performans Etkisi

### Mevcut Durum (Örnek: 100,000 kelimelik kitap)

**Varsayımlar:**
- Ortalama cümle uzunluğu: 15 kelime
- Ortalama kelime uzunluğu: 5 karakter
- Toplam cümle sayısı: ~6,667 cümle
- Her cümle = 1 chunk → **~6,667 chunk**

**İşlem Süresi Hesaplaması:**
- TTS çağrısı başına: ~2-3 saniye (CPU) / ~0.5-1 saniye (GPU)
- I/O işlemi başına: ~0.1 saniye
- Toplam süre (CPU): `6,667 × (2.5 + 0.1) = ~17,322 saniye ≈ 4.8 saat`
- Toplam süre (GPU): `6,667 × (0.75 + 0.1) = ~5,667 saniye ≈ 1.6 saat`

### Optimizasyon Sonrası Beklenen Durum

**Varsayımlar:**
- Ortalama chunk uzunluğu: 800 karakter (3-4 cümle birleştirilmiş)
- Toplam chunk sayısı: ~1,250 chunk (5.3x azalma)

**İşlem Süresi Hesaplaması:**
- TTS çağrısı başına: ~3-4 saniye (CPU) / ~1-1.5 saniye (GPU)
- I/O işlemi başına: ~0.1 saniye
- Toplam süre (CPU): `1,250 × (3.5 + 0.1) = ~4,500 saniye ≈ 1.25 saat` (**74% hızlanma**)
- Toplam süre (GPU): `1,250 × (1.25 + 0.1) = ~1,688 saniye ≈ 0.47 saat` (**70% hızlanma**)

---

## 💡 Optimizasyon Önerileri

### 1. **Cümle Birleştirme Algoritması**

**Strateji:**
- Birden fazla cümleyi birleştirerek `max_chars` limitine yaklaş
- Cümle sınırlarını koru (doğal duraklamalar için)
- Minimum chunk uzunluğu belirle (örn. 100 karakter)

**Yeni Algoritma:**
```python
def split_into_chunks(self, text: str, max_chars: int = 800, min_chars: int = 100, language: str = "en", normalize: bool = True) -> List[str]:
    """
    Metni mantıklı chunk'lara böler, birden fazla cümleyi birleştirir.
    
    Args:
        max_chars: Maksimum chunk uzunluğu (varsayılan: 800)
        min_chars: Minimum chunk uzunluğu (varsayılan: 100)
    """
    # 1. Cümlelere ayır
    doc = self.nlp(text)
    sentences = [sent.text.strip() for sent in doc.sents if sent.text.strip()]
    
    chunks = []
    current_chunk = ""
    
    for sentence in sentences:
        # Tek bir cümle max_chars'ı aşıyorsa word-wrap ile böl
        if len(sentence) > max_chars:
            # Mevcut chunk'ı kaydet
            if current_chunk:
                chunks.append(self.validate_chunk(current_chunk.strip()))
                current_chunk = ""
            
            # Uzun cümleyi word-wrap ile böl
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
                current_chunk = temp_chunk
        else:
            # Cümleyi mevcut chunk'a ekle
            potential_chunk = current_chunk + " " + sentence if current_chunk else sentence
            
            if len(potential_chunk) <= max_chars:
                current_chunk = potential_chunk
            else:
                # Mevcut chunk'ı kaydet ve yeni chunk başlat
                if current_chunk:
                    chunks.append(self.validate_chunk(current_chunk.strip()))
                current_chunk = sentence
    
    # Son chunk'ı ekle (minimum uzunluk kontrolü ile)
    if current_chunk and len(current_chunk.strip()) >= min_chars:
        chunks.append(self.validate_chunk(current_chunk.strip()))
    elif current_chunk:
        # Çok kısa chunk'ı önceki chunk'a ekle
        if chunks:
            chunks[-1] = self.validate_chunk(chunks[-1] + " " + current_chunk)
        else:
            chunks.append(self.validate_chunk(current_chunk.strip()))
    
    return chunks if chunks else [""]
```

### 2. **max_chars Değerini Artırma**

**Öneri:**
- Varsayılan `max_chars`: 280 → **800**
- XTTS v2'nin 400 token limiti göz önünde bulundurularak güvenli bir değer
- Normalizasyon sonrası token sayısı artabileceği için 800 karakter güvenli bir üst sınır

**Token Hesaplama:**
- Ortalama token/karakter oranı: ~0.3-0.4 (İngilizce)
- 800 karakter × 0.35 = ~280 token (güvenli)
- Normalizasyon sonrası: ~350-400 token (limit içinde)

### 3. **Minimum Chunk Uzunluğu**

**Öneri:**
- `min_chars = 100` karakter
- Çok kısa chunk'lar önceki chunk'a birleştirilir
- Bu, gereksiz TTS çağrılarını önler

### 4. **Dinamik max_chars Ayarlama**

**Öneri:**
- Dil bazlı farklı `max_chars` değerleri
- İngilizce: 800 karakter
- Türkçe: 600 karakter (daha uzun kelimeler)
- Diğer diller: 700 karakter (varsayılan)

### 5. **Paragraf Bazlı Chunking (İleri Seviye)**

**Öneri:**
- Paragraf sınırlarını koru
- Paragraf içinde cümleleri birleştir
- Paragraf sonlarında doğal duraklamalar için ekstra sessizlik ekle

---

## 🛠️ Uygulama Planı

### Faz 1: Temel Optimizasyonlar (Yüksek Öncelik)

1. **Cümle Birleştirme Algoritması** ✅
   - `text_processor.py` dosyasını güncelle
   - `max_chars` varsayılanını 800'e çıkar
   - `min_chars` parametresi ekle (100)

2. **Test ve Doğrulama**
   - Mevcut test dosyası ile karşılaştırma
   - Chunk sayısı ve uzunluk dağılımı analizi
   - TTS kalitesi kontrolü

**Beklenen Süre:** 2-3 saat

### Faz 2: İleri Optimizasyonlar (Orta Öncelik)

3. **Dinamik max_chars**
   - Dil bazlı ayarlama
   - Config dosyasına ekleme

4. **Paragraf Bazlı Chunking**
   - Paragraf tespiti
   - Paragraf sınırlarını koruma

**Beklenen Süre:** 4-6 saat

### Faz 3: Performans İzleme (Düşük Öncelik)

5. **Metrikler ve Loglama**
   - Chunk sayısı loglama
   - Ortalama chunk uzunluğu
   - İşlem süresi karşılaştırması

**Beklenen Süre:** 2-3 saat

---

## 📊 Beklenen İyileştirmeler

### Chunk Sayısı Azalması

| Kitap Uzunluğu | Mevcut Chunk Sayısı | Optimize Chunk Sayısı | Azalma Oranı |
|----------------|---------------------|----------------------|--------------|
| 50,000 kelime  | ~3,333              | ~625                 | **81%** ↓     |
| 100,000 kelime | ~6,667              | ~1,250               | **81%** ↓     |
| 200,000 kelime | ~13,333             | ~2,500               | **81%** ↓     |

### İşlem Süresi İyileştirmesi

| Mod | Mevcut Süre | Optimize Süre | İyileştirme |
|-----|-------------|---------------|-------------|
| CPU | 4.8 saat    | 1.25 saat     | **74%** ↓    |
| GPU | 1.6 saat    | 0.47 saat     | **70%** ↓    |

### Kaynak Kullanımı

- **TTS Çağrı Sayısı:** %81 azalma
- **Dosya I/O İşlemleri:** %81 azalma
- **Memory Allocation:** %81 azalma
- **Network Overhead (WebSocket):** %81 azalma

### Kalite Etkisi

- **Pozitif:**
  - Daha uzun chunk'lar daha doğal ses akışı sağlar
  - Cümle sınırları korunduğu için doğal duraklamalar korunur
  - Daha az chunk = daha az birleştirme noktası = daha akıcı ses

- **Dikkat Edilmesi Gerekenler:**
  - Çok uzun chunk'lar token limitini aşabilir (800 karakter güvenli)
  - Normalizasyon sonrası token sayısı artabilir (monitoring gerekli)

---

## 🔧 Teknik Detaylar

### XTTS v2 Token Limiti

- **Gerçek Limit:** ~400 token
- **Güvenli Limit:** ~350 token
- **Karakter-Token Dönüşümü:**
  - İngilizce: ~0.3-0.4 token/karakter
  - Türkçe: ~0.4-0.5 token/karakter
  - Normalizasyon sonrası: +20-30% token artışı

### Chunk Uzunluk Dağılımı (Önerilen)

- **Minimum:** 100 karakter (çok kısa chunk'ları önlemek için)
- **Hedef:** 600-800 karakter (optimal)
- **Maksimum:** 800 karakter (güvenli üst sınır)

### Cümle Birleştirme Stratejisi

1. **Greedy Approach:** Mümkün olduğunca cümle ekle, `max_chars`'a yaklaş
2. **Cümle Sınırlarını Koru:** Doğal duraklamalar için
3. **Minimum Uzunluk:** Çok kısa chunk'ları önceki chunk'a ekle

---

## 📝 Sonuç ve Öneriler

### Öncelikli Aksiyonlar

1. ✅ **Cümle birleştirme algoritmasını uygula** (Faz 1)
2. ✅ **max_chars değerini 800'e çıkar** (Faz 1)
3. ✅ **min_chars parametresi ekle** (Faz 1)
4. ⚠️ **Test ve doğrulama yap** (Faz 1)
5. 📊 **Performans metriklerini izle** (Faz 3)

### Beklenen Sonuçlar

- **Chunk sayısında %80+ azalma**
- **İşlem süresinde %70+ hızlanma**
- **Kaynak kullanımında önemli azalma**
- **Ses kalitesinde iyileşme veya en azından aynı seviyede kalma**

### Riskler ve Önlemler

1. **Token Limit Aşımı:**
   - **Risk:** Çok uzun chunk'lar token limitini aşabilir
   - **Önlem:** 800 karakter güvenli bir üst sınır, monitoring ekle

2. **Ses Kalitesi:**
   - **Risk:** Daha uzun chunk'lar kaliteyi etkileyebilir
   - **Önlem:** Test ve doğrulama, gerekirse `max_chars`'ı düşür

3. **Backward Compatibility:**
   - **Risk:** Mevcut projeler etkilenebilir
   - **Önlem:** Yeni projeler için geçerli, mevcut projeler olduğu gibi kalır

---

## 📚 Referanslar

- **Kod Dosyaları:**
  - `backend/app/ai/text_processor.py` - Chunk oluşturma mantığı
  - `backend/app/routers/projects.py` - Proje oluşturma ve chunking
  - `backend/app/services/audio_service.py` - TTS işleme
  - `scripts/test_chunking.py` - Test scripti

- **Dokümantasyon:**
  - XTTS v2 Token Limit: [Coqui TTS Documentation](https://github.com/coqui-ai/TTS)
  - Spacy Sentence Segmentation: [Spacy Documentation](https://spacy.io/usage/linguistic-features#sbd)

---

**Rapor Tarihi:** 2024  
**Hazırlayan:** AI Assistant  
**Versiyon:** 1.0

