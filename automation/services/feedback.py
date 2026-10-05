"""
automation.services.feedback — Feedback Analysis Service
=========================================================
No duplicate feedback table.  Creates only FeedbackAnalysis records
linked to course_id.  Sentiment analysis uses simple keyword-based
logic if OpenAI is unavailable.
"""

import json
import logging
from datetime import datetime

from extensions import db

logger = logging.getLogger("automation.services.feedback")

# Simple sentiment keyword lists
_POSITIVE_WORDS = {
    "great", "excellent", "amazing", "awesome", "love", "perfect", "helpful",
    "clear", "fantastic", "wonderful", "best", "good", "enjoy", "learned",
    "useful", "recommend", "easy", "fun", "informative", "well",
}
_NEGATIVE_WORDS = {
    "bad", "terrible", "awful", "confusing", "boring", "difficult", "hard",
    "poor", "waste", "unclear", "slow", "broken", "error", "frustrating",
    "disappointed", "wrong", "missing", "incomplete", "useless", "hate",
}


def submit_feedback(user, course_id: int, text: str, rating: int = None) -> dict:
    """Submit and analyze feedback.

    Returns
    -------
    dict
        ``{"id": int, "sentiment": str, "category": str}``
    """
    from automation.models import FeedbackAnalysis

    # Analyze sentiment
    sentiment = _analyze_sentiment(text, rating)
    category = _classify_category(text)

    # Try OpenAI for better analysis if available
    ai_result = _openai_analyze(text)
    if ai_result:
        sentiment = ai_result.get("sentiment", sentiment)
        category = ai_result.get("category", category)

    # Save to FeedbackAnalysis
    analysis = FeedbackAnalysis(
        user_id=user.id,
        course_id=course_id if course_id else None,
        original_text=text,
        rating=rating,
        sentiment=sentiment,
        category=category,
    )
    db.session.add(analysis)
    db.session.commit()

    # Fire background event for n8n
    try:
        from automation.trigger import fire
        fire(
            "feedback_submitted",
            user_id=user.id,
            course_id=course_id,
            sentiment=sentiment,
            category=category,
            rating=rating,
        )
    except Exception:
        pass

    return {
        "id": analysis.id,
        "sentiment": sentiment,
        "category": category,
    }


def get_feedback_stats(course_id: int = None) -> dict:
    """Get aggregated feedback statistics for admin dashboard."""
    from automation.models import FeedbackAnalysis

    query = FeedbackAnalysis.query
    if course_id:
        query = query.filter_by(course_id=course_id)

    total = query.count()
    if total == 0:
        return {"total": 0, "positive": 0, "neutral": 0, "negative": 0, "avg_rating": 0}

    positive = query.filter_by(sentiment="positive").count()
    neutral = query.filter_by(sentiment="neutral").count()
    negative = query.filter_by(sentiment="negative").count()

    from sqlalchemy import func
    avg_rating = db.session.query(func.avg(FeedbackAnalysis.rating)).filter(
        FeedbackAnalysis.rating.isnot(None)
    ).scalar() or 0

    return {
        "total": total,
        "positive": positive,
        "neutral": neutral,
        "negative": negative,
        "avg_rating": round(float(avg_rating), 1),
        "positive_pct": round(positive / total * 100) if total else 0,
        "negative_pct": round(negative / total * 100) if total else 0,
    }


# ── Private helpers ─────────────────────────────────────────────


def _analyze_sentiment(text: str, rating: int = None) -> str:
    """Simple keyword-based sentiment analysis."""
    words = set(text.lower().split())

    pos_count = len(words & _POSITIVE_WORDS)
    neg_count = len(words & _NEGATIVE_WORDS)

    # Factor in star rating if provided
    if rating:
        if rating >= 4:
            pos_count += 2
        elif rating <= 2:
            neg_count += 2

    if pos_count > neg_count:
        return "positive"
    elif neg_count > pos_count:
        return "negative"
    return "neutral"


def _classify_category(text: str) -> str:
    """Simple keyword-based category classification."""
    lower = text.lower()

    if any(w in lower for w in ["instructor", "teacher", "tutor", "lecturer"]):
        return "instructor"
    if any(w in lower for w in ["content", "lesson", "material", "topic", "course"]):
        return "content"
    if any(w in lower for w in ["ui", "interface", "design", "layout", "bug", "error", "platform"]):
        return "platform"

    return "general"


def _openai_analyze(text: str) -> dict:
    """Use OpenAI for sentiment analysis if API key is available."""
    try:
        from flask import current_app

        api_key = current_app.config.get("OPENAI_API_KEY", "")
        if not api_key:
            return None

        import openai

        client = openai.OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model=current_app.config.get("OPENAI_MODEL", "gpt-4o-mini"),
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Analyze this LMS feedback. Return JSON only: "
                        '{"sentiment": "positive|neutral|negative", '
                        '"category": "content|instructor|platform|general"}'
                    ),
                },
                {"role": "user", "content": text},
            ],
            max_tokens=50,
            temperature=0,
        )

        result_text = response.choices[0].message.content.strip()
        return json.loads(result_text)

    except Exception:
        return None
