# Vercel 404 Error - Troubleshooting Guide

## Fixed Issues

### 1. SPA Routing Configuration
**Problem:** Vercel was returning 404 for routes like `/dashboard`, `/compliance` etc.
**Solution:** Added rewrites in `vercel.json` to route all requests to `index.html`

```json
"rewrites": [
  {
    "source": "/(.*)",
    "destination": "/index.html"
  }
]
```

This allows React Router to handle client-side routing.

### 2. Build Output Verification
- Build command: `npm run build`
- Output directory: `dist/` ✓
- Build creates `dist/index.html` ✓
- All assets in `dist/assets/` ✓

## Vercel Deployment Checklist

### Before Deploying
- [ ] Run `npm run build` locally and verify `dist/` folder exists
- [ ] Test locally: `npm run preview`
- [ ] All changes committed to git

### In Vercel Dashboard

1. **Settings > Environment Variables**
   ```
   VITE_API_BASE = https://your-backend-api.com/api/v1
   ```
   Replace with your actual backend URL

2. **Settings > Build & Development**
   - Build Command: `npm run build`
   - Output Directory: `dist`
   - (These should auto-detect from vercel.json)

3. **Deployments > Redeploy**
   - After setting environment variables, trigger a new deployment
   - Click "Redeploy" on the latest commit

### Verify Deployment Success

1. **Check Vercel Build Logs**
   - Go to Deployments tab
   - Click latest deployment
   - Verify build completed without errors
   - Look for: "✓ built in XXXms"

2. **Test Frontend Loading**
   - Visit your Vercel domain
   - Check browser console for errors (F12 > Console tab)
   - Verify styles and layouts load correctly

3. **Test API Connectivity**
   - In browser console, try: `fetch('/api/v1/graph/stats')`
   - Should return data or CORS error (not 404)
   - If getting 404 on API, verify `VITE_API_BASE` environment variable

## Common 404 Issues & Solutions

### Issue 1: Frontend Page Returns 404
**Symptoms:** "Cannot GET /" when visiting Vercel domain
**Solution:** 
1. Check Vercel build logs - must complete successfully
2. Verify `outputDirectory: "dist"` in vercel.json
3. Delete `.vercel` folder locally and redeploy

### Issue 2: API Calls Return 404
**Symptoms:** "Not Found" errors when clicking buttons
**Solution:**
1. Open browser DevTools (F12 > Network tab)
2. Check the full URL of failed request
3. Verify `VITE_API_BASE` environment variable is set correctly
4. Test API directly: `curl https://your-backend-api.com/api/v1/graph/stats`

### Issue 3: CORS Error (Not 404 but similar)
**Symptoms:** "CORS policy" errors in console
**Solution:**
1. Backend API needs CORS enabled for your Vercel domain
2. Contact backend owner to add your domain to CORS whitelist
3. In backend FastAPI: add `allow_origins=["https://your-vercel-domain.vercel.app"]`

### Issue 4: Assets Not Loading (CSS/JS broken)
**Symptoms:** Page loads but looks broken/unstyled
**Solution:**
1. Check Network tab - CSS/JS should load successfully
2. Verify no 404 on `/assets/*` files
3. Clear browser cache: Cmd+Shift+R or Ctrl+Shift+R

## Debug Steps

1. **Check Browser Console**
   ```
   F12 → Console tab → Look for errors
   ```

2. **Check Network Requests**
   ```
   F12 → Network tab → Look for 404 responses
   ```

3. **Check Vercel Build Log**
   ```
   Vercel Dashboard → Deployments → Click deployment → Logs
   ```

4. **Test Build Locally**
   ```bash
   npm run build
   npm run preview
   ```
   Visit `http://localhost:4173`

## Files Changed
- `vercel.json` - Added SPA rewrites and cache headers
- `.vercelignore` - Added to exclude unnecessary files
- `vite.config.js` - Already configured for production

## Next Steps
1. Commit these changes
2. Push to git
3. Vercel auto-deploys
4. Verify deployment in browser
5. Set `VITE_API_BASE` in Vercel dashboard
6. Redeploy to apply environment variable
