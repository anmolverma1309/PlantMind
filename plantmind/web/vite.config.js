import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    host: true
  },
  // Vite automatically exposes VITE_* environment variables to import.meta.env
  // No need for manual define, just set VITE_API_BASE in .env or Vercel dashboard
})
