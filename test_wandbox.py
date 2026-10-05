import requests

compilers = {
    "c": "gcc-head-c",
    "cpp": "gcc-head",
    "python": "cpython-3.11.4",
    "javascript": "nodejs-20.17.0"
}

codes = {
    "c": '#include <stdio.h>\nint main() { printf("c works"); return 0; }',
    "cpp": '#include <iostream>\nint main() { std::cout << "cpp works"; return 0; }',
    "python": 'print("python works")',
    "javascript": 'console.log("js works")'
}

for lang, comp in compilers.items():
    payload = {
        "compiler": comp,
        "code": codes[lang],
        "stdin": ""
    }
    res = requests.post("https://wandbox.org/api/compile.json", json=payload, timeout=10)
    print(lang, res.status_code, res.text[:100])
