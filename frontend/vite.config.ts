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
  }
})
