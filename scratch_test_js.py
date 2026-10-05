from blueprints.coding import execute_local

code = """
const fs = require('fs');

function solve() {
    const inputData = fs.readFileSync('/dev/stdin', 'utf-8').trim();
    console.log("Input was: " + inputData);
}

solve();
"""

res = execute_local("javascript", code, "hello world\n", 1.0)
print(res)
