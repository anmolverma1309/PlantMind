import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    host: true
  },
  define: {
    'import.meta.env.PROD': JSON.stringify(process.env.NODE_ENV === 'production')
  }
})
