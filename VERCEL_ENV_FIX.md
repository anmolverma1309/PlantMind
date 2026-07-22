# Vercel Environment Variable Configuration - FIXED

## The Issue (Now Fixed)
**Error:** `Invalid request: env.VITE_API_BASE should be string.`

**Root Cause:** The `vercel.json` had an invalid `env` section with only `"description"` but no `"value"`, which Vercel couldn't parse as a string.

**Solution:** Removed the problematic `env` section from both `vercel.json` files. Vercel automatically detects Vite environment variables (those starting with `VITE_`).

## How Environment Variables Work Now

### ✅ Development (Local)
```bash
cd plantmind/web
npm run dev
```
Reads from: `plantmind/web/.env`
```
VITE_API_BASE=http://localhost:8000/api/v1
```

### ✅ Production (Vercel)
Vercel uses (in order of priority):
1. **Environment variables set in Vercel dashboard** (highest priority)
2. **`.env.production` file** in the repository (default fallback)

Current `.env.production`:
```
VITE_API_BASE=/api/v1
```

## 📝 Step-by-Step: Configure for Vercel

### Option A: Use Default Value (Recommended for Testing)
The `.env.production` already has a default: `VITE_API_BASE=/api/v1`
- This assumes your backend API is accessible at `/api/v1` relative to your frontend
- Good for testing with a local backend proxy

### Option B: Override in Vercel Dashboard (Recommended for Production)

1. **Go to Vercel Dashboard**
   ```
   https://vercel.com → Your Project
   ```

2. **Navigate to Settings**
   ```
   Settings → Environment Variables
   ```

3. **Add Environment Variable**
   ```
   Name: VITE_API_BASE
   Value: https://your-backend-api.com/api/v1
   
   (Replace with your actual backend URL)
   ```

4. **Select Environment** (optional, applies to all by default)
   - Recommended: Apply to all (Production, Preview, Development)

5. **Save and Redeploy**
   ```
   Deployments → Latest → Redeploy
   ```

## How It Works

### Build Time
1. Vite reads `VITE_API_BASE` from environment
2. If running on Vercel, it uses the dashboard value or `.env.production` default
3. Vite substitutes `import.meta.env.VITE_API_BASE` with the actual value
4. Build output contains hardcoded value (not a reference to process.env)

### Runtime
```javascript
// src/config.js
const getApiBase = () => {
  if (import.meta.env.PROD) {
    return import.meta.env.VITE_API_BASE || '/api/v1';
  }
  return import.meta.env.VITE_API_BASE || 'http://localhost:8000/api/v1';
};

export const API_BASE = getApiBase();
```

- If `VITE_API_BASE` was set at build time, it uses that
- Otherwise falls back to `/api/v1` (production) or `localhost:8000` (development)

## Files Changed

### ✅ Root `vercel.json`
- ❌ Removed: `env` section with invalid configuration
- ✅ Kept: Build settings, rewrites, headers

### ✅ `plantmind/web/vercel.json`  
- ❌ Removed: `env` section with invalid configuration
- ✅ Kept: Build settings, rewrites, headers

### ✅ `vite.config.js`
- ❌ Removed: Manual `define` of `import.meta.env.PROD` (Vite does this automatically)
- ✅ Added: Comment explaining Vite's automatic VITE_* variable exposure

### ✅ `plantmind/web/.env.production`
- ✅ Kept as-is: Provides default fallback value

## Testing the Fix

### Local Test
```bash
cd plantmind/web

# Test development
VITE_API_BASE=http://localhost:8000/api/v1 npm run dev

# Test production build
VITE_API_BASE=https://api.production.com npm run build
npm run preview
```

### Vercel Test
1. Push changes to GitHub
2. Wait for auto-deployment
3. Check Vercel deployment logs - should complete successfully
4. Visit your app URL - should load without "Invalid request" error
5. Check browser console - should show API requests going to correct endpoint

## Verification Checklist

- [ ] `vercel.json` files don't have invalid `env` sections
- [ ] `vite.config.js` is simplified (no manual define needed)
- [ ] `.env.production` has default value
- [ ] Vercel Dashboard has `VITE_API_BASE` environment variable set (optional but recommended)
- [ ] Latest commits pushed to GitHub
- [ ] Vercel auto-deployment completed
- [ ] Build logs show: "✓ Built successfully" (no env errors)
- [ ] Frontend loads at your Vercel URL
- [ ] Browser console shows no errors

## Troubleshooting

### Issue: Still getting "Invalid request: env.VITE_API_BASE should be string"
**Solution:**
1. Verify `vercel.json` files don't have the `env` section anymore
2. Clear Vercel cache: Settings → Build & Development → Clear Cache
3. Trigger new deployment: Deployments → Latest → Redeploy
4. Wait 2-3 minutes for rebuild

### Issue: Frontend loads but API calls to wrong URL
**Solution:**
1. Check `VITE_API_BASE` in Vercel Dashboard (should match your backend)
2. Verify environment variable is set for the correct environment
3. Check browser DevTools → Network → look at actual API request URLs
4. Redeploy after making changes: Deployments → Latest → Redeploy

### Issue: "Cannot find module" or import errors
**Solution:**
1. Run locally: `cd plantmind/web && npm install && npm run build`
2. Check for syntax errors in `src/config.js`
3. Verify all imports are correct

## How This Differs from Previous Configuration

| Aspect | Before | After |
|--------|--------|-------|
| **vercel.json env** | ❌ Invalid format | ✅ Removed entirely |
| **Vite config** | ❌ Manual define | ✅ Automatic (Vite handles it) |
| **Priority** | ❌ Confusing | ✅ Clear: Dashboard > .env.production |
| **Flexibility** | ❌ Required config | ✅ Works with or without env variable |
| **Error Messages** | ❌ "should be string" | ✅ Clear fallback behavior |

## Next Steps

1. **Commit and push** these changes to GitHub
2. **Wait for Vercel** to auto-deploy (30-60 seconds)
3. **Check Vercel build logs** - should succeed now
4. **Set `VITE_API_BASE` in Vercel dashboard** if using production backend
5. **Test your frontend** - all features should work
