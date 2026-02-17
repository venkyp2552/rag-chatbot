import os
import sys
import httpx
import asyncio
from dotenv import load_dotenv

load_dotenv()

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_INDEX = os.getenv("PINECONE_INDEX")
DIMENSION = 1024

async def validate_index():
    print("Validating Pinecone Index Compatibility...")
    headers = {
        "Api-Key": PINECONE_API_KEY,
        "Content-Type": "application/json",
        "X-Pinecone-API-Version": "2025-04"
    }

    # Get Host first
    host_url = f"https://api.pinecone.io/indexes/{PINECONE_INDEX}"
    async with httpx.AsyncClient() as client:
        r = await client.get(host_url, headers=headers)
        if r.status_code != 200:
            print(f"Failed to get index info: {r.text}")
            return False
        
        info = r.json()
        host = f"https://{info['host']}"
        print(f"Index Host: {host}")

        # Try to upsert a dummy vector
        upsert_url = f"{host}/vectors/upsert"
        dummy_vector = {
            "vectors": [
                {
                    "id": "validation_test",
                    "values": [0.1] * DIMENSION, 
                    "metadata": {"source": "validation"}
                }
            ]
        }
        
        r_upsert = await client.post(upsert_url, json=dummy_vector, headers=headers)
        if r_upsert.status_code == 200:
            print("Successfully upserted dummy vector with dimension 1024. Index is compatible.")
            # Cleanup
            del_url = f"{host}/vectors/delete"
            await client.post(del_url, json={"ids": ["validation_test"]}, headers=headers)
            return True
        else:
            print(f"Failed to upsert vector. Error: {r_upsert.text}")
            if "dimension mismatch" in r_upsert.text.lower():
                print("CRITICAL ISSUE: Index dimension mismatch! Expected 1024.")
            return False

if __name__ == "__main__":
    asyncio.run(validate_index())
