from flask import Blueprint, jsonify, request, render_template
from flask_login import login_required, current_user
from models import CodingProblem, CodingSubmission, CodingTestCase, CodingTag, db
import requests
import json
import os
import sys
from automation.trigger import fire

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
    
    # --- Award XP for Accepted submission ---
    if verdict == "Accepted":
        # Check if the user has already solved this problem
        previous_accepted = CodingSubmission.query.filter(
            CodingSubmission.user_id == current_user.id,
            CodingSubmission.problem_id == problem.id,
            CodingSubmission.verdict == "Accepted",
            CodingSubmission.id != submission.id
        ).first()
        
        if not previous_accepted:
            # Determine base XP
            base_xp = 50
            if problem.difficulty.lower() == "medium":
                base_xp = 100
            elif problem.difficulty.lower() == "hard":
                base_xp = 200
                
            from gamification import award_xp
            award_xp(current_user, base_xp, f"coding_problem_{problem.difficulty.lower()}")
            
            # Check if this is the user's first accepted submission ever
            first_accepted_ever = CodingSubmission.query.filter(
                CodingSubmission.user_id == current_user.id,
                CodingSubmission.verdict == "Accepted",
                CodingSubmission.id != submission.id
            ).first()
            
            if not first_accepted_ever:
                award_xp(current_user, 30, "first_accepted_bonus")
                
    db.session.commit()
    
    fire(
        "coding_submitted",
        user_id=current_user.id,
        problem_id=problem.id,
        verdict=submission.verdict,
        runtime=submission.runtime,
        language=submission.language
    )
    
    return jsonify({
        "submission_id": submission.id,
        "verdict": submission.verdict,
        "runtime": submission.runtime,
        "memory": submission.memory,
        "output": final_output
    })



@coding_bp.route("/api/compiler-status", methods=["GET"])
@login_required
def compiler_status():
    """Admin diagnostic: show which compilers are found on this server.
    
    Visit /coding/api/compiler-status to see the full compiler environment.
    Useful for debugging 'compiler not found' errors on production.
    """
    import shutil, glob as _glob, sys as _sys
    from flask_login import current_user
    
    # Only admins can see full details
    if not getattr(current_user, "is_admin", False):
        return jsonify({"error": "Admin only"}), 403

    # Import _COMPILER_ENV from this same module
    import blueprints.coding as _this
    env_path = _this._COMPILER_ENV.get("PATH", os.environ.get("PATH", ""))
    
    tools = ["python3", "gcc", "g++", "javac", "java", "node", "npm", "ruby", "php", "bash", "go", "rustc", "swift"]
    found = {}
    for t in tools:
        found[t] = shutil.which(t, path=env_path) or "NOT FOUND"

    jvm_dirs = _glob.glob("/usr/lib/jvm/*/bin") + _glob.glob("/usr/local/lib/jvm/*/bin")

    return jsonify({
        "PATH_used": env_path,
        "compilers": found,
        "jvm_dirs_discovered": jvm_dirs,
        "JAVA_HOME": os.environ.get("JAVA_HOME", "not set"),
        "python_executable": _sys.executable,
    })



def _build_compiler_env():
    """Build a subprocess env with ALL compiler locations prepended to PATH.

    Uses glob-based JVM discovery so it finds javac regardless of the exact
    OpenJDK version/architecture string that apt installs (e.g. java-17-openjdk,
    java-17-openjdk-amd64, java-21-openjdk-arm64, etc.).

    Works on:
      - macOS (Homebrew at /opt/homebrew/bin, Xcode CLT at /usr/bin)
      - Debian/Ubuntu Docker / Render (python:3.11-slim + apt default-jdk)
      - Any Linux where JAVA_HOME is set by the OS
    """
    import glob as _glob

    env = os.environ.copy()

    # ── Static well-known dirs ────────────────────────────────────────────────
    static_dirs = [
        "/opt/homebrew/bin",           # macOS Homebrew (Apple Silicon)
        "/opt/homebrew/opt/openjdk/bin",
        "/usr/local/bin",              # macOS Homebrew (Intel) / Linux
        "/usr/bin",                    # System-wide on all platforms
        "/bin",
        "/usr/local/sbin",
        "/usr/sbin",
        "/sbin",
    ]

    # ── JAVA_HOME (set by Docker image, OS, or Render env vars) ─────────────
    java_home = env.get("JAVA_HOME", "")
    if java_home:
        jh_bin = os.path.join(java_home, "bin")
        static_dirs.insert(0, jh_bin)

    # ── Glob every installed JVM on Linux (covers ALL version/arch variants) ─
    # This catches: java-17-openjdk, java-17-openjdk-amd64, java-21-openjdk-arm64, etc.
    jvm_bin_dirs = []
    for pattern in [
        "/usr/lib/jvm/*/bin",
        "/usr/local/lib/jvm/*/bin",
    ]:
        jvm_bin_dirs.extend(_glob.glob(pattern))

    # Prefer default-java symlink if it exists (always points to current default)
    jvm_bin_dirs.sort(key=lambda p: (0 if "default" in p else 1, p))

    all_dirs = static_dirs + jvm_bin_dirs
    existing = [d for d in all_dirs if os.path.isdir(d)]

    # Deduplicate while preserving order
    seen = set()
    unique_dirs = []
    for d in existing:
        if d not in seen:
            seen.add(d)
            unique_dirs.append(d)

    original = env.get("PATH", "")
    env["PATH"] = ":".join(unique_dirs) + (":" + original if original else "")
    return env


