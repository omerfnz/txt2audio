# 📋 TXT2AUDIO Optimizasyon Görev Listesi
## Kurumsal Kod Yapısı - Adım Adım Uygulama Planı

**Oluşturulma:** Aralık 2024  
**Hedef:** Kusursuz çalışan, production-ready kod  
**Yöntem:** Her adım onay alınarak ilerlenecek

---

## 🎯 Öncelik Sıralaması

| Öncelik | Görev | Neden Öncelikli |
|---------|-------|-----------------|
| 🔴 P0 | Devam Et (Resume) Özelliği | Yarıda kalan işler için kritik |
| 🟠 P1 | FP16 Half Precision | En yüksek hızlanma etkisi |
| 🟠 P1 | Model Warm-up | Kolay, hızlı kazanım |
| 🟡 P2 | torch.compile | Orta etki, düşük risk |
| 🟡 P2 | Speaker Embedding Cache | Aynı ses projelerinde etkili |
| 🟢 P3 | Concurrent Processing | Yüksek etki, orta karmaşıklık |
| 🟢 P3 | DeepSpeed (Linux) | Platform bağımlı |

---

## 📌 GÖREV 1: Devam Et (Resume) Özelliği ✅
**Öncelik:** 🔴 P0 - KRİTİK  
**Tahmini Süre:** 4-6 saat  
**Risk:** Düşük  
**Durum:** ✅ TAMAMLANDI

### 1.1 Problem Analizi
- [ ] Mevcut iptal (cancel) mekanizmasını incele
- [ ] Yarıda kalan projelerin durumunu analiz et
- [ ] Hangi chunk'ların işlendiğini tespit mekanizması

### 1.2 Backend Değişiklikleri

#### 1.2.1 Database Model Güncellemesi (`db/models.py`)
- [ ] `Project` modeline yeni alanlar ekle:
  - `last_processed_chunk_index: int` - Son işlenen chunk indeksi
  - `resume_count: int` - Kaç kez devam edildi (debug için)
  - `last_error: str` - Son hata mesajı (opsiyonel)
- [ ] Migration stratejisi belirle (SQLite için)

#### 1.2.2 API Endpoint (`routers/audio.py` veya `routers/projects.py`)
- [ ] `POST /api/projects/{id}/resume` endpoint'i ekle
- [ ] Resume işlemi için validasyon kuralları:
  - Proje durumu "processing", "failed", veya "cancelled" olmalı
  - En az bir işlenmemiş chunk olmalı
- [ ] Response modeli tanımla

#### 1.2.3 Audio Service Güncellemesi (`services/audio_service.py`)
- [ ] `resume_audio_task()` fonksiyonu ekle
- [ ] Mevcut `process_audio_task()` fonksiyonunu refactor et:
  - İşlenmiş chunk'ları atla (zaten var ama kontrol et)
  - `last_processed_chunk_index` güncelle
  - Hata durumunda durumu kaydet
- [ ] Ortak kod için yardımcı fonksiyonlar çıkar

