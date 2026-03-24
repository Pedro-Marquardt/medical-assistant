import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  define: {
    'import.meta.env.VITE_BACKEND_HOST': JSON.stringify(process.env.BACKEND_HOST || 'http://localhost:3030')
  },
  server: {
    host: '0.0.0.0',
    port: 5174
  }
})
