#!/usr/bin/env python3
import httpx
import json
import sys
from pathlib import Path

print("Starting quick test...")
sys.stdout.flush()

base_url = "http://localhost:8000"
client = httpx.Client(timeout=30.0)

# Create collection
print("Creating collection...")
sys.stdout.flush()
resp = client.post(f"{base_url}/api/collections/create", data={"collection_name": "quick_test"})
print(f"Collection creation: {resp.status_code}")
print(resp.json())
sys.stdout.flush()

# Upload 5-page PDF
pdf_path = Path("tests/fixtures/classroom_music_5pages.pdf")
if pdf_path.exists():
    print(f"\nUploading {pdf_path.name}...")
    sys.stdout.flush()

    with open(pdf_path, "rb") as f:
        files = {"files": (pdf_path.name, f, "application/octet-stream")}
        data = {"collection_name": "quick_test"}
        resp = client.post(f"{base_url}/api/ingest/upload", files=files, data=data)

    print(f"Upload status: {resp.status_code}")
    result = resp.json()
    task_id = result["task_id"]
    print(f"Task ID: {task_id}")
    print(json.dumps(result, indent=2))
    sys.stdout.flush()

    # Poll status
    print("\nPolling status...")
    sys.stdout.flush()
    for i in range(60):
        resp = client.get(f"{base_url}/api/ingest/status/{task_id}")
        data = resp.json()
        print(f"  [{i}] Status: {data['status']}, Progress: {data['progress']:.1f}%")
        sys.stdout.flush()

        if data['status'] == 'completed':
            print("✓ COMPLETED")
            break
        elif data['status'] == 'failed':
            print("✗ FAILED")
            print(data)
            break

        import time
        time.sleep(2)
else:
    print(f"PDF not found: {pdf_path}")
