"""
RAG API Backend - FastAPI Service
Endpoints: /auth/login, /rag/query, /ingest/upload, /health
JWT Auth with Admin + User roles
Pinecone vector DB + Groq LLM
"""

from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import jwt
import hashlib
import os
import io
import json
import time
import uuid
import httpx
import pypdf
import asyncio
from datetime import datetime, timedelta
from passlib.context import CryptContext

# ─────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────
PINECONE_API_KEY  = os.getenv("PINECONE_API_KEY")
PINECONE_INDEX    = os.getenv("PINECONE_INDEX", "own-rag")
GROQ_API_KEY      = os.getenv("GROQ_API_KEY")
JWT_SECRET        = os.getenv("JWT_SECRET", "default-secret-change-in-production")
JWT_ALGORITHM     = "HS256"
JWT_EXPIRE_HOURS  = 24

GROQ_MODEL        = "llama-3.3-70b-versatile"
EMBED_MODEL       = "llama-text-embed-v2"
EMBED_DIMENSION   = 1024
TOP_K             = 3
CHUNK_SIZE        = 800
CHUNK_OVERLAP     = 100

# ─────────────────────────────────────────────
# USERS DB (in-memory, Admin + User roles)
# ─────────────────────────────────────────────
pwd_ctx = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

USERS = {
    "admin": {
        "username": "admin",
        "password": pwd_ctx.hash("admin123"),
        "role": "admin",
        "full_name": "Administrator"
    },
    "user1": {
        "username": "user1",
        "password": pwd_ctx.hash("user123"),
        "role": "user",
        "full_name": "Regular User"
    },
    "user2": {
        "username": "user2",
        "password": pwd_ctx.hash("user456"),
        "role": "user",
        "full_name": "Second User"
    }
}

