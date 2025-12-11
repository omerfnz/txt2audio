# Proje Analiz Raporu

**Tarih:** 11 Aralık 2025  
**Kapsam:** Backend, Frontend, CLI/SH scriptleri, `app.log`

## 1) Log Gözlemleri (`app.log`)
- İki kitap işlenmiş: ilk parti “Carmilla by Joseph Sheridan Le Fanu”, ikinci parti “The Canterville Ghost”. Her iki süreç de tamamlanmış; uyarılar sonrası retry ile toparlanmış.
- Tekrarlayan uyarılar: `END-OF-FILE SILENCE DETECTED!` (ör. chunk 11 ve 85). Retry parametre ayarıyla 2. denemede başarı sağlanmış.
- Log satırları iki kez yazılıyor (aynı zaman damgasıyla ikili kayıt). Bu, logger’ın iki kez konfigüre edilmesinden kaynaklı (aşağıda bulgu).
- Dosya ~270 kB ve hızla büyüyor; log rotasyonu yok.

## 2) Kritik / Hata Bulguları
- **CORS yanlış yapılandırma (tarayıcıda başarısız/uyumsuz cevap riski):** `allow_origins` listesinde `*` varken `allow_credentials=True` kullanılıyor. Tarayıcılar bu kombinasyonda credential’lı isteğe izin vermez, bazı ortamlarda baştan hata verir.
```
24:31:backend/app/main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)
```
- **Çift logger tanımı → çift log satırı ve gereksiz I/O:** Aynı `ai_audiobook_studio` logger’ı hem `core/logging.py` hem `core/logger.py` içinde handler’larla kuruluyor; böylece her event iki kez yazılıyor, log dosyası şişiyor.
```
6:35:backend/app/core/logging.py
LOGS_DIR = settings.BASE_DIR / "logs"
LOGS_DIR.mkdir(exist_ok=True)
...
logger = logging.getLogger("ai_audiobook_studio")
logger.setLevel(logging.INFO)
...
logger.addHandler(console_handler)
...
logger.addHandler(file_handler)
```
```
10:66:backend/app/core/logger.py
def setup_logger(...):
    logger = logging.getLogger(name)
    logger.setLevel(level)
    ...
    logger.addHandler(console_handler)
...
default_logger = setup_logger(
    "ai_audiobook_studio",
    log_file=str(DEFAULT_LOG_FILE),
    level=logging.INFO,
)
```
- **Model yolu çalışma dizinine bağlı:** XTTS engine model cache’i `os.getcwd()` tabanlı ayarlanıyor; servis farklı dizinden başlarsa cache/indirme yanlış yere gider veya bulunamaz.
```
95:104:backend/app/ai/tts_engine.py
self.model_path = os.path.join(os.getcwd(), "storage", "models")
os.environ["TTS_HOME"] = self.model_path
```

## 3) Frontend Bulguları
- **API/WS adresleri ortama göre değişmiyor:** Host/port `4173→8000` replace mantığıyla yazılmış, reverse-proxy, farklı port veya HTTPS altında kırılabilir. Ortam değişkeniyle (örn. `VITE_API_URL`, `VITE_WS_URL`) çözülmeli.
```
5:8:frontend/src/api/client.ts
const API_BASE = window.location.hostname === 'localhost' 
  ? "http://localhost:8000/api"
  : `${window.location.protocol}//${window.location.hostname.replace('4173', '8000')}/api`;
```
```
11:18:frontend/src/hooks/useWebSocket.ts
if (window.location.hostname === 'localhost') {
  return 'ws://localhost:8000/api/ws';
}
const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
const host = window.location.hostname.replace('4173', '8000');
return `${protocol}//${host}/api/ws`;
```

## 4) Script Bulguları
- `setup-all.sh` otomatik `apt-get`/`sudo` deniyor; izinsiz ortamlarda ve sizin tercih ettiğiniz “sistem geneline kurma” kuralıyla çelişiyor, CI’de de kırılabilir. Kullanıcıya sadece komut önerisi vermek daha güvenli.
- `backend/start-backend.sh`’de `set -e` yok, `venv` yoksa sessizce başarısız olabilir.
```
1:9:backend/start-backend.sh
#!/bin/bash

echo "Activating venv..."
source venv/bin/activate
...
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## 5) Önerilen Aksiyonlar (öncelik sırası)
**Critical**
- CORS’u sabitle: `allow_origins`’i somut domain/port listesiyle sınırla; wildcard’ı çıkar ya da `allow_credentials=False` yap.
- Logger’ı tek yerden kur: `core/logging.py` veya `core/logger.py`’den birini seç, diğerini kaldır; handler tekrarını engelle. Log rotasyonu ekle (örn. `RotatingFileHandler`).

**High**
- Model yolu için mutlak, konfigüre edilebilir bir baz kullan (`settings.MODELS_DIR`); `os.getcwd()` bağımlılığını kaldır.
- Frontend API/WS adreslerini `.env` temelli yap (`VITE_API_URL`, `VITE_WS_URL`), port replace mantığını bırak; HTTPS’de `wss` zorunluluğunu otomatik ayarla.

**Medium**
- `setup-all.sh`’de paket kurulumunu otomatiğe bağlamadan, uyarı/rehber moduna çek; kullanıcıya manuel komut öner.
- `start-backend.sh`’ye `set -euo pipefail`, `venv` kontrolü ve hata mesajı ekle.
- `app.log` için rotasyon veya günlük klasörü (örn. `backend/logs/`) tanımla; disk büyümesini sınırlamak için 10–20 MB rotasyon uygulanabilir.

## 6) İzlenmesi Gerekenler
- TTS’te “END-OF-FILE SILENCE” uyarıları seyrek de olsa devam ediyor; gerekirse retry parametrelerini (temp/speed) ayar dosyasına taşıyıp UI’dan değiştirilebilir.
- Log büyüme hızı ve çift kayıt problemi düzeldikten sonra gürültü seviyesi yeniden ölçülmeli.

