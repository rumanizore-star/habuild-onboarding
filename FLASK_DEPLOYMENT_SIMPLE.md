# Simple Flask Deployment Guide

Easy step-by-step instructions for deploying your Flask app. No complex CI/CD, just straightforward deployment.

---

## 🎯 What You Need

- Flask app (you have it ✅)
- A server/hosting (AWS, Railway, Heroku, DigitalOcean, etc.)
- PostgreSQL database (if not local)
- A way to keep the app running (systemd, supervisor, PM2, etc.)

---

## 📍 Deployment Path

```
Your Local Computer
        ↓
    Git Push
        ↓
    Server (pulls code)
        ↓
    Install Dependencies
        ↓
    Set Environment Variables
        ↓
    Run Flask App
        ↓
    Your App is Live! 🎉
```

---

## Option A: Simple Hosting (Easiest)

### Railway.app (Recommended - 10 minutes)

**Step 1:** Go to https://railway.app → Sign up with GitHub

**Step 2:** Click "New Project" → Select your GitHub repo

**Step 3:** Railway auto-detects Flask → Adds PostgreSQL

**Step 4:** Set environment variables:
```
SECRET_KEY=your-generated-secret-key-here
DATABASE_URL=postgresql://... (Railway generates this automatically)
FLASK_ENV=production
```

**Step 5:** Click "Deploy"

**Done!** Your app is live. Every time you push to GitHub, it auto-deploys.

---

## Option B: Linux Server (Manual Control)

### Step-by-Step Manual Deployment

#### **1. SSH into your server**
```bash
ssh user@your-server-ip
```

#### **2. Install dependencies**
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python & PostgreSQL client
sudo apt install -y python3 python3-pip postgresql-client

# Install Gunicorn (production server)
pip3 install gunicorn
```

#### **3. Clone your repo**
```bash
cd /home/user/apps
git clone https://github.com/rumanizore-star/habuild-onboarding.git
cd habuild-onboarding
```

#### **4. Install Python dependencies**
```bash
pip3 install -r requirements.txt
```

#### **5. Create `.env` file with secrets**
```bash
cat > .env << 'EOF'
SECRET_KEY=your-strong-secret-key-here
DATABASE_URL=postgresql://user:password@db-host:5432/habuild
FLASK_ENV=production
EOF
```

#### **6. Test it runs**
```bash
python3 app.py
# Should see: Running on http://127.0.0.1:5050
# Press Ctrl+C to stop
```

#### **7. Set up systemd service** (auto-start on server restart)

Create `/etc/systemd/system/habuild.service`:
```bash
sudo cat > /etc/systemd/system/habuild.service << 'EOF'
[Unit]
Description=Habuild Onboarding App
After=network.target

[Service]
Type=notify
User=habuild
WorkingDirectory=/home/habuild/apps/habuild-onboarding
Environment="PATH=/home/habuild/.local/bin"
ExecStart=/home/habuild/.local/bin/gunicorn --workers 4 --bind 0.0.0.0:5050 app:app
Restart=always

[Install]
WantedBy=multi-user.target
EOF
```

#### **8. Start the service**
```bash
sudo systemctl daemon-reload
sudo systemctl enable habuild
sudo systemctl start habuild

# Check status
sudo systemctl status habuild
```

#### **9. Set up Nginx (reverse proxy)**

Install Nginx:
```bash
sudo apt install -y nginx
```

Create `/etc/nginx/sites-available/habuild`:
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:5050;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /static {
        alias /home/habuild/apps/habuild-onboarding/static;
    }
}
```

Enable it:
```bash
sudo ln -s /etc/nginx/sites-available/habuild /etc/nginx/sites-enabled/
sudo systemctl restart nginx
```

#### **10. Update code (whenever you push)**
```bash
cd /home/habuild/apps/habuild-onboarding
git pull origin main
pip3 install -r requirements.txt  # Install new dependencies if any
sudo systemctl restart habuild
```

---

## Option C: Docker on Server

### Using Docker (No install complexity)

#### **1. SSH into server**
```bash
ssh user@your-server-ip
```

#### **2. Install Docker**
```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
```

#### **3. Clone repo**
```bash
cd /home/user/apps
git clone https://github.com/rumanizore-star/habuild-onboarding.git
cd habuild-onboarding
```

#### **4. Create `.env` file**
```bash
cat > .env << 'EOF'
SECRET_KEY=your-secret-key
DATABASE_URL=postgresql://user:pass@db:5432/habuild
FLASK_ENV=production
EOF
```

