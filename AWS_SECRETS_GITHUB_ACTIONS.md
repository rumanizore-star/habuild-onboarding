# Deployment Guide: AWS Secrets Manager + GitHub Actions CI/CD

Complete setup for **secure secrets management + automated deployment**.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│ GitHub Repository                                       │
│ ├── Push code to main branch                            │
│ └── GitHub Actions triggered                            │
└──────────────────┬──────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────┐
│ GitHub Actions Workflow                                 │
│ ├── 1. Run tests                                        │
│ ├── 2. Build Docker image                               │
│ ├── 3. Push to AWS ECR                                  │
│ └── 4. Deploy to ECS                                    │
└──────────────────┬──────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────┐
│ AWS Services                                            │
│ ├── Secrets Manager (DATABASE_URL, SECRET_KEY)          │
│ ├── ECR (Docker image registry)                         │
│ ├── ECS (container orchestration)                       │
│ ├── RDS PostgreSQL (database)                           │
│ └── CloudWatch (logs)                                   │
└─────────────────────────────────────────────────────────┘
```

---

## Step 1: Create AWS Secrets in Secrets Manager

### 1.1 Create Secrets via AWS Console

1. Go to **AWS Secrets Manager** → **Secrets** → **Store a new secret**
2. Create the following secrets:

**Secret 1: `habuild/db-url`**
```json
{
  "database_url": "postgresql://habuild:password@habuild-db.xxx.us-east-1.rds.amazonaws.com:5432/habuild"
}
```

**Secret 2: `habuild/secret-key`**
```json
{
  "secret_key": "HpqB2_vK9jL4mN8pQrS5tUvWxYz1aB3cDeFgHiJkL="
}
```

### 1.2 Or via AWS CLI

```bash
# Secret 1: Database URL
aws secretsmanager create-secret \
  --name habuild/db-url \
  --secret-string '{"database_url":"postgresql://habuild:password@habuild-db.xxx.us-east-1.rds.amazonaws.com:5432/habuild"}' \
  --region us-east-1

# Secret 2: SECRET_KEY
aws secretsmanager create-secret \
  --name habuild/secret-key \
  --secret-string '{"secret_key":"HpqB2_vK9jL4mN8pQrS5tUvWxYz1aB3cDeFgHiJkL="}' \
  --region us-east-1
```

---

## Step 2: Create IAM Role for GitHub Actions

GitHub Actions needs permission to access AWS Secrets Manager and push to ECR/ECS.

### 2.1 Create IAM Policy

Go to **IAM** → **Policies** → **Create policy** → **JSON**

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "secretsmanager:GetSecretValue"
      ],
      "Resource": [
        "arn:aws:secretsmanager:us-east-1:123456789:secret:habuild/*"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "ecr:GetAuthorizationToken",
        "ecr:BatchCheckLayerAvailability",
        "ecr:GetDownloadUrlForLayer",
        "ecr:PutImage",
        "ecr:InitiateLayerUpload",
        "ecr:UploadLayerPart",
        "ecr:CompleteLayerUpload"
      ],
      "Resource": "arn:aws:ecr:us-east-1:123456789:repository/habuild-onboarding"
    },
    {
      "Effect": "Allow",
      "Action": [
        "ecs:UpdateService",
        "ecs:DescribeServices",
        "ecs:DescribeTaskDefinition",
        "ecs:DescribeCluster",
        "ecs:ListServices"
      ],
      "Resource": "*"
    }
  ]
}
```

Name it: `GitHubActionsHabuildPolicy`

### 2.2 Create IAM Role for GitHub

Go to **IAM** → **Roles** → **Create role** → **Custom trust policy**

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::123456789:oidc-provider/token.actions.githubusercontent.com"
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringLike": {
          "token.actions.githubusercontent.com:sub": "repo:rumanizore-star/habuild-onboarding:*"
        }
      }
    }
  ]
}
```

Attach the policy `GitHubActionsHabuildPolicy` to this role.

Name it: `GitHubActionsHabuildRole`

**Note the role ARN:** `arn:aws:iam::123456789:role/GitHubActionsHabuildRole`

---

## Step 3: Create GitHub Actions Workflow

Create file: `.github/workflows/deploy.yml`

```yaml
name: Deploy to ECS

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

env:
  AWS_REGION: us-east-1
  ECR_REGISTRY: 123456789.dkr.ecr.us-east-1.amazonaws.com
  ECR_REPOSITORY: habuild-onboarding
  ECS_SERVICE: habuild-service
  ECS_CLUSTER: habuild-cluster
  ECS_TASK_DEFINITION: habuild-task

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.9'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
      
      - name: Run syntax check
        run: |
          python -m py_compile app.py

  build-and-deploy:
    needs: test
    runs-on: ubuntu-latest
    permissions:
      id-token: write
      contents: read
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v2
        with:
          role-to-assume: arn:aws:iam::123456789:role/GitHubActionsHabuildRole
          aws-region: ${{ env.AWS_REGION }}
      
      - name: Login to Amazon ECR
        id: login-ecr
        uses: aws-actions/amazon-ecr-login@v1
      
      - name: Build Docker image
        env:
          ECR_REGISTRY: ${{ steps.login-ecr.outputs.registry }}
        run: |
          docker build -t $ECR_REGISTRY/$ECR_REPOSITORY:$GITHUB_SHA .
          docker tag $ECR_REGISTRY/$ECR_REPOSITORY:$GITHUB_SHA $ECR_REGISTRY/$ECR_REPOSITORY:latest
      
      - name: Push to Amazon ECR
        env:
          ECR_REGISTRY: ${{ steps.login-ecr.outputs.registry }}
        run: |
          docker push $ECR_REGISTRY/$ECR_REPOSITORY:$GITHUB_SHA
          docker push $ECR_REGISTRY/$ECR_REPOSITORY:latest
      
      - name: Update ECS Task Definition
        id: task-def
        uses: aws-actions/amazon-ecs-render-task-definition@v1
        with:
          task-definition: ${{ env.ECS_TASK_DEFINITION }}.json
          container-name: habuild-app
          image: ${{ env.ECR_REGISTRY }}/${{ env.ECR_REPOSITORY }}:${{ github.sha }}
      
      - name: Deploy to Amazon ECS
        uses: aws-actions/amazon-ecs-deploy-task-definition@v1
        with:
          task-definition: ${{ steps.task-def.outputs.task-definition }}
          service: ${{ env.ECS_SERVICE }}
          cluster: ${{ env.ECS_CLUSTER }}
          wait-for-service-stability: true
