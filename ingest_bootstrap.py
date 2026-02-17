import requests
import os

# Configuration
API_BASE = "http://127.0.0.1:8000"
USERNAME = "admin"
PASSWORD = "admin123"
PDF_FILE = "You-are-the-World.pdf"

def ingest_file():
    print(f"🔹 Starting ingestion for: {PDF_FILE}")
    
    # 1. Login to get Admin Token
    print("🔹 Authenticating as Admin...")
    try:
        auth_resp = requests.post(
            f"{API_BASE}/auth/login",
            json={"username": USERNAME, "password": PASSWORD}
        )
    except requests.exceptions.ConnectionError:
        print("❌ Error: Could not connect to backend. Is uvicorn running?")
        return

    if auth_resp.status_code != 200:
        print(f"❌ Authentication failed: {auth_resp.text}")
        return

    token = auth_resp.json()["access_token"]
    print("✅ Authenticated successfully.")

    # 2. Upload File
    if not os.path.exists(PDF_FILE):
        print(f"❌ Error: File '{PDF_FILE}' not found in current directory.")
        return

    print("🔹 Uploading and Indexing PDF (this may take a few seconds)...")
    with open(PDF_FILE, "rb") as f:
        files = {"file": (PDF_FILE, f, "application/pdf")}
        headers = {"Authorization": f"Bearer {token}"}
        
        try:
            upload_resp = requests.post(
                f"{API_BASE}/ingest/upload",
                headers=headers,
                files=files
            )
            
            if upload_resp.status_code == 200:
                data = upload_resp.json()
                print("✅ Success!")
                print(f"📄 Filename: {data['filename']}")
                print(f"📚 Chunks Indexed: {data['chunks_indexed']}")
                print(f"💬 Message: {data['message']}")
            else:
                print(f"❌ Upload failed: {upload_resp.text}")
                
        except Exception as e:
            print(f"❌ Error during upload: {str(e)}")

if __name__ == "__main__":
    ingest_file()
