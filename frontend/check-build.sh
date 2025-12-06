#!/bin/bash
# Build kontrol scripti - Sunucuda build'in güncel olup olmadığını kontrol eder

echo "========================================"
echo "Frontend Build Check"
echo "========================================"
echo ""

if [ ! -d "dist" ]; then
    echo "❌ dist klasörü bulunamadı! Build yapılmamış."
    exit 1
fi

if [ ! -f "dist/index.html" ]; then
    echo "❌ dist/index.html bulunamadı!"
    exit 1
fi

echo "✓ dist klasörü mevcut"
echo ""

# index.html'deki hash'leri göster
echo "Build dosyaları:"
echo "----------------"
JS_FILE=$(grep -o 'assets/index-[^"]*\.js' dist/index.html | head -1)
CSS_FILE=$(grep -o 'assets/index-[^"]*\.css' dist/index.html | head -1)

if [ -n "$JS_FILE" ]; then
    echo "JS: $JS_FILE"
    if [ -f "dist/$JS_FILE" ]; then
        echo "  ✓ Dosya mevcut"
        echo "  📅 Oluşturulma: $(stat -c %y "dist/$JS_FILE" 2>/dev/null || stat -f "%Sm" "dist/$JS_FILE" 2>/dev/null || echo "Bilinmiyor")"
    else
        echo "  ❌ Dosya bulunamadı!"
    fi
else
    echo "❌ JS dosyası index.html'de bulunamadı!"
fi

if [ -n "$CSS_FILE" ]; then
    echo "CSS: $CSS_FILE"
    if [ -f "dist/$CSS_FILE" ]; then
        echo "  ✓ Dosya mevcut"
        echo "  📅 Oluşturulma: $(stat -c %y "dist/$CSS_FILE" 2>/dev/null || stat -f "%Sm" "dist/$CSS_FILE" 2>/dev/null || echo "Bilinmiyor")"
    else
        echo "  ❌ Dosya bulunamadı!"
    fi
else
    echo "❌ CSS dosyası index.html'de bulunamadı!"
fi

echo ""
echo "Tüm dist içeriği:"
ls -lh dist/ 2>/dev/null || ls -l dist/

