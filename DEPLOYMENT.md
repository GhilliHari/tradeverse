# Tradeverse Deployment Guide

## 🚀 Quick Deploy to Production

This guide will help you deploy Tradeverse to the cloud in ~15 minutes.

### Prerequisites
- GitHub account
- Vercel account (free)
- Render account (free or $7/mo)
- Upstash account (free)
- Firebase project (free)

---

## Step 1: Setup Redis Database (Upstash)

1. Go to [upstash.com](https://upstash.com) and sign up
2. Create a new Redis database
3. Copy the `REDIS_URL` connection string (looks like: `redis://default:xxxxx@xxxxx.upstash.io:6379`)

---

## Step 2: Deploy Backend (Render)

1. Go to [render.com](https://render.com) and sign up
2. Click **"New +"** → **"Web Service"**
3. Connect your GitHub repository
4. Configure:
   - **Name**: `tradeverse-backend`
   - **Root Directory**: `backend`
   - **Environment**: `Docker`
   - **Instance Type**: Free or Starter ($7/mo recommended)
5. Add Environment Variables:
   ```
   ENV=LIVE
   REDIS_URL=<paste from Upstash>
   GEMINI_API_KEY=<your Gemini API key>
   FIREBASE_CREDENTIALS=<paste Firebase service account JSON as string>
   ```
6. Click **"Create Web Service"**
7. Wait for deployment (~5 mins)
8. Copy your backend URL (e.g., `https://tradeverse-backend.onrender.com`)

---

## Step 3: Deploy Frontend (Vercel)

1. Go to [vercel.com](https://vercel.com) and sign up
2. Click **"Add New"** → **"Project"**
3. Import your GitHub repository
4. Configure:
   - **Framework Preset**: Vite
   - **Root Directory**: `frontend`
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist`
5. Add Environment Variables:
   ```
   VITE_API_URL=<paste Render backend URL>
   VITE_FIREBASE_API_KEY=<from Firebase console>
   VITE_FIREBASE_AUTH_DOMAIN=<your-project>.firebaseapp.com
   VITE_FIREBASE_PROJECT_ID=<your-project-id>
   VITE_FIREBASE_STORAGE_BUCKET=<your-project>.appspot.com
   VITE_FIREBASE_MESSAGING_SENDER_ID=<sender-id>
   VITE_FIREBASE_APP_ID=<app-id>
   ```
6. Click **"Deploy"**
7. Wait for deployment (~2 mins)
8. Copy your frontend URL (e.g., `https://tradeverse.vercel.app`)

---

## Step 4: Configure Firebase

1. Go to [Firebase Console](https://console.firebase.google.com)
2. Select your project
3. Go to **Authentication** → **Settings** → **Authorized Domains**
4. Add your Vercel domain (e.g., `tradeverse.vercel.app`)

---

## Step 5: Test Your Deployment

1. Visit your Vercel URL
2. Try logging in with Firebase
3. Check if settings persist (they should save to Redis)
4. Enable AUTO mode and close the tab
5. Wait 30 seconds and check backend logs → Should revert to MANUAL (Dead Man's Switch)

---

## 🎉 You're Live!

Your trading system is now running in the cloud!

### Next Steps:
- Set up custom domain (optional)
- Configure IP restrictions for security
- Add Telegram notifications (Phase 5)
- Monitor logs and performance

### Troubleshooting

**Backend won't start:**
- Check Render logs for errors
- Verify all environment variables are set
- Ensure REDIS_URL is correct

**Frontend can't connect to backend:**
- Check VITE_API_URL is correct
- Verify backend is running (visit backend URL directly)
- Check CORS settings in backend

**Authentication fails:**
- Verify Firebase authorized domains
- Check Firebase environment variables
- Ensure Firebase credentials are valid

---

## Cost Breakdown

**Free Tier** (Good for testing):
- Vercel: Free
- Render: Free (sleeps after 15 mins inactivity)
- Upstash: Free (10K commands/day)
- **Total: $0/mo**

**Recommended** (Always-on):
- Vercel: Free
- Render Starter: $7/mo
- Upstash: Free
- **Total: $7/mo**

**Production** (High traffic):
- Vercel Pro: $20/mo
- Render Standard: $25/mo
- Upstash Pro: $10/mo
- **Total: $55/mo**
