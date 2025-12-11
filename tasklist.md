# txt2audio İyileştirme Görevleri

1. [x] F5 TTS’yi tamamen kaldır, yalnızca XTTS kalsın.  
2. [x] Logger’ı tekilleştir; çift handlerı kaldır, sorunsuz log yazımı.  
3. [x] CORS’u sabitle; wildcard’ı kaldır, originleri env/sabit listeden besle.  
4. [x] XTTS model yolu için `settings.MODELS_DIR` kullan; `os.getcwd()` bağımlılığını kaldır, `TTS_HOME`’u buna ayarla.  
5. [x] Frontend API/WS URL’lerini `.env` tabanlı yap; port replace hack’ini kaldır.  
6. [x] Vite portlarını varsayılan (dev=5173, preview=4173) tut; `.env` ile özelleştirilebilir yap.  
7. [x] `setup-all.sh`’yi kılavuz moda çek (otomatik apt/sudo yok), venv/conda tarafsızlaştır.  
8. [x] `start-backend.sh`’yi `set -euo pipefail` ve env/venv/conda kontrolleriyle sertleştir.  
9. [ ] (Opsiyonel) Log rotasyonunu değerlendir; limit eklemeden sorunsuz yazımı doğrula.
