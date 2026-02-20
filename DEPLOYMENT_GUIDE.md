# 🚀 Vercel Deployment Guide — RAG Chatbot

## Architecture Overview

| Component | Technology | Deployment Platform |
|-----------|-----------|----------------------|
| Backend (API) | FastAPI (Python) | Vercel Serverless |
| Frontend (UI) | Streamlit App | Streamlit Community Cloud (free) |
| Vector DB | Pinecone | Pinecone Cloud (already set up) |
| LLM | Groq (llama-3.3-70b) | Groq Cloud (already set up) |

> **Note:** Streamlit apps cannot be deployed to Vercel (Vercel only supports Node.js, Python functions, and static sites). We will deploy:
> - **Backend** → Vercel  
> - **Frontend** → Streamlit Community Cloud (free, easiest option)

---

## PART 1: Deploy Backend to Vercel

### Step 1 — Install Vercel CLI
```bash
npm install -g vercel
```

### Step 2 — Login to Vercel
```bash
vercel login
```
This will open a browser window. Sign in with GitHub, GitLab, or email.

### Step 3 — Update `streamlit_app.py` API_BASE (Before deploying frontend)
Open `streamlit_app.py` and change line 20 from:
```python
API_BASE = os.getenv("API_BASE", "http://127.0.0.1:8000")
```
to point to your Vercel backend URL (you'll get this after Step 4):
```python
API_BASE = os.getenv("API_BASE", "https://YOUR_VERCEL_PROJECT_NAME.vercel.app")
```

### Step 4 — Deploy Backend to Vercel
Run inside the project folder:
```bash
vercel --prod
```

When prompted:
- **Set up and deploy to existing project?** → `N` (No, create new)
- **Project name?** → e.g. `rag-chatbot-api`
- **Which directory is your code in?** → `.` (current directory)
- **Override settings?** → `N`

### Step 5 — Set Environment Variables on Vercel
After deployment, go to [vercel.com/dashboard](https://vercel.com/dashboard) → Your Project → **Settings** → **Environment Variables**

Add the following:

| Variable | Value |
|----------|-------|
| `PINECONE_API_KEY` | `pcsk_6Tcksy_...` (your Pinecone key) |
| `PINECONE_INDEX` | `own-rag` |
| `GROQ_API_KEY` | `gsk_rLQQe13J4...` (your Groq key) |
| `JWT_SECRET` | `supersecretkey123` (use a stronger key in production!) |
| `JWT_ALGORITHM` | `HS256` |
| `JWT_EXPIRE_HOURS` | `24` |
| `GROQ_MODEL` | `llama-3.3-70b-versatile` |
| `EMBED_MODEL` | `llama-text-embed-v2` |
| `EMBED_DIMENSION` | `1024` |
| `TOP_K` | `3` |
| `CHUNK_SIZE` | `800` |
| `CHUNK_OVERLAP` | `100` |

After adding all variables, click **Redeploy** to apply them.

### Step 6 — Verify Backend
Visit your Vercel URL:
- `https://YOUR_PROJECT.vercel.app/health` → Should return `{"status":"ok",...}`
- `https://YOUR_PROJECT.vercel.app/docs` → FastAPI Swagger UI

---

## PART 2: Deploy Frontend to Streamlit Community Cloud (Free)

### Step 1 — Push code to GitHub
```bash
git init  # (if not already)
git add .
git commit -m "feat: RAG chatbot ready for deployment"
git remote add origin https://github.com/YOUR_USERNAME/rag-chatbot.git
git push -u origin main
```

### Step 2 — Go to Streamlit Cloud
Visit [share.streamlit.io](https://share.streamlit.io) and sign in with GitHub.

### Step 3 — Deploy the App
- Click **"New app"**
- Select your GitHub repo and branch
- Set **Main file path** to: `streamlit_app.py`
- Click **"Advanced settings"** → Add Secrets:

```toml
API_BASE = "https://YOUR_VERCEL_PROJECT.vercel.app"
```

- Click **"Deploy!"**

---

## PART 3: Ingest Your PDF to Pinecone (One-time setup)

Before users can chat, you need to index the `You-are-the-World.pdf` into Pinecone.

### Option A — Via the App UI (After deployment)
1. Login as **admin / admin123**
2. Go to **📄 Upload Documents**
3. Upload `You-are-the-World.pdf`
4. Click **"Upload & Index All"**

### Option B — Via the Bootstrap Script (Local)
```bash
python ingest_bootstrap.py
```

---

## Summary of URLs After Deployment

| Service | URL |
|---------|-----|
| API Backend | `https://YOUR_PROJECT.vercel.app` |
| API Docs | `https://YOUR_PROJECT.vercel.app/docs` |
| Frontend App | `https://YOUR_APP.streamlit.app` |

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| `GROQ_API_KEY is not configured` | Add key in Vercel Environment Variables and redeploy |
| `Pinecone index error` | Check `PINECONE_API_KEY` and `PINECONE_INDEX` are set |
| `Backend offline` on frontend | Ensure `API_BASE` points to Vercel URL, not localhost |
| Streamlit shows "Cannot connect to backend" | Update `API_BASE` secret in Streamlit Cloud settings |
