"""Integration tests for core API flows."""

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.main import app
from app.database.session import get_db, Base
from app.core.config import settings

# Test DB URL
TEST_DB_URL = settings.DATABASE_URL.replace("/studycompanion", "/studycompanion_test")

engine = create_async_engine(TEST_DB_URL, echo=False)
test_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def override_get_db():
    async with test_session() as session:
        yield session


app.dependency_overrides[get_db] = override_get_db


@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    """Create tables before each test, drop after."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest_asyncio.fixture
async def auth_client(client: AsyncClient):
    """Client with authenticated user."""
    # Register
    res = await client.post("/api/auth/register", json={
        "email": "test@test.com",
        "password": "test12345678",
        "full_name": "Test User",
    })
    assert res.status_code == 201
    token = res.json()["access_token"]
    client.headers["Authorization"] = f"Bearer {token}"
    return client, res.json()["user"]


class TestAuth:
    async def test_register(self, client: AsyncClient):
        res = await client.post("/api/auth/register", json={
            "email": "new@test.com", "password": "password123", "full_name": "New User",
        })
        assert res.status_code == 201
        data = res.json()
        assert "access_token" in data
        assert data["user"]["email"] == "new@test.com"

    async def test_register_duplicate(self, client: AsyncClient):
        await client.post("/api/auth/register", json={
            "email": "dup@test.com", "password": "password123", "full_name": "Dup User",
        })
        res = await client.post("/api/auth/register", json={
            "email": "dup@test.com", "password": "password123", "full_name": "Dup User",
        })
        assert res.status_code == 409

    async def test_login(self, client: AsyncClient):
        await client.post("/api/auth/register", json={
            "email": "login@test.com", "password": "password123", "full_name": "Login User",
        })
        res = await client.post("/api/auth/login", json={
            "email": "login@test.com", "password": "password123",
        })
        assert res.status_code == 200
        assert "access_token" in res.json()

    async def test_login_wrong_password(self, client: AsyncClient):
        await client.post("/api/auth/register", json={
            "email": "wrong@test.com", "password": "password123", "full_name": "User",
        })
        res = await client.post("/api/auth/login", json={
            "email": "wrong@test.com", "password": "wrongpassword",
        })
        assert res.status_code == 401

    async def test_me(self, auth_client):
        client, user = auth_client
        res = await client.get("/api/auth/me")
        assert res.status_code == 200
        assert res.json()["email"] == "test@test.com"

    async def test_me_unauthenticated(self, client: AsyncClient):
        res = await client.get("/api/auth/me")
        assert res.status_code == 403


class TestSpaces:
    async def test_create_space(self, auth_client):
        client, _ = auth_client
        res = await client.post("/api/spaces/", json={"name": "CS 101", "description": "Computer Science"})
        assert res.status_code == 201
        assert res.json()["name"] == "CS 101"

    async def test_list_spaces(self, auth_client):
        client, _ = auth_client
        await client.post("/api/spaces/", json={"name": "Space 1"})
        await client.post("/api/spaces/", json={"name": "Space 2"})
        res = await client.get("/api/spaces/")
        assert res.status_code == 200
        assert len(res.json()) == 2


class TestProjects:
    async def test_create_project(self, auth_client):
        client, _ = auth_client
        space = await client.post("/api/spaces/", json={"name": "Space"})
        space_id = space.json()["id"]
        res = await client.post("/api/projects/", json={
            "name": "ML Project", "description": "Machine Learning", "space_id": space_id, "learning_goal": "Master ML basics",
        })
        assert res.status_code == 201
        assert res.json()["name"] == "ML Project"

    async def test_project_ownership(self, client: AsyncClient):
        # Register two users
        r1 = await client.post("/api/auth/register", json={"email": "u1@t.com", "password": "password123", "full_name": "U1"})
        t1 = r1.json()["access_token"]

        r2 = await client.post("/api/auth/register", json={"email": "u2@t.com", "password": "password123", "full_name": "U2"})
        t2 = r2.json()["access_token"]

        # User 1 creates space+project
        client.headers["Authorization"] = f"Bearer {t1}"
        s = await client.post("/api/spaces/", json={"name": "Private"})
        p = await client.post("/api/projects/", json={"name": "Secret", "space_id": s.json()["id"]})
        pid = p.json()["id"]

        # User 2 tries to access
        client.headers["Authorization"] = f"Bearer {t2}"
        res = await client.get(f"/api/projects/{pid}")
        assert res.status_code == 404


class TestHealth:
    async def test_health(self, client: AsyncClient):
        res = await client.get("/api/health")
        assert res.status_code == 200
        assert res.json()["status"] == "healthy"
