import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Dev: vite serves the SPA on :5173 and proxies /api to the FastAPI backend on :8000.
// Prod: built dist/ is served by the FastAPI backend itself (single-container deploy).
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: process.env.VITE_API_TARGET || 'http://localhost:8000',
        changeOrigin: true,
        ws: false,
      },
    },
  },
  build: {
    outDir: 'dist',
    sourcemap: false,
  },
})
