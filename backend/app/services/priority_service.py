from datetime import datetime, timezone

from app.core.constants import CATEGORY_WEIGHTS, SPECIAL_CASE_WEIGHTS
from app.models.request import Request
from app.models.user import ResidentProfile


def calculate_priority(request: Request, profile: ResidentProfile) -> int:
    """Calculate priority score (0-100) for a request."""
    score = 50  # Base score

    # Category weight
    score += CATEGORY_WEIGHTS.get(request.category, 0)

    # Special cases from resident profile
    if profile and profile.special_cases:
        for case in profile.special_cases:
            score += SPECIAL_CASE_WEIGHTS.get(case, 0)

    # Family size
    if profile:
        if profile.family_size > 5:
            score += 10
        elif profile.family_size > 3:
            score += 5

    # Waiting time bonus (2 points per 24h, max 20)
    if request.created_at:
        now = datetime.now(timezone.utc)
        created = request.created_at if request.created_at.tzinfo else request.created_at.replace(tzinfo=timezone.utc)
        hours_waiting = (now - created).total_seconds() / 3600
        score += min(int(hours_waiting / 24) * 2, 20)

    return min(score, 100)
