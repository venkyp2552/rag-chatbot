# 🚀 Deployment Guide

Since this is a full-stack app (Backend + Frontend), the best way to deploy it for free is to split it:
1. **Backend (FastAPI)** -> Deployed on **Vercel**.
2. **Frontend (Streamlit)** -> Deployed on **Streamlit Community Cloud**.

---

## Part 1: Prepare for Deployment

1. **Create a GitHub Repository**
   - Go to [GitHub.com](https://github.com/new) and create a new repository (e.g., `rag-app`).
   - Upload all the files from `rag_project_complete.zip` to this repository.

---

## Part 2: Deploy Backend to Vercel

1. **Go to Vercel**: [vercel.com](https://vercel.com) and Sign Up/Login.
2. **Add New Project**:
   - Click **"Add New"** > **"Project"**.
   - Import your `rag-app` GitHub repository.
3. **Configure Settings**:
   - **Framework Preset**: Select "Other".
   - **Environment Variables**: Add the following (copy values from your `.env` file):
     - `PINECONE_API_KEY`
     - `PINECONE_INDEX`
     - `GROQ_API_KEY`
     - `JWT_SECRET`
4. **Deploy**:
   - Click **"Deploy"**.
   - Once finished, copy the **Domain** (e.g., `https://rag-app-backend.vercel.app`).

---

## Part 3: Deploy Frontend to Streamlit Cloud

1. **Go to Streamlit**: [share.streamlit.io](https://share.streamlit.io) and Sign Up/Login.
2. **New App**:
   - Click **"New app"**.
   - Select your GitHub repository (`rag-app`).
   - **Main file path**: `streamlit_app.py`.
3. **Advanced Settings**:
   - Click **"Advanced settings"** (or "Environment variables").
   - Add this variable:
     - `API_BASE`: Paste your Vercel Backend URL (e.g., `https://rag-app-backend.vercel.app`)
       *(Make sure there is NO trailing slash `/` at the end)*
4. **Deploy**:
   - Click **"Deploy"**.

---

## 🎉 Done!
Your app is now live!
- **Frontend**: `https://your-streamlit-app.streamlit.app`
- **Backend API**: `https://rag-app-backend.vercel.app/docs`

### ⚠️ Important Note on Data Persistence
Since Vercel uses "Serverless Functions", the memory resets frequently.
- **Users**: Any new users you create via "Sign Up" might disappear after a while. The hardcoded admin (`admin`/`admin123`) will always work.
- **Documents**: Your PDFs are stored in Pinecone (Persistent Vector DB), so **documents WILL persist** safely!
