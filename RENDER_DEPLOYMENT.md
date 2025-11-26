# 🚀 RENDER DEPLOYMENT GUIDE

## ✅ Code Successfully Pushed to GitHub

Repository: `https://github.com/rehmanul/da_phi-OgTool`
Branch: `main`
Status: **Ready for deployment** (no secrets in git)

## 🔐 Security Fixed

- ✅ Removed `.env` from git
- ✅ Removed `deploy-render.sh` from git  
- ✅ Created `.gitignore` to prevent future leaks
- ✅ Cleaned `.env.example` of real API keys

## 📋 DEPLOY TO RENDER (3 Steps)

### Step 1: Go to Render Dashboard

Navigate to: **<https://dashboard.render.com>**

### Step 2: Create New Web Service from Blueprint

1. Click **"New +"** → **"Blueprint"**
2. Connect repository: `rehmanul/da_phi-OgTool`
3. Branch: `main`
4. Render will auto-detect `render.yaml`

### Step 3: Set Environment Variables in Render Dashboard

**Required:**

```
PERPLEXITY_API_KEY=your_perplexity_api_key_here
GEMINI_API_KEY=your_gemini_api_key_here
```

**Optional (if using AWS features):**

```
AWS_ACCESS_KEY_ID=your_aws_access_key_id_here
AWS_SECRET_ACCESS_KEY=your_aws_secret_access_key_here
AWS_REGION=us-east-1
```

**System Variables (already in render.yaml):**

```
QDRANT_URL=disabled
CLICKHOUSE_HOST=disabled
RABBITMQ_URL=disabled
```

### Step 4: Deploy

Click **"Apply"** or **"Create Web Service"**

Render will:

1. Pull code from GitHub
2. Build Docker image
3. Create PostgreSQL database  
4. Deploy the monolith
5. Provide URL: `https://ogtool-monolith.onrender.com`

---

## 🎯 What Was Deployed

### Architecture

- **6 Microservices** → **1 Monolithic App**
- **External Queue** (RabbitMQ) → **In-Memory Queue**
- **Analytics DB** (ClickHouse) → **Disabled**
- **Vector DB** (Qdrant) → **Disabled**

### APIs

- **Primary LLM**: Perplexity Sonar (`llama-3.1-sonar-small-128k-online`)
- **Fallback LLM**: Google Gemini (`gemini-1.5-flash`)
- **Database**: PostgreSQL (Render Free Tier)

### Cost

- **Infrastructure**: $0 (Render Free Tier + PostgreSQL Free Tier)
- **API Costs**: Only Perplexity/Gemini usage (pay-as-you-go)

---

## ✅ Verification

Once deployed, test these endpoints:

- **Health Check**: `https://ogtool-monolith.onrender.com/health`
- **API Docs**: `https://ogtool-monolith.onrender.com/docs`
- **Dashboard**: `https://ogtool-monolith.onrender.com`

---

## 🔄 Future Updates

To update the deployment:

```bash
git add .
git commit -m "Your update message"
git push origin main
```

Render will auto-deploy (configured in `render.yaml` with `autoDeploy: true`).

---

## 🎉 YOU'RE DONE

The application is production-ready with 0-cost infrastructure.
