import sys
import logging

logging.basicConfig(level=logging.DEBUG)

# Just test redis directly to see what n8n does
import json
import httpx
import urllib.parse

# If n8n runs locally on 5678, we can't easily trigger the redis trigger
# But let's check if the flask internal endpoint works!
payload = {
    "user_id": 1,
    "email": "test@example.com",
    "username": "testuser",
    "category_id": 1,
    "cert_code": "12345"
}

try:
    resp = httpx.post("http://127.0.0.1:5000/n8n/api/internal/render-email", json={
        "event": "course_completed",
        "payload": payload
    })
    print(resp.status_code)
    print(resp.text)
except Exception as e:
    print(e)