#### 1.2.4 WebSocket Bildirimleri (`services/websocket.py`)
- [ ] "resume_started" mesaj tipi ekle
- [ ] "resume_progress" mesaj tipi ekle (mevcut progress'ten farklı mı olmalı?)

### 1.3 Frontend Değişiklikleri

#### 1.3.1 API Client (`api/client.ts`)
- [ ] `resumeProject(projectId: number)` fonksiyonu ekle
- [ ] Hata handling

#### 1.3.2 UI Bileşenleri
- [ ] `ProjectView.tsx` - "Devam Et" butonu ekle
  - Görünürlük: cancelled, failed, veya yarıda kalmış projeler için
  - Disabled durumu: processing sırasında
- [ ] Buton tasarımı (renk, ikon, konum)
- [ ] Onay dialog'u gerekli mi?

#### 1.3.3 WebSocket Handler (`hooks/useWebSocket.ts`)
- [ ] Resume event'lerini handle et

### 1.4 Test Senaryoları
- [ ] Senaryo 1: İptal edilen projeyi devam ettir
- [ ] Senaryo 2: Sunucu çökmesi sonrası devam
- [ ] Senaryo 3: Birden fazla kez devam ettirme
- [ ] Senaryo 4: Tüm chunk'lar işlenmişken devam etme denemesi
- [ ] Senaryo 5: Processing sırasında devam etme denemesi (engellenmeli)

### 1.5 Kararlaştırılan Tasarım ✅
1. **Başarısız chunk'lar:** 3 kez retry → hala başarısızsa atla
2. **Merge sonrası:** Devam mümkün değil (dosyalar siliniyor)
3. **Resume butonu:** ProjectView'da ana buton
4. **Progress:** Kaldığı yerden devam (%45'te kaldıysa %45'ten)

---

## 📌 GÖREV 2: FP16 Half Precision Optimizasyonu ✅
**Öncelik:** 🟠 P1  
**Tahmini Süre:** 2-3 saat  
**Risk:** Düşük  
**Durum:** ✅ TAMAMLANDI  
**Bağımlılık:** Görev 1 tamamlandıktan sonra

### 2.1 Hazırlık
- [ ] Mevcut `tts_engine.py` kodunu yedekle
- [ ] XTTS v2'nin FP16 uyumluluğunu doğrula
- [ ] Test için örnek ses dosyası hazırla

### 2.2 Kod Değişiklikleri (`ai/tts_engine.py`)

#### 2.2.1 Konfigürasyon
- [ ] `config.py`'a FP16 ayarı ekle: `USE_FP16 = True`
- [ ] Environment variable desteği: `TTS_USE_FP16`

#### 2.2.2 TTSEngine Sınıfı
- [ ] `__init__`'e `use_fp16` parametresi ekle
- [ ] `load_model()` içinde FP16 dönüşümü
- [ ] `generate_audio()` içinde `autocast` context manager
- [ ] Fallback mekanizması (FP16 başarısız olursa FP32)

### 2.3 Test ve Doğrulama
- [ ] Ses kalitesi karşılaştırması (FP32 vs FP16)
- [ ] VRAM kullanımı ölçümü
- [ ] Inference süresi ölçümü
- [ ] Hata durumları testi

### 2.4 Sorular (Onay Gerekli)
1. **FP16 varsayılan olarak açık mı olsun?**
   - A) Evet, GPU varsa otomatik
   - B) Hayır, config'den manuel açılsın
   - C) GPU VRAM'e göre otomatik karar

---

## 📌 GÖREV 3: Model Warm-up ✅
**Öncelik:** 🟠 P1  
**Tahmini Süre:** 1-2 saat  
**Risk:** Çok Düşük  
**Durum:** ✅ TAMAMLANDI  
**Bağımlılık:** Görev 2 ile paralel yapılabilir

### 3.1 Kod Değişiklikleri (`ai/tts_engine.py`)
- [ ] `_warmup_model()` metodu ekle
- [ ] Warm-up için varsayılan referans ses seç
- [ ] Warm-up başarı/başarısızlık logging
- [ ] Warm-up süresini ölç ve logla

### 3.2 Konfigürasyon
- [ ] `config.py`'a warm-up ayarı: `WARMUP_ON_STARTUP = True`
- [ ] Warm-up text: "Hello, this is a warm up test."

### 3.3 Test
- [ ] İlk chunk süresi ölçümü (warm-up öncesi/sonrası)
- [ ] Warm-up hatası durumunda sistemin çalışması

---

## 📌 GÖREV 4: torch.compile Optimizasyonu ✅
**Öncelik:** 🟡 P2  
**Tahmini Süre:** 2-3 saat  
**Risk:** Düşük-Orta  
**Durum:** ✅ TAMAMLANDI  
**Bağımlılık:** Görev 2 tamamlandıktan sonra

### 4.1 Hazırlık
- [ ] PyTorch versiyonu kontrol (>=2.0 gerekli)
- [ ] Lightning AI ortamında test
- [ ] Windows uyumluluğu kontrol (development için)

### 4.2 Kod Değişiklikleri
- [ ] `load_model()` içinde `torch.compile()` entegrasyonu
- [ ] Compile mode seçimi: `reduce-overhead` veya `max-autotune`
- [ ] Fallback mekanizması
- [ ] İlk çalıştırma uyarısı (derleme süresi)

### 4.3 Konfigürasyon
- [ ] `USE_TORCH_COMPILE = True`
- [ ] `TORCH_COMPILE_MODE = "reduce-overhead"`

