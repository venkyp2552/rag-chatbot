import os
import sys
import httpx
import asyncio
from dotenv import load_dotenv

load_dotenv()

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_INDEX = os.getenv("PINECONE_INDEX")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

print(f"PINECONE_API_KEY: {PINECONE_API_KEY[:5]}...")
print(f"PINECONE_INDEX: {PINECONE_INDEX}")
print(f"GROQ_API_KEY: {GROQ_API_KEY[:5]}...")

async def check_pinecone():
    print("\nChecking Pinecone...")
    headers = {
        "Api-Key": PINECONE_API_KEY,
        "Content-Type": "application/json",
        "X-Pinecone-API-Version": "2025-04"
    }
    url = f"https://api.pinecone.io/indexes/{PINECONE_INDEX}"
    async with httpx.AsyncClient() as client:
        try:
            r = await client.get(url, headers=headers)
            print(f"Status Code: {r.status_code}")
            if r.status_code == 200:
                data = r.json()
                print(f"Host: {data.get('host')}")
                print(f"Dimension: {data.get('spec', {}).get('serverless', {}).get('dimension')}")
                return True
            else:
                print(f"Error: {r.text}")
                return False
        except Exception as e:
            print(f"Exception: {e}")
            return False

async def check_groq():
    print("\nChecking Groq...")
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    url = "https://api.groq.com/openai/v1/models"
    async with httpx.AsyncClient() as client:
        try:
            r = await client.get(url, headers=headers)
            print(f"Status Code: {r.status_code}")
            if r.status_code == 200:
                print("Groq functional.")
                return True
            else:
                print(f"Error: {r.text}")
                return False
        except Exception as e:
            print(f"Exception: {e}")
            return False

async def main():
    p = await check_pinecone()
    g = await check_groq()
    if p and g:
        print("\nAll checks passed.")
    else:
        print("\nSome checks failed.")

if __name__ == "__main__":
    asyncio.run(main())