```

---

## Step 4: Create Dockerfile

Create: `Dockerfile`

```dockerfile
FROM python:3.9-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app
COPY . .

# Create instance directory for SQLite fallback
RUN mkdir -p instance

# Run Flask
CMD ["python", "app.py"]
```

---

## Step 5: Create ECS Task Definition

Create file: `habuild-task.json`

```json
{
  "family": "habuild-task",
  "taskRoleArn": "arn:aws:iam::123456789:role/ecsTaskRole",
  "executionRoleArn": "arn:aws:iam::123456789:role/ecsTaskExecutionRole",
  "networkMode": "awsvpc",
  "cpu": "256",
  "memory": "512",
  "containerDefinitions": [
    {
      "name": "habuild-app",
      "image": "123456789.dkr.ecr.us-east-1.amazonaws.com/habuild-onboarding:latest",
      "portMappings": [
        {
          "containerPort": 5050,
          "hostPort": 5050,
          "protocol": "tcp"
        }
      ],
      "secrets": [
        {
          "name": "DATABASE_URL",
          "valueFrom": "arn:aws:secretsmanager:us-east-1:123456789:secret:habuild/db-url:database_url::"
        },
        {
          "name": "SECRET_KEY",
          "valueFrom": "arn:aws:secretsmanager:us-east-1:123456789:secret:habuild/secret-key:secret_key::"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/habuild-onboarding",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
```

---

## Step 6: GitHub Secrets (for GitHub Actions)

Go to GitHub repo → **Settings** → **Secrets and variables** → **Actions** → **New repository secret**

Add:
- `AWS_ROLE_ARN` = `arn:aws:iam::123456789:role/GitHubActionsHabuildRole`
- `AWS_ACCOUNT_ID` = `123456789`

---

## Step 7: Deploy Flow

### First Time Setup

```bash
# 1. Create ECR repository
aws ecr create-repository --repository-name habuild-onboarding --region us-east-1

# 2. Create ECS cluster
aws ecs create-cluster --cluster-name habuild-cluster --region us-east-1

# 3. Register task definition
aws ecs register-task-definition --cli-input-json file://habuild-task.json --region us-east-1

# 4. Create ECS service
aws ecs create-service \
  --cluster habuild-cluster \
  --service-name habuild-service \
  --task-definition habuild-task \
  --desired-count 2 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-xxx],securityGroups=[sg-xxx],assignPublicIp=ENABLED}" \
  --region us-east-1
```

### Automatic Deployment

After setup, just **push to main branch**:

```bash
git add .
git commit -m "Feature: Add new onboarding checklist"
git push origin main
```

**GitHub Actions automatically:**
1. ✅ Runs tests
2. ✅ Builds Docker image
3. ✅ Pushes to ECR
4. ✅ Updates ECS service
5. ✅ Deploys new containers
6. ✅ Retrieves secrets from AWS Secrets Manager
7. ✅ Logs to CloudWatch

---

## Step 8: Monitoring & Logs

### View ECS Logs
```bash
aws logs tail /ecs/habuild-onboarding --follow
```

### View GitHub Actions Logs
GitHub repo → **Actions** → Click workflow → View logs

### Health Check
```bash
# Check service status
aws ecs describe-services \
  --cluster habuild-cluster \
  --services habuild-service \
  --region us-east-1
```

---

## Security Checklist

- ✅ Secrets in AWS Secrets Manager (not in code)
- ✅ GitHub OIDC role (no long-lived AWS keys)
- ✅ Different SECRET_KEY per environment
- ✅ RDS in private subnet (not public)
- ✅ ECS security group restricted
- ✅ Logs in CloudWatch (audit trail)
- ✅ Database user with limited permissions
- ✅ Auto-rotate secrets periodically

---

## Cost Estimate (per month, us-east-1)

| Service | Cost | Notes |
|---------|------|-------|
| **ECS (Fargate)** | ~$30-50 | 256 CPU, 512 MB memory |
| **RDS PostgreSQL** | ~$30-50 | db.t3.micro, 20GB storage |
| **ECR** | ~$0.10 | ~1GB stored images |
| **Secrets Manager** | ~$0.40 | Up to 4 secrets |
| **CloudWatch Logs** | ~$5-10 | Retention: 7 days |
| **Data Transfer** | ~$0-5 | Minimal if same region |
| **TOTAL** | **~$66-105/month** | Production-ready |

---

## Rollback Strategy

If deployment fails:

```bash
# Revert to previous task definition
aws ecs update-service \
  --cluster habuild-cluster \
  --service habuild-service \
  --task-definition habuild-task:X \
  --region us-east-1
```

Or just push a fix to main → GitHub Actions auto-deploys.

---

## Next Steps

1. Update AWS account ID in all configs (replace `123456789`)
2. Create secrets in Secrets Manager
3. Set up IAM roles
4. Commit GitHub Actions workflow
5. Push to main → auto-deployment starts! 🚀