# Built once at module import — shared across all requests
_COMPILER_ENV = _build_compiler_env()


def execute_local(language, code, input_data, time_limit):
    """Executes code locally using system-installed compilers/interpreters.

    Compiler binaries are discovered dynamically via _COMPILER_ENV so this works
    on macOS (Homebrew), Linux Debian/Ubuntu Docker (Render), and future platforms.
    Returns a clear error message if a required compiler is not installed.
    """
    import copy
    import re
    import shutil

    # Resolve binaries dynamically — avoids hardcoding paths that differ per OS
    _path = _COMPILER_ENV["PATH"]
    javac_bin  = shutil.which("javac",   path=_path) or "javac"
    java_bin   = shutil.which("java",    path=_path) or "java"
    python_bin = sys.executable or shutil.which("python3", path=_path) or "python3"

    # Use deepcopy so format() calls below never mutate the shared template dict
    config = {
        "python": {
            "file": "main.py",
            "cmd": [python_bin, "main.py"]
        },
        "c": {
            "file": "main.c",
            "compile": ["gcc", "-O2", "-x", "c", "main.c", "-o", "main", "-lm"],
            "cmd": ["./main"]
        },
        "cpp": {
            "file": "main.cpp",
            "compile": ["g++", "-O2", "-std=c++17", "main.cpp", "-o", "main"],
            "cmd": ["./main"]
        },
        "java": {
            "filename_regex": r'public\s+class\s+(\w+)',
            "default_name": "Main",
            "file": "{name}.java",
            "compile": [javac_bin, "{name}.java"],
            "cmd": [java_bin, "-cp", ".", "{name}"]
        },
        "javascript": {
            "file": "main.js",
            "cmd": ["node", "main.js"]
        },
        "typescript": {
            "file": "main.ts",
            "compile": ["npx", "--yes", "ts-node", "main.ts"],
            "cmd": []
        },
        "ruby": {
            "file": "main.rb",
            "cmd": ["ruby", "main.rb"]
        },
        "go": {
            "file": "main.go",
            "compile": ["go", "build", "-o", "main", "main.go"],
            "cmd": ["./main"]
        },
        "rust": {
            "file": "main.rs",
            "compile": ["rustc", "-o", "main", "main.rs"],
            "cmd": ["./main"]
        },
        "kotlin": {
            "file": "main.kt",
            "compile": ["kotlinc", "main.kt", "-include-runtime", "-d", "main.jar"],
            "cmd": [java_bin, "-jar", "main.jar"]
        },
        "swift": {
            "file": "main.swift",
            "compile": ["swiftc", "main.swift", "-o", "main"],
            "cmd": ["./main"]
        },
        "php": {
            "file": "main.php",
            "cmd": ["php", "main.php"]
        },
        "bash": {
            "file": "main.sh",
            "cmd": ["bash", "main.sh"]
        },
        "r": {
            "file": "main.R",
            "cmd": ["Rscript", "main.R"]
        },
        "csharp": {
            "file": "main.cs",
            "compile": ["mcs", "main.cs", "-out:main.exe"],
            "cmd": ["mono", "main.exe"]
        },
    }

    lang_cfg_template = config.get(language)
    if not lang_cfg_template:
        return {"status": "Runtime Error", "output": f"Unsupported language: '{language}'", "runtime": 0}

    # Deep-copy so repeated calls don't corrupt the template via .format() mutation
    lang_cfg = copy.deepcopy(lang_cfg_template)

    # Determine base name (Java needs public class name; others use 'Main')
    base_name = lang_cfg.get("default_name", "Main")
    if "filename_regex" in lang_cfg:
        match = re.search(lang_cfg["filename_regex"], code)
        if match:
            base_name = match.group(1)

    filename = lang_cfg["file"].format(name=base_name)

    # Use the pre-built enriched environment (dynamically discovered at startup)
    env = _COMPILER_ENV.copy()

    with tempfile.TemporaryDirectory() as temp_dir:
        file_path = os.path.join(temp_dir, filename)
        with open(file_path, "w") as f:
            f.write(code)

        # Expand {name} placeholders in compile / cmd lists
        compile_cmd = [arg.format(name=base_name) for arg in lang_cfg.get("compile", [])]
        run_cmd     = [arg.format(name=base_name) for arg in lang_cfg.get("cmd", [])]

        # ── Compile step ──────────────────────────────────────────────────────
        if compile_cmd:
            try:
                result = subprocess.run(
                    compile_cmd,
                    cwd=temp_dir, env=env,
                    capture_output=True, text=True,
                    check=True, timeout=15
                )
            except subprocess.CalledProcessError as e:
                return {"status": "Compilation Error", "output": e.stderr or e.stdout, "runtime": 0}
            except subprocess.TimeoutExpired:
                return {"status": "Compilation Error", "output": "Compilation timed out (>15 s).", "runtime": 0}
            except FileNotFoundError as e:
                tool = compile_cmd[0]
                return {
                    "status": "Runtime Error",
                    "output": (
                        f"Compiler not found: '{tool}'.\n"
                        f"Please install it (e.g. `brew install {tool}`) and restart the server."
                    ),
                    "runtime": 0
                }

        # ── Execution step ────────────────────────────────────────────────────
        start_time = time.time()
        try:
            process = subprocess.run(
                run_cmd,
                cwd=temp_dir, env=env,
                input=input_data or "",
                capture_output=True, text=True,
                timeout=time_limit + 2
            )
            runtime = time.time() - start_time

            if process.returncode != 0:
                err_output = (process.stderr or process.stdout or "Non-zero exit code").strip()
                return {"status": "Runtime Error", "output": err_output, "runtime": runtime}

            return {"status": "Success", "output": process.stdout, "runtime": runtime}

        except subprocess.TimeoutExpired:
            return {"status": "Time Limit Exceeded", "output": "", "runtime": time_limit}
        except FileNotFoundError:
            tool = run_cmd[0] if run_cmd else language
            return {
                "status": "Runtime Error",
                "output": (
                    f"Runtime not found: '{tool}'.\n"
                    f"Please install it (e.g. `brew install {tool}`) and restart the server."
                ),
                "runtime": 0
            }
        except Exception as e:
            return {"status": "Runtime Error", "output": f"Unexpected execution error: {str(e)}", "runtime": 0}


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


