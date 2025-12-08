# F5-TTS Entegrasyon Görev Listesi

Bu dosya, `txt2audio` projesine F5-TTS (Flow Matching) modelini entegre etmek için izlenecek adımları içerir. Hedef, mevcut XTTS v2 yapısını bozmadan, ikinci bir seçenek olarak F5-TTS'i eklemektir.

## 1. Hazırlık ve Kurulum
- [ ] **F5-TTS Kütüphanesini Kur:** Mevcut `venv` ortamına `f5-tts` paketini ve gerekli bağımlılıkları ekle.
- [ ] **Uyumluluk Kontrolü:** Kurulum sonrası mevcut Coqui TTS'in bozulmadığını basit bir script ile test et.

## 2. Backend Geliştirme (Python/FastAPI)
- [ ] **Motor Sınıfı (`f5_engine.py`):** `backend/app/ai/` altında F5 modelini yönetecek singleton sınıfı oluştur.
    - Model yükleme (Load)
    - Ses sentezleme (Infer)
    - Bellek temizleme (Unload)
- [ ] **Model Yöneticisi (Model Manager):** XTTS ve F5 arasında geçiş yaparken VRAM'i boşaltacak mantığı `audio_service.py` veya yeni bir yönetici sınıfına ekle.
- [ ] **WebSocket Endpoint:** `backend/app/routers/websocket.py` dosyasına F5 için streaming desteği sunan `/ws/generate-f5` endpoint'ini ekle.

## 3. Frontend Geliştirme (React)
- [ ] **Model Seçici:** `Sidebar.tsx` veya `AdvancedSettings.tsx` içine "Model Seçimi" (XTTS v2 / F5-TTS) dropdown'ı ekle.
- [ ] **Hook Entegrasyonu:** Rehberdeki `useF5TTS` hook'unu `src/hooks/useF5TTS.ts` olarak projeye ekle.
- [ ] **Player Güncellemesi:** `Player.tsx` bileşenini, seçili modele göre davranacak şekilde güncelle (XTTS ise dosya, F5 ise stream).

## 4. Test ve Optimizasyon
- [ ] **Akış Testi:** WebSocket üzerinden sesin kesintisiz gelip gelmediğini test et.
- [ ] **VRAM Testi:** Modeller arası geçiş yaparken GPU belleğinin şişmediğini doğrula.
- [ ] **UI Testi:** Kullanıcı arayüzündeki geçişlerin sorunsuz olduğunu onayla.

