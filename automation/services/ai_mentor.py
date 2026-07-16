"""
automation.services.ai_mentor — AI Mentor Service (Instant, In-Process)
========================================================================
The AI Mentor runs ENTIRELY inside Flask for instant responses.  n8n is
only notified in the background to log the interaction and update analytics.

Search order (local-first, cost-saving):
  1. Course content (Bite.content, Course.description) — ILIKE search
  2. Previous AI Mentor answers (cached in DB)
  3. Quiz explanations for related topics
  4. OpenAI (if API key configured) — only as last resort
  5. Fallback — "I couldn't find a specific answer" with related topics
"""

import json
import logging
import time
from datetime import datetime

from extensions import db

logger = logging.getLogger("automation.services.ai_mentor")


def ask_question(user, question: str) -> dict:
    """Process a student's question through the local-first search pipeline.

    Parameters
    ----------
    user : User
        The authenticated user asking the question.
    question : str
        The student's question text.

    Returns
    -------
    dict
        ``{"answer": str, "source": str, "response_time_ms": int}``
        where ``source`` is one of: course_notes, cached_answer, quiz_notes, openai, fallback
    """
    start = time.time()
    answer = None
    source = None

    # 1. Search course content
    answer, source = _search_course_content(question)

    # 2. Search cached AI Mentor answers
    if not answer:
        answer, source = _search_cached_answers(question)

    # 3. Search quiz explanations
    if not answer:
        answer, source = _search_quiz_explanations(question)

    # 4. Call OpenAI (if configured)
    if not answer:
        answer, source = _call_openai(user, question)

    # 5. Fallback
    if not answer:
        answer = _generate_fallback(question)
        source = "fallback"

    response_time_ms = int((time.time() - start) * 1000)

    # Save conversation to DB
    _save_conversation(user.id, question, answer, source, response_time_ms)

    # Fire background event for n8n (logging, analytics — non-blocking)
    try:
        from automation.trigger import fire
        fire(
            "ai_mentor_used",
            user_id=user.id,
            source=source,
            response_time_ms=response_time_ms,
        )
    except Exception:
        pass

    return {
        "answer": answer,
        "source": source,
        "response_time_ms": response_time_ms,
    }


def get_conversation_history(user_id: int, limit: int = 50) -> list:
    """Retrieve conversation history for a user."""
    from automation.models import AIMentorConversation

    convos = (
        AIMentorConversation.query
        .filter_by(user_id=user_id)
        .order_by(AIMentorConversation.created_at.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "id": c.id,
            "question": c.question,
            "answer": c.answer,
            "source": c.source,
            "response_time_ms": c.response_time_ms,
            "created_at": c.created_at.isoformat(),
        }
        for c in reversed(convos)
    ]


# ── Private search helpers ──────────────────────────────────────────


def _search_course_content(question: str):
    """Search Bite.content and Course.description for relevant answers."""
    from models import Bite, Course

    keywords = _extract_keywords(question)
    if not keywords:
        return None, None

    # Search bites
    for kw in keywords:
        bites = Bite.query.filter(
            Bite.content.ilike(f"%{kw}%")
        ).limit(3).all()

        if bites:
            # Extract the most relevant paragraph
            for bite in bites:
                paragraph = _extract_relevant_paragraph(bite.content, kw)
                if paragraph and len(paragraph) > 50:
                    answer = (
                        f"Based on the lesson **\"{bite.title}\"**:\n\n"
                        f"{paragraph}\n\n"
                        f"_You can review the full lesson for more details._"
                    )
                    return answer, "course_notes"

    # Search courses
    for kw in keywords:
        courses = Course.query.filter(
            Course.description.ilike(f"%{kw}%")
        ).limit(3).all()

        if courses:
            for course in courses:
                if course.description:
                    paragraph = _extract_relevant_paragraph(course.description, kw)
                    if paragraph and len(paragraph) > 50:
                        answer = (
                            f"From the course **\"{course.title}\"**:\n\n"
                            f"{paragraph}"
                        )
                        return answer, "course_notes"

    return None, None


def _search_cached_answers(question: str):
    """Search previous AI Mentor answers for similar questions."""
    from automation.models import AIMentorConversation

    keywords = _extract_keywords(question)
    if not keywords:
        return None, None

    for kw in keywords:
        cached = (
            AIMentorConversation.query
            .filter(AIMentorConversation.question.ilike(f"%{kw}%"))
            .filter(AIMentorConversation.source.in_(["openai", "course_notes"]))
            .order_by(AIMentorConversation.created_at.desc())
            .first()
        )
        if cached and len(cached.answer) > 30:
            return cached.answer, "cached_answer"

    return None, None


def _search_quiz_explanations(question: str):
    """Search quiz question explanations for relevant content."""
    from models import QuizQuestion

    keywords = _extract_keywords(question)
    if not keywords:
        return None, None

    for kw in keywords:
        questions = QuizQuestion.query.filter(
            QuizQuestion.explanation.ilike(f"%{kw}%")
        ).limit(3).all()

        relevant = [q for q in questions if q.explanation and len(q.explanation) > 20]
        if relevant:
            parts = []
            for q in relevant[:2]:
                parts.append(f"**Q:** {q.question}\n**A:** {q.explanation}")
            answer = "Based on quiz content:\n\n" + "\n\n---\n\n".join(parts)
            return answer, "quiz_notes"

    return None, None


