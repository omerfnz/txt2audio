# 🚀 Sunucuda Frontend Güncelleme Rehberi

Eğer sunucuda hala eski UI görüyorsanız, aşağıdaki adımları **sırayla** uygulayın:

## ⚠️ ÖNEMLİ: Önce Mevcut Servisleri Durdurun

```bash
# Çalışan preview server'ı durdurun (Ctrl+C veya process kill)
# Eğer start.sh ile başlattıysanız:
pkill -f "vite preview" || true
pkill -f "npm run preview" || true
```

## 📋 Adım Adım Güncelleme

### 1. Frontend Klasörüne Gidin
```bash
cd frontend
```

### 2. Force Rebuild Scriptini Çalıştırın
```bash
chmod +x force-rebuild.sh
./force-rebuild.sh
```

**VEYA** Manuel olarak:

```bash
# Eski dosyaları temizle
rm -rf dist
rm -rf .vite
rm -rf node_modules/.vite

# npm cache temizle
npm cache clean --force

# Yeniden build et
npm run build
```

### 3. Build'in Başarılı Olduğunu Kontrol Edin
```bash
chmod +x check-build.sh
./check-build.sh
```

Bu script size:
- Build dosyalarının var olup olmadığını
- Hash'lerin güncel olup olmadığını
- Dosya oluşturulma tarihlerini gösterecek

### 4. Preview Server'ı Yeniden Başlatın
```bash
# Eski process'i öldürün (eğer çalışıyorsa)
pkill -f "vite preview" || true

# Yeni preview server başlatın
npm run preview -- --host
```

### 5. Browser Cache'i Temizleyin

**Chrome/Edge:**
- `Ctrl + Shift + Delete` → "Cached images and files" seçin → "Clear data"
- VEYA `Ctrl + F5` (Hard Refresh)
- VEYA `Ctrl + Shift + R` (Hard Reload)

**Firefox:**
- `Ctrl + Shift + Delete` → Cache temizle
- VEYA `Ctrl + F5`

**Safari:**
- `Cmd + Option + E` (Empty Caches)
- VEYA `Cmd + Shift + R`

### 6. Developer Tools ile Kontrol Edin

1. `F12` ile Developer Tools'u açın
2. **Network** tab'ına gidin
3. **Disable cache** checkbox'ını işaretleyin
4. Sayfayı yenileyin (`F5`)

### 7. Eğer Hala Eski UI Görüyorsanız

**A) index.html'i doğrudan kontrol edin:**
```bash
cat dist/index.html
```

Hash'lerin değiştiğini görmelisiniz. Eğer aynı hash'ler görünüyorsa, build düzgün çalışmamış demektir.

**B) Vite cache'ini tamamen temizleyin:**
```bash
cd frontend
rm -rf node_modules/.vite
rm -rf .vite
rm -rf dist
npm cache clean --force
npm install
npm run build
```

**C) Node modules'ü yeniden yükleyin:**
```bash
cd frontend
rm -rf node_modules
npm install
npm run build
```

## 🔍 Debug İpuçları

### Build Hash'lerini Kontrol Etme

```bash
# index.html'deki hash'leri göster
grep -o 'index-[^"]*\.js' frontend/dist/index.html

# Eğer her build'de aynı hash görüyorsanız, sorun var demektir
```

### Preview Server Port'unu Kontrol Etme

```bash
# Hangi port'ta çalışıyor?
netstat -tulpn | grep vite
# veya
lsof -i :4173
```

### Process'leri Kontrol Etme

```bash
# Tüm vite/node process'lerini göster
ps aux | grep -E "vite|node|npm"

# Eski process'leri öldür
pkill -f "vite preview"
```

## ✅ Başarı Kriterleri

Build başarılı olduğunda:
- ✅ `dist/index.html` dosyası mevcut
- ✅ `dist/assets/` klasöründe yeni hash'li dosyalar var
- ✅ Her build'de hash'ler değişiyor
- ✅ Preview server yeni dosyaları serve ediyor
- ✅ Browser cache temizlendi

## 🆘 Hala Çalışmıyorsa

1. **Sunucu loglarını kontrol edin:**
   ```bash
   # Preview server loglarını göster
   npm run preview -- --host 2>&1 | tee preview.log
   ```

2. **Build loglarını kontrol edin:**
   ```bash
   npm run build 2>&1 | tee build.log
   ```

3. **Git'te değişikliklerin commit edildiğinden emin olun:**
   ```bash
   git status
   git log --oneline -5
   ```

4. **Sunucuda doğru branch'te olduğunuzdan emin olun:**
   ```bash
   git branch
   git pull origin master
   ```

