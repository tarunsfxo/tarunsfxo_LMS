from blueprints.coding import execute_local

code = """
import sys
def solve():
    input_data = sys.stdin.read().strip().split('\\n')
    if len(input_data) < 2: return
    nums = eval(input_data[0])
    target = int(input_data[1])
    
    seen = {}
    for i, num in enumerate(nums):
        diff = target - num
        if diff in seen:
            print(f"[{seen[diff]},{i}]")
            return
        seen[num] = i

if __name__ == '__main__':
    solve()
"""

# Two Sum Test Case 1
input_data = "[2,7,11,15]\n9"
expected_output = "[0,1]"

print("Running Python Code...")
result = execute_local("python", code, input_data, time_limit=2.0)

print("Result Status:", result['status'])
print("Actual Output:", repr(result['output']))

if result['status'] == "Success":
    if result['output'].strip() == expected_output.strip():
        print("Verdict: Accepted ✅")
    else:
        print("Verdict: Wrong Answer ❌")
