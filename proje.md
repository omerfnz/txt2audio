📂 MASTER PROMPT PACK: AI AUDIOBOOK STUDIO (XTTS v2)
Rol: Sen Kıdemli Full-Stack Yazılım Mühendisi ve AI Mimarisin. Görev: Aşağıdaki tüm teknik dokümanları (PRD, Tech Spec, UI/UX, DB Schema) analiz ederek, projenin tamamını eksiksiz kodlamanı istiyorum.

📄 DOKÜMAN 1: Ürün Gereksinim Dokümanı (PRD)
Proje Adı: AI Audiobook Studio Özet: Kullanıcıların TXT/EPUB dosyalarını yükleyip, kendi seçtikleri referans ses (WAV) ile profesyonel kalitede sesli kitaba dönüştürebilecekleri, modern arayüze sahip yerel (local) bir masaüstü uygulaması.

Temel Özellikler:

Proje Yönetimi: Farklı kitaplar için farklı projeler oluşturabilme.

Akıllı Metin İşleme: Spacy NLP kullanarak metni anlamlı cümlelere bölme.

Klonlama: 6-10 saniyelik referans ses ile birebir ses klonlama (XTTS v2).

Canlı İzleme: İşlenen cümleleri arayüzde anlık görme (WebSocket).

Audio Player: Üretilen sesleri parça parça veya bütün halinde dinleyebilme.

GPU/CPU Seçimi: Kullanıcı arayüzünden işlemin CPU mu yoksa GPU mu kullanılarak yapılacağı seçilebilmeli. Lokal testler için CPU, sunucu için GPU desteği.
GPU Optimizasyonu: GPU seçildiğinde VRAM taşmasını önleyen otomatik bellek temizliği.

🛠️ DOKÜMAN 2: Teknik Spesifikasyonlar (Mühendisler İçin)
1. Mimari (Architecture)
Proje Modern Monorepo yapısında olacaktır.

Backend: Python (FastAPI) - Tüm AI işlemleri ve API.

Frontend: React (Vite + TypeScript) - Kullanıcı arayüzü.

İletişim: REST API + WebSockets (İlerleme çubuğu için).

Veritabanı: SQLite (Yerel dosya tabanlı).

2. Backend Stack (Python 3.10+)
Core Framework: fastapi, uvicorn

AI Engine: coqui-tts (XTTS v2 Modeli)

NLP: spacy (Model: en_core_web_sm ve xx_ent_wiki_sm fallback ile)

Audio Processing: pydub, ffmpeg-python

System: torch (CPU ve CUDA desteği), gc (Garbage Collection).
Modeller: Proje dizini içinde `storage/models` klasörüne indirilecek.

3. Frontend Stack
Framework: React 18 (Vite ile oluşturulmuş).

Dil: TypeScript.

State Management: Zustand (Basit ve hızlı).

Styling: Tailwind CSS (Tüm stil işlemleri için).

HTTP Client: Axios.

Icons: Lucide React.

4. AI Logic (Önemli Kurallar)
Chunking: Metin asla tek seferde modele gönderilmemeli. NLP ile cümlelere bölünmeli, maksimum 250 karakterlik "Chunk"lar oluşturulmalı.

Memory Leak Prevention: Her 15 "Chunk" üretiminden sonra torch.cuda.empty_cache() ve gc.collect() çalıştırılmalı.

Silence Injection: Her cümle sonuna AudioSegment.silent(duration=350) eklenerek robotik akış engellenmeli.

🎨 DOKÜMAN 3: UI/UX & Tasarım Sistemi (Design System)
Tasarım "Dark Mode" odaklı, modern ve minimalist olmalıdır.

1. Renk Paleti (HEX Kodları)
Background (Zemin): #0f172a (Slate 900 - Çok koyu mavi/gri)

Surface (Kartlar/Paneller): #1e293b (Slate 800)

Primary (Ana Renk): #6366f1 (Indigo 500 - Butonlar ve vurgular için)

Secondary (İkincil): #10b981 (Emerald 500 - Başarı mesajları ve Play butonu için)

Text Main (Ana Metin): #f8fafc (Slate 50)

Text Muted (Pasif Metin): #94a3b8 (Slate 400)

Border (Çerçeveler): #334155 (Slate 700)

2. Tipografi (Typography)
Font Ailesi: Inter (Google Fonts'tan çekilecek) veya sistem varsayılanı sans-serif.

H1 Başlıklar: 24px, Bold, Tracking-tight.

Gövde Metni: 14px veya 16px, Regular.

Kod/Loglar: JetBrains Mono veya Fira Code.

3. Layout (Yerleşim)
Sol Panel (Sidebar): Genişlik 280px. Geçmiş projeler listesi. "Yeni Proje" butonu.

Orta Alan (Main):

Üst: Dosya yükleme (Drag & Drop), Referans Ses seçimi ve İşlemci Seçimi (CPU/GPU Toggle).

Orta: Metin önizleme (Textarea).

Alt: Log ekranı (Terminal görünümü).

Alt Bar (Player): Sabit (Fixed). Play/Pause, İlerleme çubuğu, İndir butonu.

🗄️ DOKÜMAN 4: Veritabanı Şeması (Database Schema)
Veritabanı olarak SQLite kullanılacak. database.db dosyasında saklanacak.

Tablo 1: projects

id (Integer, PK): Otomatik artan.

name (String): Kitap adı.

created_at (Datetime).

status (String): "processing", "completed", "failed".

text_path (String): Yüklenen TXT dosyasının yolu.

audio_path (String): Üretilen final MP3 dosyasının yolu.

voice_ref_path (String): Kullanılan referans sesin yolu.

Tablo 2: chunks (İşlenen parçalar)

id (Integer, PK).

project_id (Integer, FK -> projects.id).

index (Integer): Sıra numarası (0, 1, 2...).

text_content (String): O parçanın metni.

is_processed (Boolean): İşlendi mi?

chunk_audio_path (String): Parçanın geçici WAV yolu.

📂 DOKÜMAN 5: Klasör Yapısı (File Structure)
Projeyi tam olarak bu yapıda kurmanı istiyorum:

Plaintext

/ai-audiobook-studio
│
├── backend/
│   ├── app/
│   │   ├── ai/
│   │   │   ├── tts_engine.py    # XTTS Model Wrapper
│   │   │   └── text_processor.py # Spacy NLP Logic
│   │   ├── api/
│   │   │   ├── Player.tsx
│   │   │   └── FileUpload.tsx
│   │   ├── hooks/               # Custom React Hooks
│   │   ├── api/                 # Axios setup
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── index.css                # Tailwind imports
│   └── package.json
│
└── README.md
TALİMAT:

Önce Backend kodlarını (FastAPI, AI Logic, DB) yaz.

Sonra Frontend kodlarını (React, Tailwind, Components) yaz.

Tüm kodların birbirine nasıl bağlanacağını açıkla.

Hataya yer bırakma.