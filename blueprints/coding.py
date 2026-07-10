from flask import Blueprint, jsonify, request, render_template
from flask_login import login_required, current_user
from models import CodingProblem, CodingSubmission, CodingTestCase, CodingTag, db
import requests
import json
import os

coding_bp = Blueprint("coding", __name__, url_prefix="/coding")

# Base route that serves the React App container
@coding_bp.route("/")
@coding_bp.route("/<path:path>")
@login_required
def index(path=""):
    return render_template("coding_app.html")


# API Routes for React Frontend
@coding_bp.route("/api/problems", methods=["GET"])
@login_required
def get_problems():
    problems = CodingProblem.query.filter_by(is_published=True).all()
    result = []
    for p in problems:
        # Check if user solved it
        solved = CodingSubmission.query.filter_by(
            user_id=current_user.id, problem_id=p.id, verdict="Accepted"
        ).first() is not None
        
        result.append({
            "id": p.id,
            "title": p.title,
            "slug": p.slug,
            "difficulty": p.difficulty,
            "tags": [t.name for t in p.tags],
            "solved": solved
        })
    return jsonify(result)


@coding_bp.route("/api/problems/<slug>", methods=["GET"])
@login_required
def get_problem_detail(slug):
    p = CodingProblem.query.filter_by(slug=slug, is_published=True).first_or_404()
    
    visible_test_cases = []
    for tc in p.test_cases:
        if not tc.is_hidden:
            visible_test_cases.append({
                "id": tc.id,
                "input_data": tc.input_data,
                "expected_output": tc.expected_output,
                "explanation": tc.explanation
            })
            
    return jsonify({
        "id": p.id,
        "title": p.title,
        "description": p.description,
        "difficulty": p.difficulty,
        "time_limit": p.time_limit,
        "memory_limit": p.memory_limit,
        "tags": [t.name for t in p.tags],
        "test_cases": visible_test_cases
    })


import tempfile
import subprocess
import time

@coding_bp.route("/api/submit", methods=["POST"])
@login_required
def submit_code():
    data = request.json or {}
    problem_id = data.get("problem_id")
    language = data.get("language", "python")
    code = data.get("code", "")
    
    problem = CodingProblem.query.get(problem_id)
    if not problem:
        return jsonify({"verdict": "Error", "output": "Problem not found", "runtime": 0, "memory": 0}), 404
    
    submission = CodingSubmission(
        user_id=current_user.id,
        problem_id=problem.id,
        language=language,
        code=code,
        verdict="Running"
    )
    db.session.add(submission)
    db.session.commit()

    verdict = "Accepted"
    max_runtime = 0
    max_memory = 0
    final_output = ""
    
    # We will test against the first visible test case for immediate feedback
    test_cases = problem.test_cases.all()
    if not test_cases:
        test_cases = [CodingTestCase(input_data="", expected_output="")]

    for tc in test_cases:
        inp = tc.input_data or ""
        exp_out = tc.expected_output or ""
        result = execute_local(language, code, inp, problem.time_limit)
        final_output = result["output"]
        
        if result["status"] == "Time Limit Exceeded":
            verdict = "Time Limit Exceeded"
            max_runtime = problem.time_limit
            break
        elif result["status"] == "Compilation Error":
            verdict = "Compilation Error"
            break
        elif result["status"] == "Runtime Error":
            verdict = "Runtime Error"
            break
        else:
            # Check output
            expected = exp_out.strip()
            actual = result["output"].strip()
            max_runtime = max(max_runtime, result["runtime"])
            
            if expected != actual:
                verdict = "Wrong Answer"
                final_output = f"Expected:\n{expected}\n\nGot:\n{actual}"
                break

    submission.verdict = verdict
    submission.runtime = round(max_runtime, 3)
    submission.memory = max_memory # Memory tracking omitted for simplicity
    db.session.commit()
    
    return jsonify({
        "submission_id": submission.id,
        "verdict": submission.verdict,
        "runtime": submission.runtime,
        "memory": submission.memory,
        "output": final_output
    })


