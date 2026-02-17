"""
RAG Application - Streamlit Frontend
Connects to FastAPI backend at http://localhost:8000
"""

import streamlit as st
import requests
import json
import time
from datetime import datetime

# ─────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────
import os

# ─────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────
API_BASE = os.getenv("API_BASE", "http://127.0.0.1:8000")

# ─────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="You Are The World",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─────────────────────────────────────────────
# CUSTOM CSS
# ─────────────────────────────────────────────
st.markdown("""
<style>
    /* Main theme */
    .main-header {
        background: linear-gradient(135deg, #4A5D4E 0%, #2F4F4F 100%);
        padding: 2rem;
        border-radius: 12px;
        color: #F8F9FA;
        margin-bottom: 2rem;
        text-align: center;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    .main-header h1 { font-size: 2.2rem; margin: 0; font-weight: 700; }
    .main-header p  { font-size: 1rem; margin: 0.5rem 0 0; opacity: 0.9; }

    /* Role badges */
    .badge-admin {
        background: linear-gradient(135deg, #f093fb, #f5576c);
        color: white; padding: 3px 12px; border-radius: 20px;
        font-size: 0.75rem; font-weight: 600;
    }
    .badge-user {
        background: linear-gradient(135deg, #4facfe, #00f2fe);
        color: white; padding: 3px 12px; border-radius: 20px;
        font-size: 0.75rem; font-weight: 600;
    }

    /* Chat messages */
    .chat-user {
        background: linear-gradient(135deg, #4A5D4E, #6B8E23);
        color: white; padding: 1rem 1.2rem; border-radius: 18px 18px 4px 18px;
        margin: 0.5rem 0; max-width: 80%; margin-left: auto;
    }
    .chat-assistant {
        background: #f8f9fa; border: 1px solid #e9ecef;
        color: #212529; padding: 1rem 1.2rem; border-radius: 18px 18px 18px 4px;
        margin: 0.5rem 0; max-width: 85%;
    }
    .chat-meta {
        font-size: 0.72rem; opacity: 0.6; margin-top: 0.3rem;
    }

    /* Sources card */
    .sources-card {
        background: #fff3cd; border: 1px solid #ffc107;
        border-radius: 8px; padding: 0.6rem 1rem;
        margin-top: 0.5rem; font-size: 0.82rem;
    }

    /* Upload area */
    .upload-section {
        background: linear-gradient(135deg, #a8edea, #fed6e3);
        border-radius: 12px; padding: 1.5rem; margin: 1rem 0;
    }

    /* Stats card */
    .stat-card {
        background: white; border-radius: 10px; padding: 1rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08); text-align: center;
    }
    .stat-number { font-size: 1.8rem; font-weight: 700; color: #667eea; }
    .stat-label  { font-size: 0.8rem; color: #6c757d; margin-top: 0.2rem; }

    /* Login card */
    .login-card {
        max-width: 420px; margin: 3rem auto;
        background: white; border-radius: 16px;
        padding: 2rem; box-shadow: 0 8px 32px rgba(0,0,0,0.12);
    }

    /* Success / Error banners */
    .success-banner {
        background: #d4edda; border: 1px solid #c3e6cb;
        color: #155724; padding: 0.8rem 1rem; border-radius: 8px;
    }
    .error-banner {
        background: #f8d7da; border: 1px solid #f5c6cb;
        color: #721c24; padding: 0.8rem 1rem; border-radius: 8px;
    }

    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stDeployButton {display: none;}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# SESSION STATE INIT
# ─────────────────────────────────────────────
def init_session():
    defaults = {
        "token": None,
        "username": None,
        "role": None,
        "full_name": None,
        "chat_history": [],
        "total_queries": 0,
        "total_docs": 0,
        "total_chunks": 0,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_session()

# ─────────────────────────────────────────────
# API HELPERS
# ─────────────────────────────────────────────
def api_login(username: str, password: str) -> dict:
    try:
        r = requests.post(
            f"{API_BASE}/auth/login",
            json={"username": username, "password": password},
            timeout=10
        )
        return r.json() if r.status_code == 200 else {"error": r.json().get("detail", "Login failed")}
    except requests.exceptions.ConnectionError:
        return {"error": "⚠️ Cannot connect to backend. Is the FastAPI server running on port 8000?"}
    except Exception as e:
        return {"error": str(e)}

def api_signup(username: str, password: str, full_name: str) -> dict:
    try:
        r = requests.post(
            f"{API_BASE}/auth/signup",
            json={"username": username, "password": password, "full_name": full_name},
            timeout=10
        )
        return r.json() if r.status_code == 200 else {"error": r.json().get("detail", "Signup failed")}
    except requests.exceptions.ConnectionError:
        return {"error": "Cannot connect to backend"}
    except Exception as e:
        return {"error": str(e)}

def api_query(question: str) -> dict:
    try:
        r = requests.post(
            f"{API_BASE}/rag/query",
            json={"question": question},
            headers={"Authorization": f"Bearer {st.session_state.token}"},
            timeout=60
        )
        return r.json() if r.status_code == 200 else {"error": r.json().get("detail", "Query failed")}
    except requests.exceptions.ConnectionError:
        return {"error": "Cannot connect to backend"}
    except Exception as e:
        return {"error": str(e)}

def api_upload(file_bytes: bytes, filename: str) -> dict:
    try:
        r = requests.post(
            f"{API_BASE}/ingest/upload",
            files={"file": (filename, file_bytes, "application/pdf")},
            headers={"Authorization": f"Bearer {st.session_state.token}"},
            timeout=120
        )
        return r.json() if r.status_code == 200 else {"error": r.json().get("detail", "Upload failed")}
    except requests.exceptions.ConnectionError:
        return {"error": "Cannot connect to backend"}
    except Exception as e:
        return {"error": str(e)}

def api_health() -> dict:
    try:
        r = requests.get(f"{API_BASE}/health", timeout=5)
        return r.json() if r.status_code == 200 else {"status": "error"}
    except:
        return {"status": "offline"}

def api_list_users() -> list:
    try:
        r = requests.get(
            f"{API_BASE}/users/list",
            headers={"Authorization": f"Bearer {st.session_state.token}"},
            timeout=10
        )
        return r.json() if r.status_code == 200 else []
    except:
        return []

# ─────────────────────────────────────────────
# LOGIN PAGE
# ─────────────────────────────────────────────
def show_login():
    st.markdown("""
    <div class="main-header">
        <h1>🌿 You Are The World</h1>
        <p>Explore the timeless wisdom of J. Krishnamurti through AI</p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        # Health check indicator
        health = api_health()
        if health.get("status") == "ok":
            st.success("✅ Backend is online")
        else:
            st.error("❌ Backend offline — start the FastAPI server first (`uvicorn backend:app --reload`)")

        tab1, tab2 = st.tabs(["🔐 Sign In", "📝 Sign Up"])

        with tab1:
            st.markdown("### Welcome Back")
            with st.form("login_form"):
                username = st.text_input("Username", placeholder="admin / user1")
                password = st.text_input("Password", type="password", placeholder="Password")
                submitted = st.form_submit_button("Sign In 🚀", use_container_width=True)

                if submitted:
                    if not username or not password:
                        st.error("Please enter both username and password")
                    else:
                        with st.spinner("Authenticating..."):
                            result = api_login(username, password)
                        if "error" in result:
                            st.error(result["error"])
                        else:
                            st.session_state.token     = result["access_token"]
                            st.session_state.username  = username
                            st.session_state.role      = result["role"]
                            st.session_state.full_name = result["full_name"]
                            st.success(f"Welcome, {result['full_name']}!")
                            time.sleep(0.5)
                            st.rerun()

        with tab2:
            st.markdown("### Create Account")
            with st.form("signup_form"):
                new_user = st.text_input("Choose Username", placeholder="johndoe")
                new_pass = st.text_input("Choose Password", type="password", placeholder="Minimum 4 characters")
                new_name = st.text_input("Full Name", placeholder="John Doe")
                signup_submitted = st.form_submit_button("Create Account ✨", use_container_width=True)

                if signup_submitted:
                    if not new_user or not new_pass or not new_name:
                        st.error("All fields are required")
                    else:
                        with st.spinner("Creating account..."):
                            result = api_signup(new_user, new_pass, new_name)
                        
                        if "error" in result:
                            st.error(result["error"])
                        else:
                            st.success("✅ Account created! Please switch to the Sign In tab to log in.")

        st.markdown("---")
        st.markdown("**Demo Accounts:**")
        st.code("admin  / admin123  → Admin role\nuser1  / user123   → User role")

# ─────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────
def show_sidebar():
    with st.sidebar:
        # User info
        badge = "badge-admin" if st.session_state.role == "admin" else "badge-user"
        role_label = st.session_state.role.capitalize()
        st.markdown(f"""
        <div style='text-align:center; padding: 1rem 0;'>
            <div style='font-size:3rem;'>{'👑' if st.session_state.role == 'admin' else '👤'}</div>
            <div style='font-weight:600; font-size:1.1rem;'>{st.session_state.full_name}</div>
            <div style='color:#6c757d; font-size:0.85rem;'>@{st.session_state.username}</div>
            <span class='{badge}'>{role_label}</span>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("---")

        # Navigation
        st.markdown("### 📍 Navigation")
        pages = ["💬 Chat", "📄 Upload Documents", "📊 Dashboard"]
        if st.session_state.role == "admin":
            pages.append("👥 Manage Users")

        if "current_page" not in st.session_state:
            st.session_state.current_page = "💬 Chat"

        for page in pages:
            if st.button(page, use_container_width=True,
                         type="primary" if st.session_state.current_page == page else "secondary"):
                st.session_state.current_page = page
                st.rerun()

        st.markdown("---")

        # Stats
        st.markdown("### 📈 Session Stats")
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Queries", st.session_state.total_queries)
        with col2:
            st.metric("Docs Indexed", st.session_state.total_docs)

        st.markdown("---")

        # Backend health
        health = api_health()
        status_icon = "🟢" if health.get("status") == "ok" else "🔴"
        st.markdown(f"**Backend Status:** {status_icon} {health.get('status', 'unknown').upper()}")

        st.markdown("---")

        # Logout
        if st.button("🚪 Logout", use_container_width=True):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

# ─────────────────────────────────────────────
# CHAT PAGE
# ─────────────────────────────────────────────
def show_chat():
    st.markdown("""
    <div class="main-header">
        <h1>💬 Philosophical Dialogue</h1>
        <p>Inquire freely. "Freedom is not a reaction; freedom is not a choice."</p>
    </div>
    """, unsafe_allow_html=True)

    # Chat history display
    chat_container = st.container()
    with chat_container:
        if not st.session_state.chat_history:
            st.info("👋 No conversations yet. Ask a question below to get started!")
        else:
            for msg in st.session_state.chat_history:
                if msg["role"] == "user":
                    st.markdown(f"""
                    <div class="chat-user">
                        <strong>You</strong><br>{msg['content']}
                        <div class="chat-meta">{msg.get('timestamp','')}</div>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    sources_html = ""
                    if msg.get("sources"):
                        src_list = ", ".join(msg["sources"])
                        sources_html = f"""<div class="sources-card">
                            📚 <strong>Sources:</strong> {src_list} &nbsp;|&nbsp;
                            🔢 <strong>Chunks used:</strong> {msg.get('chunks_used', 0)}
                        </div>"""
                    st.markdown(f"""
                    <div class="chat-assistant">
                        <strong>🌿 Krishnamurti AI</strong><br>{msg['content']}
                        <div class="chat-meta">{msg.get('timestamp','')}</div>
                        {sources_html}
                    </div>
                    """, unsafe_allow_html=True)

    st.markdown("---")

    # Input area
    col1, col2 = st.columns([5, 1])
    with col1:
        question = st.text_input(
            "Ask a question",
            placeholder="e.g. What is the nature of fear?",
            label_visibility="collapsed"
        )
    with col2:
        ask_btn = st.button("Ask 🚀", use_container_width=True, type="primary")

    # Quick suggestions
    st.markdown("**Suggested Inquiries:**")
    suggestions = [
        "What is the cause of conflict?",
        "Can the mind be free from fear?",
        "Why do we compare ourselves?",
        "What is true love?"
    ]
    cols = st.columns(len(suggestions))
    for i, suggestion in enumerate(suggestions):
        with cols[i]:
            if st.button(suggestion, use_container_width=True, key=f"sug_{i}"):
                question = suggestion
                ask_btn = True

    # Process query
    if ask_btn and question:
        ts = datetime.now().strftime("%I:%M %p")
        st.session_state.chat_history.append({
            "role": "user",
            "content": question,
            "timestamp": ts
        })

        with st.spinner("🔍 Searching knowledge base and generating answer..."):
            result = api_query(question)

        if "error" in result:
            st.session_state.chat_history.append({
                "role": "assistant",
                "content": f"❌ Error: {result['error']}",
                "timestamp": datetime.now().strftime("%I:%M %p"),
                "sources": [],
                "chunks_used": 0
            })
        else:
            st.session_state.total_queries += 1
            st.session_state.chat_history.append({
                "role": "assistant",
                "content": result["answer"],
                "timestamp": datetime.now().strftime("%I:%M %p"),
                "sources": result.get("sources", []),
                "chunks_used": result.get("chunks_used", 0)
            })

        st.rerun()

    # Clear chat
    if st.session_state.chat_history:
        if st.button("🗑️ Clear Chat History"):
            st.session_state.chat_history = []
            st.rerun()

# ─────────────────────────────────────────────
# UPLOAD PAGE (Admin only)
# ─────────────────────────────────────────────
def show_upload():
    st.markdown("""
    <div class="main-header">
        <h1>📄 Document Ingestion</h1>
        <p>Upload PDFs to index them into the Pinecone knowledge base</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="upload-section">
        <h4>📋 How it works</h4>
        <ol>
            <li>Upload one or more PDF files below</li>
            <li>Text is extracted and split into chunks (800 words, 100 overlap)</li>
            <li>Each chunk is embedded using <code>llama-text-embed-v2</code> via Pinecone</li>
            <li>Vectors are stored in your <strong>own-rag</strong> Pinecone index</li>
            <li>Documents become instantly queryable via the Chat tab</li>
        </ol>
    </div>
    """, unsafe_allow_html=True)

    uploaded_files = st.file_uploader(
        "Drop your PDFs here",
        type=["pdf"],
        accept_multiple_files=True,
        help="Upload one or more PDF files to add to the knowledge base"
    )

    if uploaded_files:
        st.markdown(f"**{len(uploaded_files)} file(s) selected:**")
        for f in uploaded_files:
            size_kb = len(f.getvalue()) / 1024
            st.markdown(f"- 📄 `{f.name}` ({size_kb:.1f} KB)")

        if st.button("⬆️ Upload & Index All", type="primary", use_container_width=True):
            results = []
            progress = st.progress(0)
            status_text = st.empty()

            for i, uploaded_file in enumerate(uploaded_files):
                status_text.text(f"Processing {uploaded_file.name}...")
                file_bytes = uploaded_file.getvalue()
                result = api_upload(file_bytes, uploaded_file.name)
                results.append((uploaded_file.name, result))
                progress.progress((i + 1) / len(uploaded_files))

            status_text.text("Done!")
            st.markdown("---")
            st.markdown("### Results")

            total_chunks = 0
            for fname, result in results:
                if "error" in result:
                    st.error(f"❌ **{fname}**: {result['error']}")
                else:
                    chunks = result.get("chunks_indexed", 0)
                    total_chunks += chunks
                    st.success(f"✅ **{fname}**: {chunks} chunks indexed successfully")
                    st.session_state.total_docs += 1
                    st.session_state.total_chunks += chunks

            if total_chunks > 0:
                st.balloons()
                st.info(f"🎉 Total: **{total_chunks} chunks** indexed across {len(uploaded_files)} document(s)")

# ─────────────────────────────────────────────
# DASHBOARD PAGE
# ─────────────────────────────────────────────
def show_dashboard():
    st.markdown("""
    <div class="main-header">
        <h1>📊 Dashboard</h1>
        <p>Session overview and system status</p>
    </div>
    """, unsafe_allow_html=True)

    # Stats row
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""<div class="stat-card">
            <div class="stat-number">{st.session_state.total_queries}</div>
            <div class="stat-label">Total Queries</div>
        </div>""", unsafe_allow_html=True)
    with col2:
        st.markdown(f"""<div class="stat-card">
            <div class="stat-number">{st.session_state.total_docs}</div>
            <div class="stat-label">Docs Indexed</div>
        </div>""", unsafe_allow_html=True)
    with col3:
        st.markdown(f"""<div class="stat-card">
            <div class="stat-number">{st.session_state.total_chunks}</div>
            <div class="stat-label">Chunks Stored</div>
        </div>""", unsafe_allow_html=True)
    with col4:
        st.markdown(f"""<div class="stat-card">
            <div class="stat-number">{len(st.session_state.chat_history) // 2}</div>
            <div class="stat-label">Conversations</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 🔧 System Configuration")
        config = {
            "LLM Model": "llama-3.3-70b-versatile",
            "LLM Provider": "Groq",
            "Embedding Model": "llama-text-embed-v2",
            "Vector DB": "Pinecone",
            "Pinecone Index": "own-rag",
            "Embedding Dimension": "1024",
            "Chunk Size": "800 words",
            "Chunk Overlap": "100 words",
            "Top-K Retrieval": "5",
            "JWT Expiry": "24 hours"
        }
        for k, v in config.items():
            col_a, col_b = st.columns([2, 3])
            col_a.markdown(f"**{k}**")
            col_b.markdown(f"`{v}`")

    with col2:
        st.markdown("### 🌐 API Endpoints")
        endpoints = [
            ("POST", "/auth/login", "Get JWT token"),
            ("POST", "/rag/query", "Ask a question"),
            ("POST", "/ingest/upload", "Upload PDF (Admin)"),
            ("GET",  "/health",       "Service health"),
            ("GET",  "/users/me",     "Current user info"),
            ("GET",  "/users/list",   "List users (Admin)"),
        ]
        for method, path, desc in endpoints:
            color = "#28a745" if method == "GET" else "#007bff"
            st.markdown(f"""
            <div style='display:flex; align-items:center; gap:10px; margin:6px 0; 
                        background:#f8f9fa; padding:6px 10px; border-radius:6px;'>
                <span style='background:{color}; color:white; padding:2px 8px; 
                             border-radius:4px; font-size:0.75rem; font-weight:600;'>{method}</span>
                <code style='flex:1;'>{path}</code>
                <span style='color:#6c757d; font-size:0.82rem;'>{desc}</span>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("### 🏥 Backend Health")
        health = api_health()
        if health.get("status") == "ok":
            st.success(f"✅ Online — {health.get('timestamp', '')[:19].replace('T', ' ')}")
        else:
            st.error("❌ Backend is offline")
            st.code("uvicorn backend:app --reload --port 8000")

# ─────────────────────────────────────────────
# USERS PAGE (Admin only)
# ─────────────────────────────────────────────
def show_users():
    st.markdown("""
    <div class="main-header">
        <h1>👥 User Management</h1>
        <p>View and manage system users (Admin only)</p>
    </div>
    """, unsafe_allow_html=True)

    users = api_list_users()
    if users:
        st.markdown(f"**{len(users)} registered users:**")
        for u in users:
            badge = "badge-admin" if u["role"] == "admin" else "badge-user"
            icon = "👑" if u["role"] == "admin" else "👤"
            st.markdown(f"""
            <div style='display:flex; align-items:center; gap:15px; background:#f8f9fa;
                        padding:12px 16px; border-radius:10px; margin:8px 0;
                        border-left: 4px solid {"#f5576c" if u["role"] == "admin" else "#4facfe"};'>
                <span style='font-size:1.5rem;'>{icon}</span>
                <div>
                    <strong>{u["full_name"]}</strong>
                    <span style='color:#6c757d; font-size:0.85rem;'> @{u["username"]}</span>
                </div>
                <span class='{badge}' style='margin-left:auto;'>{u["role"].capitalize()}</span>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.warning("Could not fetch user list")

    st.markdown("---")
    st.markdown("### Default Credentials")
    st.code("""
Username: admin  | Password: admin123 | Role: Admin
Username: user1  | Password: user123  | Role: User
Username: user2  | Password: user456  | Role: User
    """)
    st.info("💡 To add more users, edit the `USERS` dictionary in `backend.py`")

# ─────────────────────────────────────────────
# MAIN ROUTER
# ─────────────────────────────────────────────
def main():
    if not st.session_state.token:
        show_login()
    else:
        show_sidebar()
        page = st.session_state.get("current_page", "💬 Chat")

        if page == "💬 Chat":
            show_chat()
        elif page == "📊 Dashboard":
            show_dashboard()
        elif page == "📄 Upload Documents":
            show_upload()
        elif page == "👥 Manage Users":
            if st.session_state.role == "admin":
                show_users()
            else:
                st.error("❌ Admin access required for this page")

if __name__ == "__main__":
    main()
