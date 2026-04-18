# 🚀 Netlify Deployment Guide

## Prerequisites
1. **Backend Deployment**: Deploy your FastAPI backend first on a platform like:
   - [Render](https://render.com) (recommended)
   - [Railway](https://railway.app)
   - [Heroku](https://heroku.com)
   - [PythonAnywhere](https://pythonanywhere.com)

2. **Update API URLs**: In `netlify.toml`, replace `https://your-backend-url.onrender.com` with your actual backend URL.

## Deployment Steps

### 1. Connect to Netlify
- Go to [netlify.com](https://netlify.com)
- Sign up/Login with GitHub
- Click "New site from Git"
- Connect your GitHub repository: `https://github.com/Dipanshuth/Updated-project`

### 2. Configure Build Settings
- **Branch**: `main`
- **Build command**: `npm run build` (or leave as default)
- **Publish directory**: `frontend`

### 3. Environment Variables (Optional)
Add any environment variables your frontend might need:
- `API_BASE_URL`: Your backend URL (will override the default)

### 4. Deploy
- Click "Deploy site"
- Wait for deployment to complete
- Your site will be available at: `https://your-site-name.netlify.app`

## Post-Deployment
1. **Update Backend CORS**: Make sure your backend allows requests from your Netlify domain
2. **Test API Calls**: Verify that frontend can communicate with backend
3. **Custom Domain** (Optional): Add a custom domain in Netlify settings

## Troubleshooting
- **API Not Working**: Check that backend URL in `netlify.toml` is correct
- **404 Errors**: The `_redirects` file handles SPA routing
- **CORS Issues**: Update backend CORS settings to include Netlify domain

## File Structure for Deployment
```
frontend/          ← Published directory
├── index.html
├── dashboard.html
├── upload.html
├── css/
├── js/
└── _redirects     ← SPA routing
netlify.toml       ← Netlify configuration
package.json       ← Build configuration
```