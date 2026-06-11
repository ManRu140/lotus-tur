import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.db.base import Base
from app.db.session import get_session
from app.main import app


TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture(scope="function")
async def test_session():
    engine = create_async_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
    async_session = async_sessionmaker(engine, expire_on_commit=False)

    import app.models

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def client(test_session):
    app.dependency_overrides[get_session] = lambda: test_session

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac

    app.dependency_overrides.clear()


class TestAuth:
    @pytest.mark.asyncio
    async def test_register_success(self, client: AsyncClient):
        resp = await client.post("/api/auth/register", json={
            "username": "TestUser1",
            "email": "test@example.com",
            "password": "SecurePass1",
        })
        assert resp.status_code == 201
        data = resp.json()
        assert "access_token" in data
        assert data["username"] == "TestUser1"

    @pytest.mark.asyncio
    async def test_register_duplicate_username(self, client: AsyncClient):
        payload = {
            "username": "DuplicateUser",
            "email": "user1@example.com",
            "password": "SecurePass1",
        }
        await client.post("/api/auth/register", json=payload)

        payload["email"] = "user2@example.com"
        resp = await client.post("/api/auth/register", json=payload)
        assert resp.status_code == 409

    @pytest.mark.asyncio
    async def test_register_weak_password(self, client: AsyncClient):
        resp = await client.post("/api/auth/register", json={
            "username": "WeakPassUser",
            "email": "weak@example.com",
            "password": "weak",
        })
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_login_success(self, client: AsyncClient):
        await client.post("/api/auth/register", json={
            "username": "LoginUser",
            "email": "login@example.com",
            "password": "SecurePass1",
        })
        resp = await client.post("/api/auth/login", json={
            "username": "LoginUser",
            "password": "SecurePass1",
        })
        assert resp.status_code == 200
        assert "access_token" in resp.json()

    @pytest.mark.asyncio
    async def test_login_wrong_password(self, client: AsyncClient):
        await client.post("/api/auth/register", json={
            "username": "WrongPassUser",
            "email": "wrongpass@example.com",
            "password": "SecurePass1",
        })
        resp = await client.post("/api/auth/login", json={
            "username": "WrongPassUser",
            "password": "wrongpassword",
        })
        assert resp.status_code == 401


class TestProfile:
    async def _register_and_get_token(self, client: AsyncClient, suffix: str = "") -> str:
        resp = await client.post("/api/auth/register", json={
            "username": f"ProfileUser{suffix}",
            "email": f"profile{suffix}@example.com",
            "password": "SecurePass1",
        })
        return resp.json()["access_token"]

    @pytest.mark.asyncio
    async def test_get_profile(self, client: AsyncClient):
        token = await self._register_and_get_token(client, "A")
        resp = await client.get(
            "/api/profile/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["username"] == "ProfileUserA"

    @pytest.mark.asyncio
    async def test_update_username(self, client: AsyncClient):
        token = await self._register_and_get_token(client, "B")
        resp = await client.patch(
            "/api/profile/username",
            json={"username": "NewNameB"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["username"] == "NewNameB"

    @pytest.mark.asyncio
    async def test_get_profile_unauthorized(self, client: AsyncClient):
        resp = await client.get("/api/profile/me")
        assert resp.status_code == 401


class TestSecurity:
    @pytest.mark.asyncio
    async def test_invalid_token(self, client: AsyncClient):
        resp = await client.get(
            "/api/profile/me",
            headers={"Authorization": "Bearer not_a_valid_token"},
        )
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_booking_requires_auth(self, client: AsyncClient):
        resp = await client.post("/api/bookings", json={
            "tour_id": "askold",
            "first_name": "Иван",
            "phone": "+79001234567",
            "email": "ivan@example.com",
            "tour_date": "2027-07-01",
        })
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_username_with_invalid_chars(self, client: AsyncClient):
        resp = await client.post("/api/auth/register", json={
            "username": "user<script>",
            "email": "xss@example.com",
            "password": "SecurePass1",
        })
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_booking_past_date(self, client: AsyncClient):

        reg = await client.post("/api/auth/register", json={
            "username": "PastDateUser",
            "email": "pastdate@example.com",
            "password": "SecurePass1",
        })
        token = reg.json()["access_token"]

        resp = await client.post(
            "/api/bookings",
            json={
                "tour_id": "askold",
                "first_name": "Иван",
                "phone": "+79001234567",
                "email": "ivan@example.com",
                "tour_date": "2020-01-01",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 422