# ─────────────────────────────────────────────
# FASTAPI APP
# ─────────────────────────────────────────────
app = FastAPI(
    title="RAG API Service",
    description="Retrieval-Augmented Generation API with Pinecone + Groq",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

security = HTTPBearer()

# ─────────────────────────────────────────────
# SCHEMAS
# ─────────────────────────────────────────────
class LoginRequest(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    role: str
    full_name: str
    expires_in: int

class QueryRequest(BaseModel):
    question: str

class QueryResponse(BaseModel):
    answer: str
    sources: List[str]
    chunks_used: int

class IngestResponse(BaseModel):
    message: str
    filename: str
    chunks_indexed: int

class HealthResponse(BaseModel):
    status: str
    timestamp: str
    version: str

class SignupRequest(BaseModel):
    username: str
    password: str
    full_name: str

# ─────────────────────────────────────────────
# JWT HELPERS
# ─────────────────────────────────────────────
def create_token(username: str, role: str) -> str:
    payload = {
        "sub": username,
        "role": role,
        "iat": datetime.utcnow(),
        "exp": datetime.utcnow() + timedelta(hours=JWT_EXPIRE_HOURS)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

def get_current_user(creds: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    payload = decode_token(creds.credentials)
    username = payload.get("sub")
    if username not in USERS:
        raise HTTPException(status_code=401, detail="User not found")
    user = USERS[username].copy()
    user["role"] = payload.get("role", user["role"])
    return user

def require_admin(user: dict = Depends(get_current_user)) -> dict:
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return user

# ─────────────────────────────────────────────
# PINECONE HELPERS (via REST API)
# ─────────────────────────────────────────────
PINECONE_HEADERS = {
    "Api-Key": PINECONE_API_KEY,
    "Content-Type": "application/json",
    "X-Pinecone-API-Version": "2025-04"
}

async def get_pinecone_host() -> str:
    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.get(
            f"https://api.pinecone.io/indexes/{PINECONE_INDEX}",
            headers=PINECONE_HEADERS
        )
        if r.status_code != 200:
            raise HTTPException(status_code=500, detail=f"Pinecone index error: {r.text}")
        data = r.json()
        return f"https://{data['host']}"

async def embed_text(texts: List[str]) -> List[List[float]]:
    """Generate embeddings via Pinecone Inference API"""
    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.post(
            "https://api.pinecone.io/embed",
            headers=PINECONE_HEADERS,
            json={
                "model": EMBED_MODEL,
                "inputs": [{"text": t} for t in texts],
                "parameters": {"input_type": "passage", "truncate": "END"}
            }
        )
        if r.status_code != 200:
            raise HTTPException(status_code=500, detail=f"Embedding error: {r.text}")
        data = r.json()
        return [item["values"] for item in data["data"]]

async def embed_query(question: str) -> List[float]:
    """Embed a query for retrieval"""
    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.post(
            "https://api.pinecone.io/embed",
            headers=PINECONE_HEADERS,
            json={
                "model": EMBED_MODEL,
                "inputs": [{"text": question}],
                "parameters": {"input_type": "query", "truncate": "END"}
            }
        )
        if r.status_code != 200:
            raise HTTPException(status_code=500, detail=f"Query embed error: {r.text}")
        data = r.json()
        return data["data"][0]["values"]

async def upsert_vectors(host: str, vectors: list):
    """Upsert vectors into Pinecone index"""
    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.post(
            f"{host}/vectors/upsert",
            headers=PINECONE_HEADERS,
            json={"vectors": vectors}
        )
        if r.status_code != 200:
            raise HTTPException(status_code=500, detail=f"Upsert error: {r.text}")
        return r.json()

async def query_vectors(host: str, vector: List[float], top_k: int = TOP_K) -> list:
    """Query Pinecone for similar vectors"""
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post(
            f"{host}/query",
            headers=PINECONE_HEADERS,
            json={
                "vector": vector,
                "topK": top_k,
                "includeMetadata": True,
                "includeValues": False
            }
        )
        if r.status_code != 200:
            raise HTTPException(status_code=500, detail=f"Query error: {r.text}")
        return r.json().get("matches", [])

# ─────────────────────────────────────────────
# GROQ LLM HELPER
# ─────────────────────────────────────────────
async def generate_answer(question: str, context_chunks: List[str]) -> str:
    """Call Groq API to generate answer with context"""
    context = "\n\n---\n\n".join(context_chunks)
    system_prompt = """You are an AI assistant helping users explore the philosophy of Jiddu Krishnamurti based on his book 'You Are The World'. 
    
    Guidelines:
    1. Answer questions deeply and reflectively using the provided context as your foundation.
    2. If asked to summarize a topic or the text, synthesize the available context chunks into a coherent overview.
    3. If asked about a specific concept (e.g., "What is love?"), explain it fully based on the retrieved text.
    4. Maintain a calm, inquiry-based tone similar to the author's style.
    5. You may use your general understanding of Krishnamurti's philosophy to connect the dots between the provided chunks, but do not contradict the text."""
    
    user_message = f"""Context from documents:
{context}

Question: {question}

Please provide a clear, accurate answer based on the context above."""

    max_retries = 3
    base_delay = 5
    
    async with httpx.AsyncClient(timeout=60) as client:
        for attempt in range(max_retries):
            r = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {GROQ_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": GROQ_MODEL,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_message}
                    ],
                    "temperature": 0.2,
                    "max_tokens": 1024
                }
            )
            
            if r.status_code == 200:
                return r.json()["choices"][0]["message"]["content"]
            
            if r.status_code == 429:
                error_data = r.json()
                wait_time = base_delay * (attempt + 1)
                print(f"⚠️ Rate limit hit. Retrying in {wait_time}s... (Attempt {attempt + 1}/{max_retries})")
                await asyncio.sleep(wait_time)
                continue
                
            raise HTTPException(status_code=500, detail=f"LLM error: {r.text}")
            
        raise HTTPException(status_code=429, detail="Rate limit exceeded. Please try again later.")

# ─────────────────────────────────────────────
# PDF PROCESSING
# ─────────────────────────────────────────────
def extract_text_from_pdf(file_bytes: bytes) -> str:
    """Extract text from PDF bytes"""
    reader = pypdf.PdfReader(io.BytesIO(file_bytes))
    text = ""
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text + "\n"
    return text.strip()

def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> List[str]:
    """Split text into overlapping chunks"""
    words = text.split()
    chunks = []
    i = 0
    while i < len(words):
        chunk_words = words[i:i + chunk_size]
        chunk = " ".join(chunk_words)
        if chunk.strip():
            chunks.append(chunk)
        i += chunk_size - overlap
    return chunks

# ─────────────────────────────────────────────
# ENDPOINTS
# ─────────────────────────────────────────────

@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """Basic service health status"""
    return HealthResponse(
        status="ok",
        timestamp=datetime.utcnow().isoformat() + "Z",
        version="1.0.0"
    )

@app.post("/auth/login", response_model=LoginResponse, tags=["Authentication"])
async def login(request: LoginRequest):
    """Generate JWT token for valid credentials"""
    user = USERS.get(request.username)
    if not user or not pwd_ctx.verify(request.password, user["password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )
    token = create_token(user["username"], user["role"])
    return LoginResponse(
        access_token=token,
        token_type="bearer",
        role=user["role"],
        full_name=user["full_name"],
        expires_in=JWT_EXPIRE_HOURS * 3600
    )

@app.post("/auth/signup", tags=["Authentication"])
async def signup(request: SignupRequest):
    """Register a new user"""
    if request.username in USERS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists"
        )
    
    USERS[request.username] = {
        "username": request.username,
        "password": pwd_ctx.hash(request.password),
        "role": "user",  # Default role
        "full_name": request.full_name
    }
    
    return {"message": "User created successfully", "username": request.username}

@app.post("/rag/query", response_model=QueryResponse, tags=["RAG"])
async def rag_query(request: QueryRequest, user: dict = Depends(get_current_user)):
    """
    Accept a natural language question and return a generated answer.
    Requires valid JWT token (Admin or User role).
    """
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")

    # 1. Get Pinecone host
    host = await get_pinecone_host()

    # 2. Embed the query
    query_vector = await embed_query(request.question)

    # 3. Retrieve relevant chunks from Pinecone
    matches = await query_vectors(host, query_vector, top_k=TOP_K)

    if not matches:
        return QueryResponse(
            answer="I could not find relevant information in the knowledge base to answer your question. Please ensure documents have been uploaded and indexed.",
            sources=[],
            chunks_used=0
        )

    # 4. Extract context and sources
    context_chunks = []
    sources = []
    for match in matches:
        meta = match.get("metadata", {})
        text = meta.get("text", "")
        source = meta.get("source", "unknown")
        if text:
            context_chunks.append(text)
        if source not in sources:
            sources.append(source)

    # 5. Generate answer with Groq LLM
    answer = await generate_answer(request.question, context_chunks)

    return QueryResponse(
        answer=answer,
        sources=sources,
        chunks_used=len(context_chunks)
    )

@app.post("/ingest/upload", response_model=IngestResponse, tags=["Ingestion"])
async def ingest_pdf(
    file: UploadFile = File(...),
    user: dict = Depends(get_current_user)
):
    """
    Upload and index a PDF document into Pinecone.
    Requires Admin role.
    """
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    # Read file
    file_bytes = await file.read()
    if len(file_bytes) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    # Extract text
    try:
        text = extract_text_from_pdf(file_bytes)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to read PDF: {str(e)}")

    if not text.strip():
        raise HTTPException(status_code=400, detail="No extractable text found in PDF")

    # Chunk text
    chunks = chunk_text(text)
    if not chunks:
        raise HTTPException(status_code=400, detail="No content chunks generated from PDF")

    # Get Pinecone host
    host = await get_pinecone_host()

    # Embed chunks in batches of 20
    batch_size = 20
    all_embeddings = []
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i:i + batch_size]
        embeddings = await embed_text(batch)
        all_embeddings.extend(embeddings)

    # Prepare vectors for upsert
    doc_id = hashlib.md5(file.filename.encode()).hexdigest()[:8]
    vectors = []
    for i, (chunk, embedding) in enumerate(zip(chunks, all_embeddings)):
        vectors.append({
            "id": f"{doc_id}-chunk-{i}",
            "values": embedding,
            "metadata": {
                "text": chunk,
                "source": file.filename,
                "chunk_index": i,
                "total_chunks": len(chunks)
            }
        })

    # Upsert to Pinecone in batches of 100
    upsert_batch = 100
    for i in range(0, len(vectors), upsert_batch):
        await upsert_vectors(host, vectors[i:i + upsert_batch])

    return IngestResponse(
        message=f"Successfully indexed '{file.filename}' into Pinecone",
        filename=file.filename,
        chunks_indexed=len(chunks)
    )

@app.get("/users/me", tags=["Users"])
async def get_me(user: dict = Depends(get_current_user)):
    """Get current user info"""
    return {
        "username": user["username"],
        "role": user["role"],
        "full_name": user["full_name"]
    }

@app.get("/users/list", tags=["Users"])
async def list_users(user: dict = Depends(require_admin)):
    """List all users (Admin only)"""
    return [
        {"username": u["username"], "role": u["role"], "full_name": u["full_name"]}
        for u in USERS.values()
    ]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=False)
