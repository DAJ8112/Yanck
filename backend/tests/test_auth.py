from __future__ import annotations

import pytest


@pytest.mark.asyncio
async def test_register_login_and_me_flow(async_client) -> None:
    register_payload = {
        "email": "alice@example.com",
        "password": "password123",
        "full_name": "Alice",
    }
    response = await async_client.post("/api/auth/register", json=register_payload)
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == register_payload["email"]
    assert data["full_name"] == register_payload["full_name"]
    assert data["is_active"] is True

    # Duplicate registration should fail
    duplicate = await async_client.post("/api/auth/register", json=register_payload)
    assert duplicate.status_code == 400

    # Login with correct credentials
    login_payload = {
        "email": register_payload["email"],
        "password": register_payload["password"],
    }
    login = await async_client.post("/api/auth/login", json=login_payload)
    assert login.status_code == 200
    tokens = login.json()
    assert "access_token" in tokens
    assert "refresh_token" in tokens

    # Use access token to fetch current user
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}
    me = await async_client.get("/api/auth/me", headers=headers)
    assert me.status_code == 200
    me_data = me.json()
    assert me_data["email"] == register_payload["email"]

    # Refresh tokens should issue a new access token
    refresh = await async_client.post(
        "/api/auth/refresh", json={"refresh_token": tokens["refresh_token"]}
    )
    assert refresh.status_code == 200
    refreshed_tokens = refresh.json()
    assert refreshed_tokens["access_token"] != tokens["access_token"]