def execute_local(language, code, input_data, time_limit):
    """Executes code using local compilers instead of Docker for immediate results."""
    config = {
        "python": {
            "file": "main.py",
            "cmd": ["python3", "main.py"]
        },
        "c": {
            "file": "main.c",
            "compile": ["gcc", "-O2", "main.c", "-o", "main"],
            "cmd": ["./main"]
        },
        "cpp": {
            "file": "main.cpp",
            "compile": ["g++", "-O2", "main.cpp", "-o", "main"],
            "cmd": ["./main"]
        },
        "java": {
            "filename_regex": r'public\s+class\s+(\w+)',
            "default_name": "Main",
            "file": "{name}.java",
            "compile": ["javac", "{name}.java"],
            "cmd": ["java", "{name}"]
        },
        "javascript": {
            "file": "main.js",
            "cmd": ["node", "main.js"]
        }
    }
    
    lang_cfg = config.get(language)
    if not lang_cfg:
        return {"status": "Runtime Error", "output": f"Unsupported language {language}", "runtime": 0}

    if "filename_regex" in lang_cfg:
        import re
        match = re.search(lang_cfg["filename_regex"], code)
        base_name = match.group(1) if match else lang_cfg["default_name"]
        
        lang_cfg["file"] = lang_cfg["file"].format(name=base_name)
        if "compile" in lang_cfg:
            lang_cfg["compile"] = [arg.format(name=base_name) for arg in lang_cfg["compile"]]
        lang_cfg["cmd"] = [arg.format(name=base_name) for arg in lang_cfg["cmd"]]

    with tempfile.TemporaryDirectory() as temp_dir:
        file_path = os.path.join(temp_dir, lang_cfg["file"])
        with open(file_path, "w") as f:
            f.write(code)
            
        # Compile step
        if "compile" in lang_cfg:
            try:
                subprocess.run(lang_cfg["compile"], cwd=temp_dir, capture_output=True, text=True, check=True, timeout=10)
            except subprocess.CalledProcessError as e:
                return {"status": "Compilation Error", "output": e.stderr, "runtime": 0}
            except subprocess.TimeoutExpired:
                return {"status": "Compilation Error", "output": "Compilation Timeout", "runtime": 0}
            except FileNotFoundError:
                return {"status": "Compilation Error", "output": f"Compiler not found: {lang_cfg['compile'][0]}", "runtime": 0}

        # Execution step
        start_time = time.time()
        try:
            process = subprocess.run(
                lang_cfg["cmd"],
                cwd=temp_dir,
                input=input_data,
                capture_output=True,
                text=True,
                timeout=time_limit + 1
            )
            runtime = time.time() - start_time
            
            if process.returncode != 0:
                return {"status": "Runtime Error", "output": process.stderr, "runtime": runtime}
                
            return {"status": "Success", "output": process.stdout, "runtime": runtime}
            
        except subprocess.TimeoutExpired:
            return {"status": "Time Limit Exceeded", "output": "", "runtime": time_limit}
        except FileNotFoundError:
            return {"status": "Runtime Error", "output": f"Execution engine not found: {lang_cfg['cmd'][0]}", "runtime": 0}




@coding_bp.route("/api/stats", methods=["GET"])
@login_required
def get_user_stats():
    # Gather stats for the current user
    submissions = CodingSubmission.query.filter_by(user_id=current_user.id).all()
    solved_problems = set(s.problem_id for s in submissions if s.verdict == "Accepted")
    total_problems = CodingProblem.query.filter_by(is_published=True).count()
    
    return jsonify({
        "total_solved": len(solved_problems),
        "total_problems": total_problems,
        "total_submissions": len(submissions),
        "acceptance_rate": (len(solved_problems) / len(submissions) * 100) if submissions else 0
    })