def _call_openai(user, question: str):
    """Call OpenAI API as a last resort.  Returns None if no API key."""
    from flask import current_app

    api_key = current_app.config.get("OPENAI_API_KEY", "")
    if not api_key:
        return None, None

    model = current_app.config.get("OPENAI_MODEL", "gpt-4o-mini")

    try:
        import openai

        client = openai.OpenAI(api_key=api_key)

        # Build context from user's enrolled courses
        context = _build_user_context(user)

        start = time.time()
        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an AI learning mentor for Tarunsfxo LMS, "
                        "a coding education platform. Answer the student's question "
                        "clearly and concisely. Use examples when helpful. "
                        f"Student context: {context}"
                    ),
                },
                {"role": "user", "content": question},
            ],
            max_tokens=600,
            temperature=0.7,
        )

        latency_ms = int((time.time() - start) * 1000)

        # Update health metrics passively
        try:
            from automation.health import update_health
            update_health("openai", success=True, latency_ms=latency_ms)
        except Exception:
            pass

        answer = response.choices[0].message.content.strip()
        return answer, "openai"

    except Exception as exc:
        logger.warning("OpenAI call failed: %s", exc)
        try:
            from automation.health import update_health
            update_health("openai", success=False, error=str(exc))
        except Exception:
            pass
        return None, None


def _generate_fallback(question: str) -> str:
    """Generate a helpful fallback response when no answer is found."""
    from models import Bite, Course

    keywords = _extract_keywords(question)

    # Suggest related content
    suggestions = []
    for kw in keywords[:2]:
        bites = Bite.query.filter(Bite.title.ilike(f"%{kw}%")).limit(2).all()
        for b in bites:
            suggestions.append(f"📚 Lesson: **{b.title}**")

        courses = Course.query.filter(Course.title.ilike(f"%{kw}%")).limit(2).all()
        for c in courses:
            suggestions.append(f"🎓 Course: **{c.title}**")

    answer = (
        "I couldn't find a specific answer to your question in our course materials. "
        "Here are some things you can try:\n\n"
    )

    if suggestions:
        answer += "**Related content you might find helpful:**\n"
        for s in suggestions[:4]:
            answer += f"- {s}\n"
        answer += "\n"

    answer += (
        "- Try rephrasing your question with different keywords\n"
        "- Check the course lessons related to this topic\n"
        "- Review quiz explanations for similar concepts"
    )

    return answer


# ── Utility helpers ──────────────────────────────────────────────────


def _extract_keywords(text: str) -> list:
    """Extract meaningful keywords from a question (simple stopword removal)."""
    stopwords = {
        "a", "an", "the", "is", "are", "was", "were", "be", "been", "being",
        "have", "has", "had", "do", "does", "did", "will", "would", "could",
        "should", "may", "might", "shall", "can", "need", "dare", "ought",
        "to", "of", "in", "for", "on", "with", "at", "by", "from", "as",
        "into", "through", "during", "before", "after", "above", "below",
        "between", "out", "off", "over", "under", "again", "further", "then",
        "once", "here", "there", "when", "where", "why", "how", "all", "each",
        "every", "both", "few", "more", "most", "other", "some", "such", "no",
        "nor", "not", "only", "own", "same", "so", "than", "too", "very",
        "just", "but", "and", "or", "if", "what", "which", "who", "whom",
        "this", "that", "these", "those", "i", "me", "my", "myself", "we",
        "our", "ours", "you", "your", "he", "him", "his", "she", "her", "it",
        "its", "they", "them", "their", "about", "up", "it's", "i'm",
        "please", "explain", "tell", "help", "understand", "know", "learn",
    }

    words = text.lower().split()
    keywords = [w.strip("?.,!:;\"'()") for w in words if len(w) > 2]
    keywords = [w for w in keywords if w and w not in stopwords]

    return keywords[:5]  # limit to top 5 keywords


def _extract_relevant_paragraph(text: str, keyword: str) -> str:
    """Extract the paragraph containing the keyword from a longer text."""
    paragraphs = text.split("\n\n")
    if not paragraphs:
        paragraphs = text.split("\n")

    for para in paragraphs:
        if keyword.lower() in para.lower() and len(para.strip()) > 30:
            # Truncate very long paragraphs
            if len(para) > 500:
                return para[:500] + "..."
            return para.strip()

    return None


def _build_user_context(user) -> str:
    """Build a context string about the user for OpenAI."""
    from models import Progress, CourseProgress, Bite, Course

    completed_bites = Progress.query.filter_by(user_id=user.id, completed=True).count()
    completed_courses = CourseProgress.query.filter_by(user_id=user.id, completed=True).count()

    context = (
        f"Username: {user.username}, "
        f"XP: {user.xp}, Level: {user.level()}, "
        f"Completed lessons: {completed_bites}, "
        f"Completed courses: {completed_courses}"
    )
    return context


def _save_conversation(user_id: int, question: str, answer: str, source: str, response_time_ms: int):
    """Save the conversation to the database."""
    try:
        from automation.models import AIMentorConversation

        convo = AIMentorConversation(
            user_id=user_id,
            question=question,
            answer=answer,
            source=source,
            response_time_ms=response_time_ms,
        )
        db.session.add(convo)
        db.session.commit()
    except Exception:
        logger.exception("Failed to save AI Mentor conversation")
        db.session.rollback()
