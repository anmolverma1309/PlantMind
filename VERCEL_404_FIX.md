# Vercel Deployment Fix - 404 Resolution

## Root Cause of 404 Error

The 404 error was happening because:
1. Vercel wasn't finding the correct build output directory
2. SPA routing wasn't properly configured
3. Vercel didn't know to route non-existent routes to `/index.html`

## Solution Implemented

### 1. Root-Level `vercel.json`
Created a root-level configuration file that tells Vercel:
- Where to build from: `plantmind/web` directory
- Where the output is: `plantmind/web/dist`
- How to route requests: All requests → `/index.html`

### 2. Updated Web-Level `vercel.json`
Improved the rewrites configuration with:
- Proper Vercel syntax: `:path*` pattern matching
- Cache control headers for assets (1 year)
- HTML cache headers (no-cache for index.html)

### 3. Build Verification
- ✓ Build completes successfully in ~550ms
- ✓ `dist/index.html` generated with correct structure
- ✓ All assets referenced with `/assets/` prefix
- ✓ No build errors

## How to Fix the 404 Error on Vercel

### Step 1: Clear Vercel Cache
1. Go to Vercel Dashboard
2. Find your PlantMind project
3. Click "Settings" → "Build & Development"
4. Click "Clear Cache"

### Step 2: Trigger New Deployment
```bash
# Option A: Push changes to git (auto-deploys)
git push origin main

# Option B: Manual redeploy
# In Vercel dashboard → Deployments → Latest → Redeploy
```

### Step 3: Verify Configuration
After pushing/redeploying, verify in Vercel:
1. Go to Deployments → Latest
2. Check "Overview" tab - should show success
3. Check "Build Logs" - should end with "✓ Built successfully"
4. Verify no errors mentioning `dist` or `index.html`

### Step 4: Test Frontend
1. Visit your Vercel domain (e.g., `your-app.vercel.app`)
2. Should load the PlantMind page
3. Click navigation tabs - routes should work
4. Open browser console (F12) - should show no 404 errors

## Vercel.json Configuration Explanation

### Root vercel.json
```json
{
  "buildCommand": "cd plantmind/web && npm run build",
  "outputDirectory": "plantmind/web/dist",
  "framework": "vite",
  "rewrites": [{ "source": "/:path*", "destination": "/index.html" }]
}
```
- Explicitly tells Vercel to build in subdirectory
- Routes all URLs to React app

### Web vercel.json
```json
{
  "outputDirectory": "dist",
  "rewrites": [{ "source": "/:path*", "destination": "/index.html" }],
  "headers": [
    { "source": "/assets/:path*", "headers": [...] },
    { "source": "/index.html", "headers": [...] }
  ]
}
```
- Optimizes caching for assets
- Ensures index.html is never cached

## Files Changed
1. **vercel.json** (root) - NEW
   - Monorepo configuration
   - Build and deployment settings

2. **plantmind/web/vercel.json** - UPDATED
   - Improved rewrite patterns
   - Better cache headers

## Verification Checklist

- [ ] Root `vercel.json` created at project root
- [ ] `plantmind/web/vercel.json` updated with correct rewrites
- [ ] Build completes locally without errors
- [ ] `dist/index.html` file exists
- [ ] Vercel cache cleared
- [ ] Latest commits pushed to GitHub
- [ ] Vercel shows "Production" deployment as successful
- [ ] Frontend loads at your Vercel URL
- [ ] Routes work: `/`, `/dashboard`, `/compliance`, `/lessons`, `/graph`
- [ ] Browser console shows no 404 errors

## Common Issues & Solutions

### Issue: Still getting 404
**Solution:**
1. Check Vercel Build Logs (Deployments → Latest → Logs)
2. Look for errors about `outputDirectory`
3. Ensure both `vercel.json` files are committed and pushed
4. Wait 2-3 minutes for Vercel to process
5. Try clearing cache and redeploying

### Issue: Build fails with "command not found"
**Solution:**
1. Ensure `package.json` has build script: `"build": "vite build"`
2. Check dependencies are installed: `npm install`
3. Verify Node version in Vercel (should be 16+)

### Issue: Assets return 404
**Solution:**
1. Check build output: `dist/assets/` folder should exist
2. Verify file paths in `dist/index.html`
3. Check Cache headers aren't preventing asset loading

## Next Steps

1. Commit these changes
2. Push to GitHub
3. Wait for Vercel auto-deployment
4. Verify in browser
5. Set `VITE_API_BASE` environment variable in Vercel dashboard
6. Redeploy after setting environment variable

Once 404 is fixed:
1. Verify API calls work (check browser Network tab)
2. Test all features (Chat, Dashboard, Compliance, Lessons, Graph)
3. Monitor Vercel dashboard for any errors
