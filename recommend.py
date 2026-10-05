"""
Lightweight rule-based 'AI' recommendation engine for tarunsfxo LMS.
Uses weighted scoring of category affinity, difficulty progression,
recency, and popularity to recommend next bites. No external ML
dependency required, keeps the project self-contained and runnable.
"""
from collections import Counter
from sqlalchemy import func
from extensions import db
from models import Bite, Progress, Category, QuizAttempt

DIFFICULTY_ORDER = {"beginner": 1, "intermediate": 2, "advanced": 3}


def get_user_category_affinity(user):
    """Return Counter of category_id -> weighted interest score."""
    affinity = Counter()
    completed = (
        Progress.query.filter_by(user_id=user.id, completed=True)
        .join(Bite, Progress.bite_id == Bite.id)
        .with_entities(Bite.category_id)
        .all()
    )
    for (cat_id,) in completed:
        if cat_id:
            affinity[cat_id] += 2

    attempts = (
        QuizAttempt.query.filter_by(user_id=user.id)
        .join(Bite, QuizAttempt.bite_id == Bite.id)
        .with_entities(Bite.category_id, QuizAttempt.score, QuizAttempt.total_questions)
        .all()
    )
    for cat_id, score, total in attempts:
        if cat_id and total:
            ratio = score / total
            affinity[cat_id] += ratio * 1.5
    return affinity


def estimate_user_level(user, completed_ids=None):
    if completed_ids is None:
        completed_ids = user.completed_bite_ids()
    if not completed_ids:
        return "beginner"
    bites = Bite.query.filter(Bite.id.in_(completed_ids)).all()
    avg = sum(DIFFICULTY_ORDER.get(b.difficulty, 1) for b in bites) / len(bites)
    if avg < 1.5:
        return "beginner"
    elif avg < 2.5:
        return "intermediate"
    return "advanced"


def recommend_bites(user, limit=6, completed_ids=None):
    """
    Generate personalized bite recommendations using:
    1. Category affinity from completed bites + quiz performance
    2. Difficulty matched to estimated skill level (slightly above)
    3. Popularity fallback (most completed bites) for cold-start users
    4. Excludes already completed bites

    `completed_ids` may be passed in by the caller to avoid re-querying
    progress rows that were already fetched earlier in the same request
    (e.g. the dashboard view already loads this for the progress bar).
    """
    if completed_ids is None:
        completed_ids = user.completed_bite_ids()
    completed_ids = set(completed_ids)

    affinity = get_user_category_affinity(user)
    level = estimate_user_level(user, completed_ids=completed_ids)

    target_difficulties = {
        "beginner": ["beginner", "intermediate"],
        "intermediate": ["intermediate", "advanced", "beginner"],
        "advanced": ["advanced", "intermediate"],
    }[level]

    candidates = Bite.query.filter(~Bite.id.in_(completed_ids) if completed_ids else True).all()

    # Avoid an N+1 query: when there's no affinity signal yet (cold start),
    # popularity counts are needed for every candidate. Fetch them all in a
    # single grouped query instead of querying per-bite inside the loop.
    popularity_by_bite = {}
    if not affinity and candidates:
        rows = (
            db.session.query(Progress.bite_id, func.count(Progress.id))
            .filter(Progress.completed.is_(True))
            .group_by(Progress.bite_id)
            .all()
        )
        popularity_by_bite = dict(rows)

    scored = []
    for bite in candidates:
        score = 0.0
        score += affinity.get(bite.category_id, 0) * 3
        if bite.difficulty in target_difficulties:
            score += (len(target_difficulties) - target_difficulties.index(bite.difficulty)) * 2
        score += max(0, 5 - bite.order_index) * 0.1
        if not affinity:
            score += popularity_by_bite.get(bite.id, 0) * 0.5
        scored.append((score, bite))

    scored.sort(key=lambda x: x[0], reverse=True)
    results = [b for _, b in scored[:limit]]

    if len(results) < limit:
        exclude_ids = completed_ids.union({b.id for b in results})
        extra = (
            Bite.query.filter(~Bite.id.in_(exclude_ids))
            .order_by(Bite.order_index.asc())
            .limit(limit - len(results))
            .all()
        )
        results.extend(extra)

    return results[:limit]


def recommend_category_for_certificate(user):
    """Suggest which category the user is closest to mastering."""
    affinity = get_user_category_affinity(user)
    if not affinity:
        return None
    best_cat_id = affinity.most_common(1)[0][0]
    return Category.query.get(best_cat_id)
