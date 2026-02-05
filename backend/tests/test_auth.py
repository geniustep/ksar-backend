import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_start_otp(client: AsyncClient):
    response = await client.post(
        "/api/v1/auth/start",
        json={"phone": "+212612345678"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "تم إرسال رمز التحقق"
    assert data["expires_in"] == 300


@pytest.mark.asyncio
async def test_start_otp_invalid_phone(client: AsyncClient):
    response = await client.post(
        "/api/v1/auth/start",
        json={"phone": "123"},
    )
    assert response.status_code == 422
