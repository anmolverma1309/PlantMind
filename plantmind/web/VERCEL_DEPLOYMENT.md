# PlantMind Frontend Deployment Guide

## Vercel Deployment Instructions

### Prerequisites
- Vercel account (https://vercel.com)
- Git repository connected to Vercel
- Backend API endpoint URL

### Environment Configuration

1. **Local Development**
   - The `.env` file is already configured for local development
   - Default API base: `http://localhost:8000/api/v1`
   - Run: `npm run dev`

2. **Vercel Production**
   - In your Vercel project dashboard, go to Settings > Environment Variables
   - Add the following environment variable:
     ```
     VITE_API_BASE = https://your-backend-api.com/api/v1
     ```
   - Replace `https://your-backend-api.com` with your actual backend URL

### Deployment Steps

1. **Push to Git**
   ```bash
   git add .
   git commit -m "Fix Vercel deployment configuration"
   git push origin main
   ```

2. **Vercel Auto-Deploy**
   - Vercel will automatically detect changes and deploy
   - Or manually trigger deployment from Vercel dashboard

3. **Verify Deployment**
   - Check that the build completes successfully
   - Test API connectivity from the deployed frontend
   - Monitor Vercel deployment logs for errors

### Build Details
- Framework: Vite + React
- Build output: `dist/`
- Build command: `npm run build`
- Start command: `npm run preview` (for local preview)

### Troubleshooting

**Issue: API calls fail with 404 or CORS errors**
- Verify `VITE_API_BASE` environment variable is set in Vercel dashboard
- Check that your backend API is accessible from Vercel
- Ensure backend has CORS enabled for your Vercel domain

**Issue: Build fails**
- Check Vercel build logs for specific error messages
- Ensure all dependencies are installed: `npm install`
- Verify Node version compatibility (Node 16+)

**Issue: Components not loading**
- Clear browser cache
- Check browser console for import errors
- Verify all component files exist

### API Configuration

The application uses a dynamic API configuration:
- **Development**: Connects to `http://localhost:8000/api/v1`
- **Production**: Uses environment variable `VITE_API_BASE`
  - Defaults to `/api/v1` (relative path) if not specified
  - Can be configured via Vercel environment variables

All API calls are made through axios with proper error handling.