@coding_bp.route("/api/practice-generate", methods=["POST"])
@login_required
def practice_generate():
    """Generates a dynamic coding problem matching user's requested level."""
    data = request.get_json(silent=True) or {}
    difficulty = data.get("difficulty", "Easy").capitalize()
    if difficulty not in ["Easy", "Medium", "Hard"]:
        difficulty = "Easy"

    # Search local database for existing problems of this difficulty to recommend
    from models import CodingProblem
    problems = CodingProblem.query.filter_by(difficulty=difficulty, is_published=True).all()
    
    # Try calling OpenAI to generate a dynamic custom practice challenge if configured
    from flask import current_app
    import json
    api_key = current_app.config.get("OPENAI_API_KEY", "")
    if api_key:
        try:
            import openai
            client = openai.OpenAI(api_key=api_key)
            prompt = (
                f"Generate a unique coding challenge with difficulty '{difficulty}'. "
                "Output JSON with fields: 'title', 'description' (in markdown format), "
                "'starter_code' (python template), and 'test_cases' (an array of objects containing 'input' and 'expected_output')."
            )
            response = client.chat.completions.create(
                model=current_app.config.get("OPENAI_MODEL", "gpt-4o-mini"),
                messages=[
                    {"role": "system", "content": "You are a senior coding challenge compiler. Always output pure valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"}
            )
            challenge = json.loads(response.choices[0].message.content.strip())
            return jsonify({
                "success": True,
                "title": challenge.get("title", f"Dynamic {difficulty} Challenge"),
                "description": challenge.get("description", "Solve the challenge using standard streams."),
                "starter_code": challenge.get("starter_code", "def solve():\n    pass"),
                "test_cases": challenge.get("test_cases", [])
            })
        except Exception as e:
            # Safe log fail fallback
            import logging
            logging.getLogger("blueprints.coding").warning("Dynamic practice generation failed: %s", e)
            
    # Fallback to choosing a random published problem from the DB
    import random
    if problems:
        problem = random.choice(problems)
        # Parse test cases
        test_cases = []
        if problem.test_cases:
            try:
                test_cases = json.loads(problem.test_cases)
            except Exception:
                pass
        return jsonify({
            "success": True,
            "title": problem.title,
            "description": problem.description,
            "starter_code": "def solve():\n    pass",
            "test_cases": test_cases
        })

    return jsonify({"error": "No practice problems available of this difficulty level."}), 404