#### **5. Create `docker-compose.yml`** (if deploying database too)
```yaml
version: '3.8'

services:
  db:
    image: postgres:15-alpine
    environment:
      POSTGRES_USER: habuild
      POSTGRES_PASSWORD: your_secure_password
      POSTGRES_DB: habuild
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  web:
    build: .
    environment:
      DATABASE_URL: postgresql://habuild:your_secure_password@db:5432/habuild
      SECRET_KEY: your-secret-key
      FLASK_ENV: production
    ports:
      - "5050:5050"
    depends_on:
      - db

volumes:
  postgres_data:
```

#### **6. Run it**
```bash
# Start both database and app
docker-compose up -d

# View logs
docker-compose logs -f web

# Stop
docker-compose down
```

#### **7. Update when you push**
```bash
git pull origin main
docker-compose up -d --build  # Rebuilds and restarts
```

---

## 🔄 Deployment Workflow

### Every time you want to deploy:

**Local Computer:**
```bash
# Make changes
git add .
git commit -m "Update features"
git push origin main
```

**On Server:**
```bash
# Option 1: Manual (systemd)
cd /home/habuild/apps/habuild-onboarding
git pull
pip3 install -r requirements.txt
sudo systemctl restart habuild

# Option 2: Docker
cd /home/habuild/apps/habuild-onboarding
git pull
docker-compose up -d --build

# Option 3: Railway
(automatic - just push to GitHub)
```

---

## 🔍 Troubleshooting

### App won't start?
```bash
# Check logs
sudo systemctl status habuild
sudo journalctl -u habuild -n 50

# Or with Docker
docker-compose logs web
```

### Database connection error?
Check `.env` file:
```bash
cat .env
# Verify DATABASE_URL is correct
```

### Port already in use?
```bash
# Check what's using port 5050
sudo lsof -i :5050

# Kill it
sudo kill -9 <PID>
```

### Permission denied errors?
```bash
# Make sure user owns the directory
sudo chown -R habuild:habuild /home/habuild/apps/habuild-onboarding
```

---

## 📊 Comparison

| Method | Setup Time | Cost | Maintenance | Best For |
|--------|-----------|------|-------------|----------|
| **Railway.app** | 10 min | $10-25 | None | MVP, quick launch |
| **Linux + Systemd** | 1 hour | $5-20 | Medium | Full control |
| **Docker** | 30 min | $5-20 | Low | Scalability |
| **Heroku** | 10 min | $50+ | None | Simple (expensive) |

---

## 🎯 Quick Start (Choose One)

### I want it NOW (15 min)
→ Use **Railway.app**
1. Sign up with GitHub
2. Connect repo
3. Add PostgreSQL
4. Set `SECRET_KEY`
5. Deploy

### I want full control (1 hour)
→ Use **Linux Server**
1. SSH into server
2. Clone repo
3. Install dependencies
4. Set up systemd service
5. Set up Nginx
6. Deploy

### I want simplicity with Docker (30 min)
→ Use **Docker**
1. Install Docker
2. Clone repo
3. Run `docker-compose up`
4. Done

---

## 🚀 One-Line Deploy (after first setup)

**Linux Server:**
```bash
cd ~/apps/habuild-onboarding && git pull && pip3 install -r requirements.txt && sudo systemctl restart habuild
```

**Docker:**
```bash
cd ~/apps/habuild-onboarding && git pull && docker-compose up -d --build
```

**Railway:**
```bash
git push origin main  # Auto-deploys!
```

---

## 📝 Environment Variables (Quick Reference)

```bash
# Always needed
SECRET_KEY=<run: python3 -c "import secrets; print(secrets.token_urlsafe(32))">

# For production (Database URL)
DATABASE_URL=postgresql://user:password@host:5432/database

# Optional
FLASK_ENV=production
```

---

## 🔐 Security Checklist

- ✅ Never commit `.env` to GitHub (it's in .gitignore)
- ✅ Use strong `SECRET_KEY` (32+ characters)
- ✅ Use strong database password
- ✅ Keep server updated: `sudo apt update && sudo apt upgrade`
- ✅ Use HTTPS with SSL certificate (Railway/Heroku do this automatically)
- ✅ Restrict database to app server only (firewall rules)

---

## When Something Goes Wrong

**App won't start?**
```bash
python3 app.py  # Run locally to debug
```

**Can't connect to database?**
```bash
# Test connection
psql -h <host> -U <user> -d <database>
```

**Port 5050 not responding?**
```bash
# Check if app is running
ps aux | grep python
# Check firewall
sudo ufw allow 5050
```

---

## Support & Debugging

Check logs:
- **Systemd:** `sudo journalctl -u habuild -f`
- **Docker:** `docker-compose logs -f`
- **Railway:** Check dashboard logs

Check connectivity:
```bash
curl http://localhost:5050/login
```

Check database:
```bash
psql -h localhost -U habuild -d habuild
\dt  # List tables
```

---

## That's it!

Pick your method, follow the steps, and your Flask app is deployed! 🎉

**Questions?** Check the detailed guides or ask in the repo issues.
