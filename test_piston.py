import requests

payload = {
    "language": "python",
    "version": "3.10.0",
    "files": [
        {
            "name": "main.py",
            "content": "print('Hello from Piston!')"
        }
    ]
}

try:
    response = requests.post("https://emacs.ch/piston/api/v2/execute", json=payload, timeout=5)
    print("Piston emacs.ch:", response.status_code, response.text)
except Exception as e:
    print("Piston emacs.ch failed:", e)

try:
    response = requests.post("https://piston.codes/api/v2/execute", json=payload, timeout=5)
    print("Piston codes:", response.status_code, response.text)
except Exception as e:
    print("Piston codes failed:", e)
