"""
automation.services.career — Career & Resume Service
======================================================
Analyzes completed courses, quiz scores, and coding submissions to
generate career recommendations and ATS-friendly resume content.
"""

import json
import logging
from datetime import datetime

from extensions import db

logger = logging.getLogger("automation.services.career")

# Skill-to-role mapping
SKILL_ROLES = {
    "python": ["Python Developer", "Backend Engineer", "Data Analyst", "ML Engineer"],
    "javascript": ["Frontend Developer", "Full Stack Developer", "React Developer"],
    "html": ["Frontend Developer", "Web Developer"],
    "css": ["Frontend Developer", "UI Developer"],
    "sql": ["Database Administrator", "Data Analyst", "Backend Engineer"],
    "java": ["Java Developer", "Android Developer", "Backend Engineer"],
    "c": ["Systems Programmer", "Embedded Engineer"],
    "cpp": ["Systems Programmer", "Game Developer", "Embedded Engineer"],
    "react": ["React Developer", "Frontend Engineer"],
    "node": ["Backend Developer", "Full Stack Developer"],
    "api": ["Backend Engineer", "API Developer"],
    "database": ["Database Administrator", "Backend Engineer"],
    "algorithms": ["Software Engineer", "ML Engineer"],
    "data structures": ["Software Engineer", "Backend Engineer"],
    "machine learning": ["ML Engineer", "Data Scientist"],
    "web development": ["Full Stack Developer", "Web Developer"],
}


def generate_recommendations(user) -> dict:
    """Generate career recommendations based on user's completed content."""
    from models import Progress, CourseProgress, Bite, Course, Category, CodingSubmission, QuizAttempt

    # 1. Extract skills from completed content
    skills = set()

    # From completed bites
    completed_bites = (
        db.session.query(Bite)
        .join(Progress, Progress.bite_id == Bite.id)
        .filter(Progress.user_id == user.id, Progress.completed == True)
        .all()
    )
    for bite in completed_bites:
        if bite.category:
            skills.add(bite.category.name.lower())
        _extract_skills_from_text(bite.title, skills)

    # From completed courses
    completed_courses = (
        db.session.query(Course)
        .join(CourseProgress, CourseProgress.course_id == Course.id)
        .filter(CourseProgress.user_id == user.id, CourseProgress.completed == True)
        .all()
    )
    for course in completed_courses:
        if course.category:
            skills.add(course.category.name.lower())
        _extract_skills_from_text(course.title, skills)

    # From coding submissions
    coding_solved = CodingSubmission.query.filter_by(
        user_id=user.id, verdict="Accepted"
    ).count()
    if coding_solved > 0:
        skills.add("algorithms")
        skills.add("problem solving")

    # 2. Map skills to roles
    recommended_roles = set()
    for skill in skills:
        for key, roles in SKILL_ROLES.items():
            if key in skill or skill in key:
                recommended_roles.update(roles)

    # 3. Generate project suggestions
    projects = _suggest_projects(skills)

    # 4. Generate interview questions
    interview_questions = _suggest_interview_questions(skills)

    # 5. Certification recommendations
    certifications = _suggest_certifications(skills)

    # 6. Build results
    result = {
        "skills": sorted(skills),
        "recommended_roles": sorted(recommended_roles)[:8],
        "projects": projects[:5],
        "interview_questions": interview_questions[:10],
        "certifications": certifications[:5],
        "stats": {
            "completed_lessons": len(completed_bites),
            "completed_courses": len(completed_courses),
            "coding_solved": coding_solved,
            "xp": user.xp,
            "level": user.level(),
        },
    }

    # Save to database
    from automation.models import CareerRecommendation

    rec = CareerRecommendation(
        user_id=user.id,
        recommendations_json=json.dumps(result, default=str),
        skills_json=json.dumps(sorted(skills)),
    )
    db.session.add(rec)
    db.session.commit()

    return result


