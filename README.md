# 🎙️ AI Audiobook Studio

Modern bir sesli kitap oluşturma uygulaması. TXT/EPUB dosyalarınızı referans ses ile profesyonel kalitede sesli kitaba dönüştürün.

## 🚀 Özellikler

- ✅ **Ses Klonlama**: XTTS v2 ile 6-10 saniyelik referans ses kullanarak birebir ses klonlama
- ✅ **Optimize Edilmiş Performans**: FP16 (Half Precision) ve Async Locking ile hızlı ve hatasız üretim
- ✅ **Akıllı Metin İşleme**: Spacy NLP ile metni anlamlı cümlelere bölme
- ✅ **Gelişmiş Sayı Normalizasyonu**: Virgüllü büyük sayılar (140,000), ondalıklar, para birimleri doğru okunur ⭐ YENİ
- ✅ **Canlı İzleme**: WebSocket ile gerçek zamanlı ilerleme takibi
- ✅ **GPU/CPU Desteği**: Hem CPU hem de CUDA GPU desteği (T4 ve üzeri optimize)
- ✅ **Modern UI**: React + Tailwind CSS ile tasarlanmış kullanıcı dostu arayüz

## 📋 Gereksinimler

### Yazılım
- **Python**: 3.10 veya üzeri
- **Node.js**: 16 veya üzeri
- **espeak-ng**: TTS için gerekli
- **ffmpeg**: Ses birleştirme için gerekli

### Donanım
- **GPU Mode**: NVIDIA GPU (4GB+ VRAM). Tesla T4, RTX 30xx/40xx önerilir.
- **CPU Mode**: En az 8 GB RAM (Yavaş çalışır)

## 🔧 Kurulum

### 1. Sistem Bağımlılıkları (İlk Kez)

**Windows:**
```powershell
winget install eSpeak-NG.eSpeak-NG
winget install Gyan.FFmpeg
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get update
sudo apt-get install -y espeak-ng ffmpeg
```

### 2. Projeyi Kur

Windows:
```cmd
.\setup-all.cmd
```

Linux/Mac:
```bash
chmod +x setup-all.sh
./setup-all.sh
```

Bu komut sanal ortamı kurar, bağımlılıkları yükler ve modeli hazırlar.

## 🎬 Başlatma

Kurulum tamamlandıktan sonra uygulamayı başlatmak için:

**Windows:**
```cmd
.\start_app.cmd
```
*(setup-all.cmd tarafından oluşturulur)*

**Linux/Mac:**
```bash
chmod +x start.sh
./start.sh
```

- Backend: `http://localhost:8000`
- Frontend: `http://localhost:5173`

## ⚡ Performans Optimizasyonları (Güncel)

Bu proje, XTTS v2 modelinin kararlılığı ve hızı için özel optimizasyonlar içerir:

1.  **Async Locking**: GPU erişimi seri hale getirilerek `device-side assert` ve bellek çakışmaları %100 önlenmiştir.
2.  **Native FP16**: DeepSpeed yerine PyTorch native FP16 kullanılarak Tesla T4 gibi kartlarda 2x hız artışı sağlanmıştır.
3.  **No-DeepSpeed**: XTTS ile uyumsuzluk yaratan DeepSpeed modülleri devre dışı bırakılmıştır.
4.  **Auto-Recovery**: OOM (Out of Memory) durumlarında otomatik bellek temizliği yapılır.
5.  **⭐ Gelişmiş Sayı Normalizasyonu (YENİ)**: Virgüllü büyük sayılar (140,000 → "one hundred and forty thousand"), ondalıklar, para birimleri ve sıra sayıları XTTS için optimize edildi. Detaylar: [`XTTS_SAYI_COZUMU_TR.md`](XTTS_SAYI_COZUMU_TR.md)

## 📁 Proje Yapısı

```
txt2audio/
├── backend/              # FastAPI + AI Logic
│   ├── app/
│   │   ├── core/        # Config (Pydantic) & Logging
│   │   ├── ai/          # TTS Engine & Text Processing
│   │   ├── services/    # Business Logic
│   │   └── main.py      # App Entry Point
│   └── storage/         # Models & Outputs
│
├── frontend/            # React + TypeScript + Vite
│
├── scripts/             # Yardımcı araçlar
├── setup-all.sh         # Linux kurulum scripti
├── setup-all.cmd        # Windows kurulum scripti
└── start.sh             # Başlatma scripti
```

## 📝 Lisans

Bu proje Coqui TTS lisansına tabidir (CPML). Ticari kullanım için lisans gereklidir.