### 4.4 Sorular (Onay Gerekli)
1. **Windows'ta torch.compile aktif olsun mu?**
   - A) Evet
   - B) Hayır, sadece Linux
   - C) Opsiyonel (config'den)

---

## 📌 GÖREV 5: Speaker Embedding Cache ✅
**Öncelik:** 🟡 P2  
**Tahmini Süre:** 2-3 saat  
**Risk:** Düşük  
**Durum:** ✅ TAMAMLANDI  
**Bağımlılık:** Görev 2 tamamlandıktan sonra

### 5.1 Kod Değişiklikleri (`ai/tts_engine.py`)
- [ ] `_speaker_cache` dictionary ekle
- [ ] `_get_speaker_embedding()` metodu
- [ ] Cache invalidation stratejisi (dosya değişikliği)
- [ ] Cache boyutu limiti (memory leak önleme)

### 5.2 Optimizasyon
- [ ] LRU cache kullanımı
- [ ] Cache hit/miss logging
- [ ] Memory kullanımı monitoring

### 5.3 Sorular (Onay Gerekli)
1. **Cache'i ne zaman temizleyelim?**
   - A) Her proje bitiminde
   - B) Belirli boyutu aşınca (LRU)
   - C) Manuel (API endpoint)
   - D) Asla (session boyunca)

---

## 📌 GÖREV 6: Concurrent Processing (Paralel Chunk İşleme) ✅
**Öncelik:** 🟢 P3  
**Tahmini Süre:** 6-8 saat  
**Risk:** Orta  
**Durum:** ✅ TAMAMLANDI  
**Bağımlılık:** Görev 1-5 tamamlandıktan sonra

### 6.1 Mimari Tasarım
- [ ] Concurrent chunk sayısı belirleme (T4: 2 önerilir)
- [ ] Queue-based işleme vs batch processing
- [ ] Error handling stratejisi
- [ ] Progress reporting (concurrent için)

### 6.2 Kod Değişiklikleri (`services/audio_service.py`)
- [ ] `ChunkProcessor` sınıfı oluştur
- [ ] `asyncio.Semaphore` ile concurrent limit
- [ ] `ThreadPoolExecutor` entegrasyonu
- [ ] Batch-level retry mekanizması

### 6.3 Konfigürasyon
- [ ] `MAX_CONCURRENT_CHUNKS = 2`
- [ ] VRAM'e göre dinamik ayarlama (opsiyonel)

### 6.4 Test
- [ ] Memory leak testi
- [ ] Concurrent error handling
- [ ] Progress doğruluğu
- [ ] Chunk sırası korunması

### 6.5 Sorular (Onay Gerekli)
1. **Concurrent işlem başarısız olursa?**
   - A) Tüm batch'i tekrar dene
   - B) Sadece başarısız chunk'ı tekrar dene
   - C) Sequential mode'a düş

2. **VRAM yetersizse ne olsun?**
   - A) Otomatik concurrent=1'e düş
   - B) Hata ver ve dur
   - C) Kullanıcıya sor

---

## 📌 GÖREV 7: DeepSpeed Entegrasyonu (Lightning AI)
**Öncelik:** 🟢 P3  
**Tahmini Süre:** 4-6 saat  
**Risk:** Orta  
**Durum:** ⏳ Beklemede  
**Bağımlılık:** Görev 6 tamamlandıktan sonra  
**Platform:** Sadece Linux/Lightning AI

### 7.1 Hazırlık
- [ ] DeepSpeed kurulumu (`requirements.txt` güncelle)
- [ ] Lightning AI ortamında test
- [ ] XTTS v2 + DeepSpeed uyumluluk kontrolü

### 7.2 Kod Değişiklikleri
- [ ] `__init__`'e DeepSpeed kontrolü
- [ ] `load_model()` içinde DeepSpeed inference engine
- [ ] Platform detection (Linux only)
- [ ] Fallback mekanizması

### 7.3 Konfigürasyon
- [ ] `USE_DEEPSPEED = True`
- [ ] `DEEPSPEED_DTYPE = "fp16"`

---

## 📌 GÖREV 8: GPU Monitoring ve Güvenlik ✅
**Öncelik:** 🟢 P3  
**Tahmini Süre:** 2-3 saat  
**Risk:** Düşük  
**Durum:** ✅ TAMAMLANDI  
**Bağımlılık:** Tüm GPU görevleri ile paralel

### 8.1 Monitoring Fonksiyonları
- [ ] `get_gpu_stats()` - VRAM, utilization, temperature
- [ ] `check_gpu_throttling()` - Sıcaklık kontrolü
- [ ] `monitor_vram()` - Memory kullanımı

### 8.2 Güvenlik Mekanizmaları
- [ ] OOM (Out of Memory) handling
- [ ] Throttling algılama ve uyarı
- [ ] Otomatik memory cleanup

### 8.3 Logging
- [ ] GPU stats her chunk'ta logla
- [ ] Anomali algılama

---

## 🔄 Genel Görevler (Tüm Adımlarda)

