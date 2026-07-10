import requests

payload = {
    "language": "python",
    "version": "3.10.0",
    "files": [{"name": "main.py", "content": "print('hello')"}]
}
try:
    response = requests.post("https://emacs.ch/api/v2/piston/execute", json=payload, timeout=5)
    print("emacs v2:", response.status_code, response.text[:100])
except Exception as e: pass

try:
    response = requests.get("https://emacs.ch/api/v2/piston/runtimes", timeout=5)
    print("runtimes:", response.status_code, response.text[:100])
except Exception as e: pass
