import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    host: true, // 0.0.0.0 - tüm network interface'lere izin ver
    strictPort: false,
  },
  preview: {
    host: true, // Lightning AI gibi external hostları kabul et
    strictPort: false,
    allowedHosts: ['.litng.ai', '.lightning.ai', 'localhost'], // Lightning AI domainlerini allow et
  },
  build: {
    // Cache busting için her build'de yeni hash'ler oluştur
    rollupOptions: {
      output: {
        // Dosya isimlerine timestamp ekleyerek cache'i bypass et
        entryFileNames: 'assets/[name]-[hash].js',
        chunkFileNames: 'assets/[name]-[hash].js',
        assetFileNames: 'assets/[name]-[hash].[ext]',
      },
    },
    // Eski dosyaları temizle
    emptyOutDir: true,
    // Source map'leri production'da kapat (opsiyonel, performans için)
    sourcemap: false,
  },
})
