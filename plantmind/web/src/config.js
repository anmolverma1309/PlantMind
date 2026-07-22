// Environment configuration for API endpoints
const getApiBase = () => {
  // In production (Vercel), use relative URLs or the deployed backend
  if (import.meta.env.PROD) {
    // Use environment variable from Vercel, fallback to relative URL
    return import.meta.env.VITE_API_BASE || '/api/v1';
  }
  
  // Development environment
  return import.meta.env.VITE_API_BASE || 'http://localhost:8000/api/v1';
};

export const API_BASE = getApiBase();

export default {
  API_BASE
};
