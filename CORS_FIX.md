# 🔧 CORS Configuration Fix for Tavonga Backend

## Issue Description
The web-app deployed on Heroku (`https://tavonga-app-4e7034e4fd41.herokuapp.com`) is getting CORS errors when trying to make API calls to the backend on DigitalOcean (`https://jellyfish-app-ho48c.ondigitalocean.app`).

## ✅ Fixes Applied

### 1. Updated Django Settings (`core/settings.py`)
- ✅ Added comprehensive CORS configuration
- ✅ Included Heroku domain in allowed origins
- ✅ Added proper CORS headers and methods
- ✅ Configured CORS middleware correctly

### 2. Added CORS Test Endpoint
- ✅ Created `/api/v1/cors-test/` endpoint for debugging
- ✅ Returns detailed CORS information
- ✅ Helps diagnose cross-origin issues

### 3. Enhanced CORS Settings
```python
CORS_ALLOWED_ORIGINS = [
    'https://tavonga-app-4e7034e4fd41.herokuapp.com',
    'https://*.herokuapp.com',
    'http://localhost:3000',  # For local development
    'http://127.0.0.1:3000',  # For local development
]

CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_HEADERS = [
    'accept', 'accept-encoding', 'authorization', 'content-type',
    'dnt', 'origin', 'user-agent', 'x-csrftoken', 'x-requested-with',
]

CORS_ALLOW_METHODS = ['DELETE', 'GET', 'OPTIONS', 'PATCH', 'POST', 'PUT']
```

## 🚨 Environment Configuration Required

### For Production Deployment, Set These Environment Variables:

```bash
# CORS Configuration - CRITICAL!
CORS_ALLOWED_ORIGINS=https://tavonga-app-4e7034e4fd41.herokuapp.com

# CSRF Configuration
CSRF_TRUSTED_ORIGINS=https://jellyfish-app-ho48c.ondigitalocean.app,https://tavonga-app-4e7034e4fd41.herokuapp.com

# Other production settings
DEBUG=False
SECRET_KEY=your-production-secret-key
DATABASE_URL=your-postgres-url
```

## 🧪 Testing CORS Configuration

### Option 1: Use the CORS Test Endpoint
```bash
curl -X GET "https://jellyfish-app-ho48c.ondigitalocean.app/api/v1/cors-test/" \
  -H "Origin: https://tavonga-app-4e7034e4fd41.herokuapp.com" \
  -H "Content-Type: application/json"
```

### Option 2: Use the Test HTML Page
1. Deploy the web-app with the test page: `/public/test-cors.html`
2. Visit: `https://tavonga-app-4e7034e4fd41.herokuapp.com/test-cors.html`
3. Run the CORS tests

### Option 3: Browser Console Test
```javascript
fetch('https://jellyfish-app-ho48c.ondigitalocean.app/api/v1/cors-test/', {
  method: 'GET',
  headers: { 'Content-Type': 'application/json' }
})
.then(response => response.json())
.then(data => console.log('CORS Test:', data))
.catch(error => console.error('CORS Error:', error));
```

## 🔧 Deployment Steps

### 1. Deploy Backend Changes
```bash
# Commit and push backend changes
git add backend-api/
git commit -m "Fix CORS configuration for Heroku frontend"
git push origin main

# Deploy to DigitalOcean (your deployment method)
```

### 2. Set Environment Variables
In your DigitalOcean deployment, ensure these are set:
- `CORS_ALLOWED_ORIGINS=https://tavonga-app-4e7034e4fd41.herokuapp.com`
- `DEBUG=False`
- `SECRET_KEY=your-secure-key`

### 3. Restart Backend Service
```bash
# Restart your Django application
sudo systemctl restart tavonga-backend
# or however you restart your service
```

## ✅ Verification Checklist

- [ ] Backend deployed with CORS fixes
- [ ] Environment variables set correctly
- [ ] CORS test endpoint returns success
- [ ] Login endpoint accessible from frontend
- [ ] No CORS errors in browser console

## 📋 Common CORS Issues & Solutions

### Issue: "Access to fetch blocked by CORS policy"
**Solution:** Ensure Heroku domain is in `CORS_ALLOWED_ORIGINS`

### Issue: "Preflight request doesn't pass access control check"
**Solution:** Check `CORS_ALLOW_HEADERS` and `CORS_ALLOW_METHODS`

### Issue: "Credentials not supported if CORS header is '*'"
**Solution:** Use specific domains in `CORS_ALLOWED_ORIGINS`, not wildcards

### Issue: Environment variables not taking effect
**Solution:** Restart the Django application after setting env vars

## 🔍 Debugging Commands

### Check current CORS settings:
```python
# In Django shell
from django.conf import settings
print("CORS_ALLOWED_ORIGINS:", settings.CORS_ALLOWED_ORIGINS)
print("CORS_ALLOW_CREDENTIALS:", settings.CORS_ALLOW_CREDENTIALS)
```

### Test CORS manually:
```bash
# Test preflight request
curl -X OPTIONS "https://jellyfish-app-ho48c.ondigitalocean.app/api/v1/users/login/" \
  -H "Origin: https://tavonga-app-4e7034e4fd41.herokuapp.com" \
  -H "Access-Control-Request-Method: POST" \
  -H "Access-Control-Request-Headers: Content-Type" \
  -v
```

## 📞 Need Help?
If CORS issues persist after following these steps:
1. Check browser network tab for exact error messages
2. Verify environment variables are set correctly
3. Test with the CORS test endpoint
4. Check Django logs for any CORS-related errors 