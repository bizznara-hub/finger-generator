import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { fileURLToPath, URL } from 'node:url'

export default defineConfig({
  plugins: [
    vue({
      template: {
        // <iconify-icon> adalah custom element, bukan komponen Vue
        compilerOptions: { isCustomElement: (tag) => tag === 'iconify-icon' }
      }
    })
  ],
  resolve: {
    alias: { '@': fileURLToPath(new URL('./src', import.meta.url)) }
  },
  server: {
    port: 5173,
    proxy: { '/api': 'http://127.0.0.1:5057' }
  },
  build: { outDir: 'dist', emptyOutDir: true }
})
