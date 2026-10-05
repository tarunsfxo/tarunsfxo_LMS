from app import app, db
from sqlalchemy import text

def fix_schema():
    with app.app_context():
        try:
            db.session.execute(text("ALTER TABLE quiz_questions ADD COLUMN course_id INTEGER REFERENCES courses(id);"))
            print("Added course_id to quiz_questions.")
        except Exception as e:
            print("course_id on quiz_questions may already exist:", e)
            db.session.rollback()
            
        try:
            db.session.execute(text("ALTER TABLE quiz_questions ALTER COLUMN bite_id DROP NOT NULL;"))
            print("Dropped NOT NULL on quiz_questions.bite_id.")
        except Exception as e:
            print("Could not drop NOT NULL on quiz_questions.bite_id:", e)
            db.session.rollback()

        try:
            db.session.execute(text("ALTER TABLE quiz_attempts ADD COLUMN course_id INTEGER REFERENCES courses(id);"))
            print("Added course_id to quiz_attempts.")
        except Exception as e:
            print("course_id on quiz_attempts may already exist:", e)
            db.session.rollback()

        try:
            db.session.execute(text("ALTER TABLE quiz_attempts ALTER COLUMN bite_id DROP NOT NULL;"))
            print("Dropped NOT NULL on quiz_attempts.bite_id.")
        except Exception as e:
            print("Could not drop NOT NULL on quiz_attempts.bite_id:", e)
            db.session.rollback()

        db.session.commit()
        print("Schema update completed successfully.")

if __name__ == "__main__":
    fix_schema()
