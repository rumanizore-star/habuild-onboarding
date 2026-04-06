# Deployment Guide: SQLite (Local) → PostgreSQL (ECS/Production)

## Local Development (SQLite)

**No setup needed!** The app automatically uses SQLite by default.

```bash
# Install dependencies
pip3 install -r requirements.txt

# Run the app
python3 app.py
```

Data persists to `instance/habuild_onboarding.db` on the filesystem.

---

## ECS/Production Deployment (PostgreSQL + RDS)

### 1. Create AWS RDS PostgreSQL Instance

```bash
aws rds create-db-instance \
  --db-instance-identifier habuild-db \
  --db-instance-class db.t3.micro \
  --engine postgres \
  --master-username habuild \
  --master-user-password your-strong-password \
  --allocated-storage 20 \
  --publicly-accessible false
```

**Or use AWS Console:**
- RDS → Create Database → PostgreSQL
- Instance ID: `habuild-db`
- Master username: `habuild`
- Note the endpoint (e.g., `habuild-db.xxx.us-east-1.rds.amazonaws.com`)

### 2. Set Environment Variables in ECS

Create an `.env` file or set in ECS Task Definition:

```bash
export SECRET_KEY=your-strong-secret-key-here
export DATABASE_URL=postgresql://habuild:password@habuild-db.xxx.us-east-1.rds.amazonaws.com:5432/habuild
```

**In ECS Task Definition (JSON):**
```json
{
  "containerDefinitions": [
    {
      "name": "habuild-app",
      "environment": [
        {
          "name": "DATABASE_URL",
          "value": "postgresql://habuild:password@habuild-db.xxx.us-east-1.rds.amazonaws.com:5432/habuild"
        },
        {
          "name": "SECRET_KEY",
          "value": "your-strong-secret-key"
        }
      ]
    }
  ]
}
```

**Better: Use AWS Secrets Manager for passwords**
```json
{
  "name": "DATABASE_URL",
  "valueFrom": "arn:aws:secretsmanager:us-east-1:123456789:secret:habuild-db-url"
}
```

### 3. Build & Push Docker Image

```dockerfile
# Dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "app.py"]
```

```bash
# Build
docker build -t habuild-onboarding:latest .

# Push to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 123456789.dkr.ecr.us-east-1.amazonaws.com
docker tag habuild-onboarding:latest 123456789.dkr.ecr.us-east-1.amazonaws.com/habuild-onboarding:latest
docker push 123456789.dkr.ecr.us-east-1.amazonaws.com/habuild-onboarding:latest
```

### 4. Deploy to ECS

```bash
# Update task definition with new image
aws ecs update-service \
  --cluster habuild-cluster \
  --service habuild-service \
  --force-new-deployment
```

---

## How It Works

### Environment Variable Priority

```
1. Check $DATABASE_URL env var
   ├─ If set to PostgreSQL URL → Use PostgreSQL
   └─ If empty or not set → Use SQLite (fallback)

2. app.py logic:
   DATABASE_URL = os.environ.get('DATABASE_URL') or 'sqlite:///habuild_onboarding.db'
```

### Database URL Format

**SQLite (local):**
```
sqlite:///habuild_onboarding.db
```

**PostgreSQL (RDS):**
```
postgresql://username:password@hostname:5432/database_name
```

**Example RDS URL:**
```
postgresql://habuild:MyPassword123@habuild-db.c9akciq32.us-east-1.rds.amazonaws.com:5432/habuild
```

---

## File Structure

```
.env                    ← Your environment variables (NOT committed, .gitignored)
.env.example           ← Template for .env (committed, for reference)
app.py                 ← Reads DATABASE_URL from environment
requirements.txt       ← Includes psycopg2-binary (PostgreSQL driver)
Dockerfile             ← For ECS container build
instance/              ← Local SQLite data (only exists locally)
  habuild_onboarding.db
```

---

## Troubleshooting

### "Could not parse SQLAlchemy URL"
**Cause:** Empty or invalid DATABASE_URL  
**Fix:** Leave DATABASE_URL unset/empty in .env to use SQLite, or provide valid PostgreSQL URL

### "Psycopg2 import error"
**Cause:** psycopg2-binary not installed  
**Fix:** `pip3 install psycopg2-binary`

### "Connection refused to PostgreSQL"
**Cause:** RDS endpoint incorrect or security group rules missing  
**Fix:** 
1. Check RDS endpoint in AWS Console
2. Verify security group allows inbound port 5432
3. Test connection: `psql -h endpoint -U habuild -d habuild`

---

## Security Notes

- ⚠️ **Never commit `.env`** — it's in `.gitignore` for a reason
- ⚠️ **Use AWS Secrets Manager** for production database passwords
- ⚠️ **Use strong SECRET_KEY** — generate with: `python3 -c "import secrets; print(secrets.token_urlsafe(32))"`
- ⚠️ **Restrict RDS security group** — only allow inbound from ECS security group
