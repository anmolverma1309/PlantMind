# PlantMind - Full Deployment Guide

## Project Structure

```
PlantMind ET/
├── plantmind/
│   ├── api/              (FastAPI backend - Python)
│   ├── web/              (React frontend - Vite)
│   ├── graph/            (Knowledge graph module)
│   ├── ingestion/        (Data pipeline)
│   ├── agents/           (AI agents)
│   └── requirements.txt  (Python dependencies)
└── docs/                 (Documentation)
```

## Vercel Frontend Deployment

### 1. Prerequisites
- Vercel account
- GitHub repository with `plantmind/web` folder
- Deployed backend API URL

### 2. Environment Configuration

#### In Vercel Dashboard:
1. Settings > Environment Variables
2. Add the following:
   ```
   VITE_API_BASE = https://your-backend-api.com/api/v1
   ```

#### In Local Development:
```bash
cd plantmind/web
npm install
npm run dev  # http://localhost:5173
```

### 3. Deploy to Vercel

```bash
# Option 1: Auto-deploy via GitHub
# Just push to main branch, Vercel will auto-deploy

# Option 2: Manual deployment
npm run build
vercel deploy
```

### 4. Verify Deployment
- [ ] Frontend loads at `https://your-domain.vercel.app`
- [ ] Routes work: `/dashboard`, `/compliance`, `/lessons`, `/graph`
- [ ] API calls succeed (check browser console for errors)
- [ ] Environment variable `VITE_API_BASE` is set

## Backend Deployment (FastAPI)

### Option A: Deploy to Heroku (Recommended)

```bash
# 1. Install Heroku CLI
# 2. Login to Heroku
heroku login

# 3. Create Heroku app
heroku create plantmind-api
heroku config:set GOOGLE_API_KEY=your-key
heroku config:set CORS_ORIGINS=https://your-domain.vercel.app,http://localhost:3000

# 4. Deploy
git push heroku main

# 5. Verify
heroku open
```

### Option B: Deploy to Railway, Render, or AWS

Update `CORS_ORIGINS` in backend config to include your frontend URL.

### Backend Environment Variables

```bash
# Required
GOOGLE_API_KEY=your-google-api-key
CORS_ORIGINS=https://your-domain.vercel.app,http://localhost:3000

# Optional
LOG_LEVEL=INFO
CHROMA_PERSIST_DIR=/tmp/chroma_db
```

## Full Integration Checklist

### Frontend (Vercel)
- [ ] Build succeeds locally: `npm run build`
- [ ] No build errors in Vercel logs
- [ ] Environment variables set in Vercel dashboard
- [ ] `VITE_API_BASE` points to backend URL
- [ ] Frontend loads without 404 errors
- [ ] Routes work correctly

### Backend (Your Server)
- [ ] API runs successfully
- [ ] CORS enabled for your Vercel domain
- [ ] `GOOGLE_API_KEY` environment variable set
- [ ] Database files/graph initialized
- [ ] Accessible at public URL

### Integration
- [ ] Backend URL set in frontend environment
- [ ] API calls from frontend succeed
- [ ] No CORS errors in browser console
- [ ] Chat, Dashboard, Compliance, Graph all load data
- [ ] Error messages are helpful (not 404 mentions of localhost)

## Troubleshooting

### Frontend 404 Error
- Check Vercel build logs
- Verify `vercel.json` exists with SPA rewrites
- Clear Vercel cache and redeploy

### API 404 Errors in Frontend
- Verify `VITE_API_BASE` environment variable is set
- Check it matches your backend URL
- Test backend directly: `curl https://your-backend/api/v1/graph/stats`

### CORS Errors
- Backend must have your Vercel domain in `CORS_ORIGINS`
- Error will look like: "No 'Access-Control-Allow-Origin' header"
- Update backend config and redeploy

### Build Fails
- Run `npm install` locally to verify dependencies
- Check for TypeScript/Linting errors: `npm run lint`
- Check Node version (16+): `node --version`

## Local Testing

```bash
# Terminal 1: Backend
cd plantmind
python -m uvicorn api.main:app --reload --port 8000

# Terminal 2: Frontend
cd plantmind/web
npm run dev

# Terminal 3: Build testing
cd plantmind/web
npm run build
npm run preview  # Test production build
```

## API Endpoints Reference

- `GET /api/v1/graph/stats` - Get graph statistics
- `GET /api/v1/graph/export` - Export graph data
- `POST /api/v1/query` - Ask a question
- `POST /api/v1/agents/compliance` - Run compliance audit
- `POST /api/v1/agents/rca` - Run root cause analysis
- `POST /api/v1/agents/lessons` - Get lessons learned

## Support

For deployment issues:
1. Check build logs (Vercel dashboard)
2. Check browser console (F12)
3. Check network requests (F12 > Network tab)
4. Review error messages - they now include detailed info
5. Verify environment variables are set correctly