def get_latest_recommendation(user_id: int) -> dict:
    """Get the most recent career recommendation for a user."""
    from automation.models import CareerRecommendation

    rec = (
        CareerRecommendation.query
        .filter_by(user_id=user_id)
        .order_by(CareerRecommendation.generated_at.desc())
        .first()
    )
    if not rec:
        return None

    result = json.loads(rec.recommendations_json) if rec.recommendations_json else {}
    result["generated_at"] = rec.generated_at.isoformat() if rec.generated_at else None
    return result


# ── Private helpers ─────────────────────────────────────────────


def _extract_skills_from_text(text: str, skills: set):
    """Extract skill keywords from a title/description."""
    lower = text.lower()
    known_skills = [
        "python", "javascript", "html", "css", "sql", "java", "c++", "react",
        "node", "api", "database", "algorithms", "data structures", "flask",
        "django", "machine learning", "web development", "git",
    ]
    for skill in known_skills:
        if skill in lower:
            skills.add(skill)


def _suggest_projects(skills: set) -> list:
    """Suggest portfolio projects based on skills."""
    projects = []

    if "python" in skills:
        projects.append({
            "title": "REST API with Flask",
            "description": "Build a full REST API with authentication, CRUD, and database integration.",
            "skills_used": ["Python", "Flask", "SQL"],
        })
    if "javascript" in skills or "react" in skills:
        projects.append({
            "title": "Interactive Dashboard",
            "description": "Create a data visualization dashboard with React and Chart.js.",
            "skills_used": ["JavaScript", "React", "CSS"],
        })
    if "sql" in skills or "database" in skills:
        projects.append({
            "title": "Database Design Project",
            "description": "Design and implement a normalized database schema for an e-commerce platform.",
            "skills_used": ["SQL", "Database Design"],
        })
    if "algorithms" in skills:
        projects.append({
            "title": "Algorithm Visualizer",
            "description": "Build an interactive tool that visualizes sorting and pathfinding algorithms.",
            "skills_used": ["JavaScript", "Algorithms", "CSS"],
        })
    if "web development" in skills or "html" in skills:
        projects.append({
            "title": "Portfolio Website",
            "description": "Design and deploy a personal portfolio website showcasing your projects.",
            "skills_used": ["HTML", "CSS", "JavaScript"],
        })

    # Always suggest a capstone
    projects.append({
        "title": "Full-Stack Capstone Project",
        "description": "Build a complete web application combining all your learned skills.",
        "skills_used": sorted(list(skills))[:5],
    })

    return projects


def _suggest_interview_questions(skills: set) -> list:
    """Generate relevant interview questions."""
    questions = []

    if "python" in skills:
        questions.extend([
            "What are Python decorators and how do you use them?",
            "Explain the difference between a list and a tuple in Python.",
            "How does garbage collection work in Python?",
        ])
    if "javascript" in skills:
        questions.extend([
            "Explain closures in JavaScript.",
            "What is the event loop and how does it work?",
            "What's the difference between var, let, and const?",
        ])
    if "sql" in skills or "database" in skills:
        questions.extend([
            "What is database normalization? Explain 1NF, 2NF, and 3NF.",
            "What's the difference between INNER JOIN and LEFT JOIN?",
        ])
    if "algorithms" in skills:
        questions.extend([
            "Explain Big O notation and give examples.",
            "What are the differences between BFS and DFS?",
        ])

    # General questions
    questions.extend([
        "Tell me about a challenging project you worked on.",
        "How do you approach debugging a complex issue?",
    ])

    return questions


def _suggest_certifications(skills: set) -> list:
    """Suggest relevant certifications."""
    certs = []

    if "python" in skills:
        certs.append("PCEP – Certified Entry-Level Python Programmer")
    if "javascript" in skills or "web development" in skills:
        certs.append("Meta Front-End Developer Professional Certificate")
    if "sql" in skills or "database" in skills:
        certs.append("Oracle Database SQL Certified Associate")
    if "machine learning" in skills:
        certs.append("Google Machine Learning Engineer Certificate")

    certs.append("AWS Certified Cloud Practitioner")

    return certs
