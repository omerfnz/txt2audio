# 🎙️ AI Audiobook Studio

Modern bir sesli kitap oluşturma uygulaması. TXT/EPUB dosyalarınızı referans ses ile profesyonel kalitede sesli kitaba dönüştürün.

## 🚀 Özellikler

- ✅ **Ses Klonlama**: XTTS v2 ile 6-10 saniyelik referans ses kullanarak birebir ses klonlama
- ✅ **Akıllı Metin İşleme**: Spacy NLP ile metni anlamlı cümlelere bölme
- ✅ **Canlı İzleme**: WebSocket ile gerçek zamanlı ilerleme takibi
- ✅ **GPU/CPU Desteği**: Hem CPU hem de CUDA GPU desteği
- ✅ **Modern UI**: React + Tailwind CSS ile tasarlanmış kullanıcı dostu arayüz
- ✅ **Referans Sesler**: Hazır İngilizce referans sesleri veya kendi sesinizi yükleyebilme

## 📋 Gereksinimler

### Yazılım
- **Python**: 3.10 veya üzeri
- **Node.js**: 16 veya üzeri
- **espeak-ng**: TTS için gerekli (otomatik kurulum talimatları aşağıda)

### Donanım
- **CPU Mode**: En az 8 GB RAM
- **GPU Mode**: CUDA destekli GPU + en az 4 GB VRAM (önerilen: 6 GB+)

## 🔧 Kurulum

### 1. espeak-ng Kurulumu (İlk Kez)
```bash
winget install eSpeak-NG.eSpeak-NG
```

### 2. Projeyi Kur
```bash
# İlk kurulum için
.\setup-all.cmd
```

Bu komut:
- Backend için Python sanal ortamı oluşturur
- Tüm Python bağımlılıklarını yükler
- Frontend için npm paketlerini yükler
- Spacy modelini indirir

## 🎬 Kullanım

### Quick Start (Önerilen)
```bash
.\quick-start.cmd
```

Bu komut:
- Backend'i `http://localhost:8000` adresinde başlatır
- Frontend'i `http://localhost:5173` adresinde başlatır
- Tarayıcınızı otomatik açar

### Manuel Başlatma

**Backend:**
```bash
cd backend
venv\Scripts\activate
set COQUI_TOS_AGREED=1
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Frontend:**
```bash
cd frontend
npm run dev
```

## 📁 Proje Yapısı

```
txt2audio/
├── backend/              # FastAPI + AI Logic
│   ├── app/
│   │   ├── ai/          # TTS Engine & Text Processor
│   │   ├── api/         # REST & WebSocket Endpoints
│   │   ├── db/          # Database Models & Session
│   │   └── main.py      # FastAPI App
│   ├── storage/         # Uploads, Outputs, Models
│   └── venv/            # Python Virtual Environment
│
├── frontend/            # React + TypeScript
│   ├── src/
│   │   ├── components/  # UI Components
│   │   ├── hooks/       # Custom React Hooks
│   │   ├── api/         # API Client
│   │   └── App.tsx      # Main App
│   └── package.json
│
├── quick-start.cmd      # Hızlı başlatma scripti
├── setup-all.cmd        # Kurulum scripti
└── clean.cmd            # Temizlik scripti
```

## 🎯 Önemli Yapılan Optimizasyonlar

### ✅ WebSocket Düzeltmeleri
- WebSocket endpoint URL'i düzeltildi (`/api/ws`)
- Background task execution model optimize edildi (asyncio.run yerine direct async)
- Bağlantı hatalarının düzeltilmesi

### ✅ TTS Engine İyileştirmeleri
- Deprecated `gpu` parametresi kaldırıldı, `.to(device)` kullanımına geçildi
- espeak-ng yolu otomatik tespiti geliştirildi (scoop, winget yolları eklendi)
- Coqui TTS lisans onayı otomatikleştirildi (`COQUI_TOS_AGREED=1`)
- Düşük VRAM uyarısı eklendi (< 4 GB)
- Progress bar görünür hale getirildi

### ✅ Memory Management
- GPU memory cleanup sıklığı artırıldı (her 5 chunk → her 3 chunk)
- Model yüklendikten sonra otomatik cache temizleme
- Düşük VRAM'li GPU'lar için optimize edildi

### ✅ Frontend Lint Düzeltmeleri
- Kullanılmayan değişkenler temizlendi (`isConnected`, `_error`)
- TypeScript strict mode uyumluluğu sağlandı

## 🐛 Bilinen Sorunlar ve Çözümler

### espeak-ng bulunamıyor
**Çözüm**: 
```bash
winget install eSpeak-NG.eSpeak-NG
```
Kurulumdan sonra terminal'i yeniden başlatın.

### GPU Memory (VRAM) yetersiz
**Çözüm**: 
- CPU modunda çalıştırın (frontend'de GPU checkbox'ını işaretlemeyin)
- Küçük metin parçaları ile test edin

### Model indirme çok uzun sürüyor
**Açıklama**: XTTS v2 modeli ilk çalıştırmada ~2 GB indirilir. Bu normal bir durumdur ve sadece bir kez olur.

## 📚 API Dökümantasyonu

Backend çalışırken otomatik API dökümantasyonuna erişebilirsiniz:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 🏗️ Teknoloji Stack'i

### Backend
- **FastAPI**: Modern, hızlı web framework
- **SQLAlchemy**: ORM ve database yönetimi
- **Coqui TTS**: XTTS v2 ses klonlama motoru
- **Spacy**: NLP ve metin işleme
- **PyTorch**: GPU/CPU compute

### Frontend
- **React 18**: UI library
- **TypeScript**: Type-safe JavaScript
- **Vite**: Build tool ve dev server
- **Tailwind CSS**: Utility-first CSS
- **Zustand**: State management
- **Axios**: HTTP client

## 📝 Lisans

Bu proje Coqui TTS'in lisansına tabidir. Ticari kullanım için Coqui'den lisans alınması gerekmektedir.
- Non-commercial: CPML (https://coqui.ai/cpml)
- Commercial: licensing@coqui.ai

## 🤝 Katkıda Bulunma

Pull request'ler hoş karşılanır. Büyük değişiklikler için lütfen önce bir issue açarak ne değiştirmek istediğinizi tartışın.

## 📧 İletişim

Sorularınız için issue açabilir veya projeyi fork edebilirsiniz.
