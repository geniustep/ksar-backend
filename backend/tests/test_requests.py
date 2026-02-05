import pytest
from httpx import AsyncClient

from app.models.user import User
from tests.conftest import get_auth_headers


@pytest.mark.asyncio
async def test_create_request(client: AsyncClient, resident_user: User):
    headers = get_auth_headers(resident_user)
    response = await client.post(
        "/api/v1/requests",
        headers=headers,
        json={
            "category": "food",
            "description": "نحتاج مواد غذائية لأسرة من 4 أفراد",
            "quantity": 4,
            "location_text": "حي السلام، قرب المسجد الكبير",
            "region_code": "tanger",
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["category"] == "food"
    assert data["status"] == "new"
    assert data["priority_score"] > 0


@pytest.mark.asyncio
async def test_get_my_requests(client: AsyncClient, resident_user: User):
    headers = get_auth_headers(resident_user)

    # Create a request first
    await client.post(
        "/api/v1/requests",
        headers=headers,
        json={
            "category": "medicine",
            "location_text": "حي النور، بجانب الصيدلية",
            "quantity": 1,
        },
    )

    response = await client.get("/api/v1/requests/mine", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    assert len(data["items"]) >= 1


@pytest.mark.asyncio
async def test_cancel_request(client: AsyncClient, resident_user: User):
    headers = get_auth_headers(resident_user)

    # Create request
    create_resp = await client.post(
        "/api/v1/requests",
        headers=headers,
        json={
            "category": "water",
            "location_text": "حي الأمل، شارع الماء",
            "quantity": 2,
        },
    )
    request_id = create_resp.json()["id"]

    # Cancel it
    response = await client.post(
        f"/api/v1/requests/{request_id}/cancel",
        headers=headers,
    )
    assert response.status_code == 200
    assert response.json()["status"] == "cancelled"


@pytest.mark.asyncio
async def test_org_cannot_create_request(client: AsyncClient, org_user: User):
    headers = get_auth_headers(org_user)
    response = await client.post(
        "/api/v1/requests",
        headers=headers,
        json={
            "category": "food",
            "location_text": "مكان ما",
            "quantity": 1,
        },
    )
    assert response.status_code == 403
