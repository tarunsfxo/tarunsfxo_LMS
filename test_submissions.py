from app import create_app
from extensions import db
from models import CodingSubmission

app = create_app()

with app.app_context():
    subs = CodingSubmission.query.order_by(CodingSubmission.submitted_at.desc()).limit(5).all()
    for s in subs:
        print(f"ID: {s.id} | User: {s.user_id} | Prob: {s.problem_id} | Lang: {s.language} | Verdict: {s.verdict}")
        print("CODE:")
        print(s.code)
        print("-" * 40)
