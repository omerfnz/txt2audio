# 📋 Proje Görev Listesi (Task List)

Bu dosya, projenin adım adım ilerleyişini takip etmek için oluşturulmuştur. Her adım tamamlandığında işaretlenecek ve bir sonraki adıma geçilmeden önce kullanıcı onayı alınacaktır.

## 🟢 Faz 1: Hazırlık ve Altyapı
- [x] **Adım 1.1:** Proje klasör yapısının (Backend & Frontend) oluşturulması.
- [x] **Adım 1.2:** Backend için Python sanal ortamının (venv) kurulması ve `.gitignore` dosyasının oluşturulması.
- [x] **Adım 1.3:** Gerekli kütüphanelerin (`requirements.txt`) belirlenmesi (CPU/GPU uyumlu Torch, FastAPI, Coqui-TTS vb.) ve yüklenmesi.

## 🟡 Faz 2: Backend Geliştirme (FastAPI & AI)
- [x] **Adım 2.1:** Veritabanı modellerinin (SQLAlchemy) ve bağlantı ayarlarının (`database.db`) yapılması.
- [x] **Adım 2.2:** Spacy NLP entegrasyonu (Metin bölme/Chunking servisi).
- [x] **Adım 2.3:** TTS Motoru Wrapper'ının yazılması.
    - *Detay:* CPU/GPU seçimine göre cihaz ataması yapabilmeli.
    - *Detay:* Modelleri `storage/models` altına indirmeli.
- [x] **Adım 2.4:** API Endpoint'lerinin oluşturulması (Upload, Process, Status).
- [x] **Adım 2.5:** WebSocket entegrasyonu (İlerleme çubuğu için).

## 🔵 Faz 3: Frontend Geliştirme (React & UI)
- [x] **Adım 3.1:** React (Vite + TS) projesinin oluşturulması ve Tailwind CSS kurulumu.
- [x] **Adım 3.2:** Temel Layout ve Bileşenlerin (Sidebar, FileUpload, Player) kodlanması.
- [x] **Adım 3.3:** İşlemci Seçimi (CPU/GPU) bileşeninin eklenmesi.
- [x] **Adım 3.4:** API ve WebSocket servislerinin frontend'e bağlanması.

## 🟣 Faz 4: Test ve Optimizasyon
- [x] **Adım 4.1:** WebSocket bağlantı sorunları düzeltildi.
    - Path uyumsuzluğu giderildi (`/api/ws`)
    - Background task execution model optimize edildi
- [x] **Adım 4.2:** TTS Engine optimizasyonları yapıldı.
    - Deprecated `gpu` parametresi kaldırıldı
    - espeak-ng otomatik tespit iyileştirildi
    - Coqui TTS lisans onayı otomatikleştirildi
    - VRAM optimizasyonları eklendi (düşük VRAM uyarısı, sık memory cleanup)
- [x] **Adım 4.3:** Frontend lint hataları düzeltildi.
- [x] **Adım 4.4:** espeak-ng kurulumu tamamlandı.
- [x] **Adım 4.5:** README ve sistem kontrol script'i oluşturuldu.

## 🟠 Faz 5: Refactoring & Mimari İyileştirmeler (BAŞLIYORUZ)
> **Hedef:** Kod tabanını modüler, test edilebilir ve bakımı kolay hale getirmek.

### Backend Refactoring
- [x] **Adım 5.1:** Konfigürasyon Yönetimi
    - `backend/app/core/config.py` oluşturulacak.
    - Hardcoded path'ler (`storage/`, `models/`) ve ayarlar buraya taşınacak.
- [x] **Adım 5.2:** Service Layer Ayrımı
    - `backend/app/services/` klasörü oluşturulacak.
    - `audio_service.py`: Merge ve process mantığı buraya.
    - `project_service.py`: DB işlemleri buraya.
    - `websocket.py`: WebSocket manager buraya.
- [x] **Adım 5.3:** Router Ayrımı
    - `backend/app/routers/` klasörü oluşturulacak.
    - `endpoints.py` parçalanacak: `projects.py`, `audio.py`, `websocket.py`.
- [x] **Adım 5.4:** Global Hata Yönetimi & Loglama
    - Global Exception Handler eklenecek.
    - `print()` yerine `logging` modülü entegre edilecek.

### Frontend Refactoring
- [x] **Adım 5.5:** View Ayrımı
    - `App.tsx` içindeki görünümler `views/UploadView.tsx` ve `views/ProjectView.tsx` olarak ayrılacak.
- [x] **Adım 5.6:** Custom Hooks
    - WebSocket ve proje durumu mantığı `hooks/useProjectStatus.ts` içine taşınacak.
    - `types/index.ts` oluşturulacak.

## 🏁 Proje Durumu
- [x] **Backend:** Çalışıyor ✅
- [x] **Frontend:** Çalışıyor ✅
- [x] **WebSocket:** Çalışıyor ✅
- [x] **TTS Engine:** Optimize edildi ✅
- [x] **Refactoring:** Tamamlandı ✅
- [ ] **GPU Test:** Bekleniyor (kullanıcı testi gerekli)

## 📝 Notlar
- **VRAM Uyarısı:** GPU modunda 2.15 GB VRAM düşüktür. Büyük metinlerde sorun yaşanabilir. CPU modu önerilir.
- **Model İndirme:** İlk çalıştırmada XTTS v2 modeli (~2 GB) indirilecektir, bu normaldir.
