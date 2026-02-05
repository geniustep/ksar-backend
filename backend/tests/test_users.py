import pytest
from httpx import AsyncClient

from app.models.user import User
from tests.conftest import get_auth_headers


@pytest.mark.asyncio
async def test_get_me(client: AsyncClient, resident_user: User):
    headers = get_auth_headers(resident_user)
    response = await client.get("/api/v1/me", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert data["phone"] == "+212600000001"
    assert data["role"] == "resident"
    assert data["full_name"] == "ساكن تجريبي"


@pytest.mark.asyncio
async def test_update_me(client: AsyncClient, resident_user: User):
    headers = get_auth_headers(resident_user)
    response = await client.patch(
        "/api/v1/me",
        headers=headers,
        json={"full_name": "اسم جديد", "language": "fr"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["full_name"] == "اسم جديد"
    assert data["language"] == "fr"


@pytest.mark.asyncio
async def test_update_profile(client: AsyncClient, resident_user: User):
    headers = get_auth_headers(resident_user)
    response = await client.patch(
        "/api/v1/me/profile",
        headers=headers,
        json={
            "family_size": 6,
            "special_cases": ["children", "elderly"],
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["family_size"] == 6
    assert "elderly" in data["special_cases"]


@pytest.mark.asyncio
async def test_unauthorized_access(client: AsyncClient):
    response = await client.get("/api/v1/me")
    assert response.status_code == 403