### Her Görev İçin Yapılacaklar
- [ ] Kod değişikliklerinden önce mevcut kodu yedekle
- [ ] Lint kontrolü (`ruff` veya `flake8`)
- [ ] Type hints ekle
- [ ] Docstring'ler yaz
- [ ] Error handling kontrol et
- [ ] Logging ekle
- [ ] Test yaz (mümkünse)

### Kod Standartları
- [ ] PEP 8 uyumu
- [ ] Type hints zorunlu
- [ ] Docstring formatı: Google style
- [ ] Max satır uzunluğu: 100 karakter
- [ ] Import sıralaması: isort

---

## 📊 İlerleme Takibi

| Görev | Durum | Başlangıç | Bitiş | Notlar |
|-------|-------|-----------|-------|--------|
| Görev 1: Resume | ✅ Tamamlandı | Aralık 2024 | Aralık 2024 | DB + API + Service + Frontend |
| Görev 2: FP16 | ✅ Tamamlandı | Aralık 2024 | Aralık 2024 | Config + TTSEngine (VRAM>=8GB otomatik) |
| Görev 3: Warm-up | ✅ Tamamlandı | Aralık 2024 | Aralık 2024 | CUDA kernel preload + dummy inference |
| Görev 4: torch.compile | ❌ İptal | - | - | XTTS v2 uyumsuz - CUDA errors |
| Görev 5: Speaker Cache | ⏸️ Devre Dışı | Aralık 2024 | - | Kod hazır, config'de kapalı (test sonrası açılabilir) |
| Görev 6: Concurrent | ❌ İptal | - | - | XTTS v2 thread-safe değil, GPU çakışması |
| Görev 7: DeepSpeed | ⏸️ Atlandı | - | - | İleride eklenebilir |
| Görev 8: Monitoring | ✅ Tamamlandı | Aralık 2024 | Aralık 2024 | Temp + VRAM izleme |

**Son Durum (7 Aralık 2024):**
- ✅ **FP16 Aktif:** VRAM >= 8GB'de otomatik açılıyor (%40-50 hızlanma)
- ✅ **Warmup Aktif:** CUDA kernel preload (ilk chunk hızlanması)
- ❌ **Concurrent Kapalı:** XTTS v2 thread-safe değil (KRİTİK: AÇMAYIN!)
- ❌ **torch.compile Kapalı:** XTTS v2 ile uyumsuz
- ❌ **Speaker Cache Kapalı:** Şimdilik kapalı (test sonrası açılabilir)

**CUDA Assertion Hatası Çözümü:**
- Problem: `srcIndex < srcSelectDimSize` → 2 concurrent chunk GPU çakışması
- Çözüm: `USE_CONCURRENT_PROCESSING = False` ve `MAX_CONCURRENT_CHUNKS = 1`
- Durum: Config güncellendi, tek chunk modunda çalışacak

---

## ✅ Kararlaştırılan Tasarım Seçimleri

### Görev 1: Resume Özelliği
1. ✅ **Başarısız chunk'lar:** 3 kez retry, hala başarısızsa atla ve devam et
2. ✅ **Merge sonrası:** Devam mümkün değil (chunk dosyaları siliniyor)
3. ✅ **Resume butonu:** ProjectView'da ana buton olarak
4. ✅ **Progress:** Kaldığı yerden devam (%45'te kaldıysa %45'ten başlar)

### Görev 2: FP16
5. ✅ **FP16:** GPU VRAM'e göre otomatik (8GB+ ise açık, altında kapalı)

### Görev 4: torch.compile
6. ⏳ **Windows:** Henüz karar verilmedi (Görev 4'te sorulacak)

### Görev 5: Speaker Cache
7. ✅ **Cache:** LRU Cache (max 10 speaker, ~1GB limit, otomatik temizlik)

### Görev 6: Concurrent Processing
8. ⏳ **Başarısızlık:** Henüz karar verilmedi (Görev 6'da sorulacak)
9. ⏳ **VRAM yetersiz:** Henüz karar verilmedi (Görev 6'da sorulacak)

---

## 📝 Notlar

- Her kod değişikliği öncesi kullanıcı onayı alınacak
- Chunk boyutu (400 karakter) SABİT kalacak
- Tüm değişiklikler geriye uyumlu olmalı
- Production-ready, kurumsal kod kalitesi hedefleniyor
- Lightning AI + T4 GPU ortamı öncelikli

---

**Son Güncelleme:** Aralık 2024  
**Durum:** Görev listesi oluşturuldu, kullanıcı onayı bekleniyor

