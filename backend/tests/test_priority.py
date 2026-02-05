from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock

from app.core.constants import RequestCategory
from app.services.priority_service import calculate_priority


def _make_request(category: RequestCategory, created_at=None):
    req = MagicMock()
    req.category = category
    req.created_at = created_at or datetime.now(timezone.utc)
    return req


def _make_profile(family_size=1, special_cases=None):
    profile = MagicMock()
    profile.family_size = family_size
    profile.special_cases = special_cases or []
    return profile


def test_base_score():
    req = _make_request(RequestCategory.OTHER)
    profile = _make_profile()
    score = calculate_priority(req, profile)
    assert score == 50  # base score + 0 for OTHER


def test_medicine_high_priority():
    req = _make_request(RequestCategory.MEDICINE)
    profile = _make_profile()
    score = calculate_priority(req, profile)
    assert score == 75  # 50 + 25


def test_special_cases_increase_score():
    req = _make_request(RequestCategory.FOOD)
    profile = _make_profile(special_cases=["pregnant", "children"])
    score = calculate_priority(req, profile)
    # 50 (base) + 15 (food) + 10 (pregnant) + 5 (children) = 80
    assert score == 80


def test_large_family_bonus():
    req = _make_request(RequestCategory.FOOD)
    profile = _make_profile(family_size=7)
    score = calculate_priority(req, profile)
    # 50 + 15 + 10 = 75
    assert score == 75


def test_waiting_time_bonus():
    req = _make_request(
        RequestCategory.OTHER,
        created_at=datetime.now(timezone.utc) - timedelta(days=3),
    )
    profile = _make_profile()
    score = calculate_priority(req, profile)
    # 50 + 0 + 6 (3 days * 2) = 56
    assert score == 56


def test_max_score_cap():
    req = _make_request(
        RequestCategory.MEDICINE,
        created_at=datetime.now(timezone.utc) - timedelta(days=30),
    )
    profile = _make_profile(
        family_size=8,
        special_cases=["pregnant", "disabled", "chronic_illness", "elderly", "children"],
    )
    score = calculate_priority(req, profile)
    assert score == 100  # Capped at 100
