# Deploy to Railway (10 Minutes)

Simple step-by-step to deploy your Flask app + database on Railway.

---

## What is Railway?

- ☁️ Cloud hosting (like Heroku, but better)
- 📦 Auto-deploys on every git push
- 🗄️ Built-in PostgreSQL database
- 💰 $10-25/month for Flask + database
- 🔄 Zero downtime updates
- 📊 Free monitoring & logs

---

## Step 1: Create Railway Account

1. Go to **https://railway.app**
2. Click "Login"
3. Choose "GitHub" → Authorize
4. Done ✅

---

## Step 2: Create New Project

1. Click **"New Project"** button
2. Select **"Deploy from GitHub repo"**
3. Search for `habuild-onboarding`
4. Click to select it
5. Railway detects it's a Flask app ✅

---

## Step 3: Add PostgreSQL Database

1. Click **"Add Service"** (top-right)
2. Select **"PostgreSQL"**
3. Wait for it to spin up (30 seconds)
4. Railway auto-creates:
   - Database user: `postgres`
   - Database name: `railway`
   - Random secure password
   - Full connection URL

---

## Step 4: Configure Environment Variables

1. Go to **"Variables"** tab
2. You'll see these auto-created:
   ```
   DATABASE_URL=postgresql://postgres:...@...:5432/railway
   ```

3. Add these manually:
   ```
   SECRET_KEY=hb-onboarding-secret-key
   FLASK_ENV=production
   ```

Your variables should look like:
```
DATABASE_URL    postgresql://postgres:xyz@containers.railway.app:5432/railway
SECRET_KEY      hb-onboarding-secret-key
FLASK_ENV       production
```

---

## Step 5: Deploy!

1. Click **"Deploy"** button
2. Railway pulls your code from GitHub
3. Installs dependencies from `requirements.txt`
4. Starts the Flask app
5. Wait for green checkmark ✅

---

## Step 6: Get Your Live URL

1. Go to **Deployments** tab
2. Click the green "Running" deployment
3. Copy the URL: `https://habuild-xxxx.railway.app`
4. Visit it! 🎉

---

## 🔄 From Now On: Auto-Deployment

Every time you push to GitHub:

```bash
# Local computer
git add .
git commit -m "Update features"
git push origin main

# ↓ Automatic ↓

# Railway automatically:
# 1. Pulls latest code
# 2. Installs requirements.txt
# 3. Reads environment variables
# 4. Restarts Flask app
# 5. Your site updates live (zero downtime)
```

**You don't need to do anything else!**

---

## ✅ Database (PostgreSQL)

Railway's PostgreSQL is:
- ✅ Fully managed (Railway handles backups, updates)
- ✅ Automatically created
- ✅ Connection URL auto-set in `DATABASE_URL`
- ✅ Persists data across deployments
- ✅ Included in the price ($10-25/month)

**Your app automatically uses it** because:
- `.env` has `DATABASE_URL` pointing to Railway's PostgreSQL
- `app.py` reads `DATABASE_URL` env variable
- SQLAlchemy connects to PostgreSQL automatically

---

## 🔍 Check Deployment Status

### View Logs
1. Click the **"Running" deployment**
2. Click **"View Logs"**
3. See real-time Flask logs

### View Database
1. In Railway, click **PostgreSQL service**
2. Click **"Data"** tab
3. Browse your database tables
4. See your joiners, tasks, plans, etc.

### Visit Your App
Click the **URL** in Railway dashboard → Your live app!

---

## 🔑 Secret Key Note

You already set:
```
SECRET_KEY=hb-onboarding-secret-key
```

This is fine for now. For production, generate a stronger one:
```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
# Copy output → Update in Railway Variables tab
```

---

## Troubleshooting

### App won't deploy?
1. Check **Logs** tab → See error messages
2. Common issues:
   - Missing dependency in `requirements.txt`
   - Python version mismatch
   - Environment variable typo

### Can't connect to database?
1. Check `DATABASE_URL` is in Variables
2. Make sure PostgreSQL service is running (green checkmark)
3. Check logs for connection errors

### Need to restart app?
1. Go to **Deployments**
2. Click the running one
3. Click **"Redeploy"** button

---

## 💰 Pricing

| Component | Cost |
|-----------|------|
| Flask app (256MB) | $5/month |
| PostgreSQL database | $5-15/month |
| **Total** | **$10-25/month** |

---

## 🚀 Your Deployment Checklist

- ✅ GitHub account connected
- ✅ Flask app pushed to GitHub (`main` branch)
- ✅ `requirements.txt` has all dependencies
- ✅ `Dockerfile` present (Railway uses it)
- ✅ `.env` file exists locally (NOT committed)
- ✅ Railway project created
- ✅ PostgreSQL added
- ✅ Environment variables set:
  - `SECRET_KEY`
  - `DATABASE_URL` (auto from Railway)
  - `FLASK_ENV=production`
- ✅ Deployed
- ✅ Testing live app

---

## 📚 That's It!

You're done! Your app is:
- ✅ Live at: `https://habuild-xxxx.railway.app`
- ✅ Using PostgreSQL database
- ✅ Auto-updating on every git push
- ✅ Costing $10-25/month
- ✅ Monitored by Railway

---

## Next Steps

1. **Test the live app:**
   - Visit your Railway URL
   - Login with: `hr@habuild.in` / `Onboarding@123`
   - Try adding a joiner
   - Check the 30-60-90 plan feature

2. **Make changes locally:**
   ```bash
   git add .
   git commit -m "Your change"
   git push origin main
   # ← Auto-deploys!
   ```

3. **Monitor in Railway:**
   - Check logs anytime
   - View database
   - Set up alerts (optional)

---

## Support

**Railway Dashboard:** https://railway.app/dashboard

**Stuck?** Check Railway docs or contact support via the dashboard.

**App working?** Great! You're deployed! 🎉
