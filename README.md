# 🤖 RAG API Service — FastAPI + Streamlit

A full-stack Retrieval-Augmented Generation (RAG) application with:
- **FastAPI** backend with JWT authentication
- **Streamlit** frontend UI
- **Pinecone** vector database with `llama-text-embed-v2` embeddings
- **Groq** LLM with `llama-3.3-70b-versatile`

---

## 🗂️ Project Structure

```
rag_app/
├── backend.py          # FastAPI backend (API server)
├── streamlit_app.py    # Streamlit frontend UI
├── requirements.txt    # Python dependencies
├── .env                # Environment variables (pre-configured)
├── .gitignore
└── Rag_folder/         # Place your PDFs here (optional, use UI to upload)
```

---

## ⚡ Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Start the FastAPI Backend

Open **Terminal 1**:
```bash
uvicorn backend:app --reload --host 0.0.0.0 --port 8000
```

You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete.
```

### 3. Start the Streamlit Frontend

Open **Terminal 2**:
```bash
streamlit run streamlit_app.py
```

Your browser will open automatically at `http://localhost:8501`

---

## 🔐 Login Credentials

| Username | Password  | Role  | Permissions                        |
|----------|-----------|-------|------------------------------------|
| admin    | admin123  | Admin | Full access: chat + upload + users |
| user1    | user123   | User  | Chat only                          |
| user2    | user456   | User  | Chat only                          |

---

## 📄 How to Index Documents

1. Log in as **admin**
2. Click **"📄 Upload Documents"** in the sidebar
3. Drag and drop your PDF files
4. Click **"Upload & Index All"**
5. Wait for indexing to complete (depends on file size)
6. Switch to **"💬 Chat"** and start asking questions!

---

## 🌐 API Endpoints

| Method | Endpoint          | Auth Required | Role  | Description              |
|--------|-------------------|---------------|-------|--------------------------|
| GET    | `/health`         | No            | —     | Service health check     |
| POST   | `/auth/login`     | No            | —     | Get JWT token            |
| POST   | `/rag/query`      | Yes           | Any   | Ask a question           |
| POST   | `/ingest/upload`  | Yes           | Admin | Upload & index a PDF     |
| GET    | `/users/me`       | Yes           | Any   | Current user info        |
| GET    | `/users/list`     | Yes           | Admin | List all users           |

### Interactive API Docs
Once backend is running, visit:
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

---

## 🧪 Testing the API Manually

### Login
```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'
```

### Query
```bash
curl -X POST http://localhost:8000/rag/query \
  -H "Authorization: Bearer <YOUR_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"question": "What is the main topic of the documents?"}'
```

### Upload PDF
```bash
curl -X POST http://localhost:8000/ingest/upload \
  -H "Authorization: Bearer <YOUR_TOKEN>" \
  -F "file=@/path/to/your/document.pdf"
```

### Health Check
```bash
curl http://localhost:8000/health
```

---

## ⚙️ Configuration

All settings are in `.env` (pre-configured):

```env
PINECONE_API_KEY=pcsk_6Tcksy_...
PINECONE_INDEX=own-rag
GROQ_API_KEY=gsk_SxmvqT...
JWT_SECRET=a3f8c2e1...
GROQ_MODEL=llama-3.3-70b-versatile
EMBED_MODEL=llama-text-embed-v2
EMBED_DIMENSION=1024
TOP_K=5
CHUNK_SIZE=800
CHUNK_OVERLAP=100
```

---

## 🏗️ Architecture

```
User Browser
     │
     ▼
┌─────────────────────┐
│   Streamlit UI      │  Port 8501
│   (streamlit_app.py)│
└──────────┬──────────┘
           │ HTTP REST
           ▼
┌─────────────────────┐
│   FastAPI Backend   │  Port 8000
│   (backend.py)      │
│   JWT Auth          │
└──────┬──────────────┘
       │
   ┌───┴────┐
   │        │
   ▼        ▼
Pinecone   Groq API
(Vectors)  (LLM)
   ▲
   │ embed via Pinecone Inference
llama-text-embed-v2
```

---

## 🔧 RAG Pipeline Flow

1. **User sends question** via Streamlit chat
2. **JWT validated** by FastAPI middleware
3. **Query embedded** using `llama-text-embed-v2` (Pinecone Inference)
4. **Top-5 chunks retrieved** from Pinecone `own-rag` index
5. **Context + question sent** to Groq `llama-3.3-70b-versatile`
6. **Answer returned** with source document names

---

## 🚨 Troubleshooting

| Problem | Solution |
|---------|----------|
| "Cannot connect to backend" | Start backend: `uvicorn backend:app --reload` |
| "Pinecone index error" | Check your index name is exactly `own-rag` |
| "Embedding error" | Verify Pinecone API key in `.env` |
| "LLM error" | Verify Groq API key in `.env` |
| "No relevant information found" | Upload and index PDFs first via Admin UI |
| Slow responses | Normal — embedding + retrieval + generation takes 3-8s |

---

## 🔒 Security Notes

- JWT tokens expire after **24 hours**
- Only **Admin** users can upload documents
- All API endpoints (except `/health` and `/auth/login`) require a valid JWT
- Keep your `.env` file private — never commit it to git

---

## 📦 Adding More Users

Edit the `USERS` dictionary in `backend.py`:

```python
USERS = {
    "newuser": {
        "username": "newuser",
        "password": pwd_ctx.hash("their_password"),  # bcrypt hashed
        "role": "user",  # or "admin"
        "full_name": "New User Name"
    },
    # ... existing users
}
```

---

*Built with FastAPI + Streamlit + Pinecone + Groq | RAG API Service v1.0*
