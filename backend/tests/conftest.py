import asyncio
import uuid
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.database import Base, get_db
from app.main import app
from app.core.constants import UserRole
from app.core.security import create_access_token
from app.models.user import User, ResidentProfile
from app.models.organization import Organization

# Use SQLite for testing
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"

engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    async with TestSessionLocal() as session:
        yield session


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def resident_user(db_session: AsyncSession) -> User:
    user = User(
        id=uuid.uuid4(),
        phone="+212600000001",
        phone_verified=True,
        role=UserRole.RESIDENT,
        full_name="ساكن تجريبي",
        language="ar",
    )
    db_session.add(user)
    await db_session.flush()

    profile = ResidentProfile(
        user_id=user.id,
        family_size=4,
        special_cases=["children"],
        location_text="حي السلام",
    )
    db_session.add(profile)
    await db_session.commit()

    return user


@pytest_asyncio.fixture
async def org_user(db_session: AsyncSession) -> User:
    user = User(
        id=uuid.uuid4(),
        phone="+212600000002",
        phone_verified=True,
        role=UserRole.ORGANIZATION,
        full_name="مسؤول جمعية",
        language="ar",
    )
    db_session.add(user)
    await db_session.flush()

    org = Organization(
        user_id=user.id,
        name="جمعية الخير",
        service_types=["food", "medicine"],
        coverage_areas=["tanger"],
    )
    db_session.add(org)
    await db_session.commit()

    return user


@pytest_asyncio.fixture
async def coordinator_user(db_session: AsyncSession) -> User:
    user = User(
        id=uuid.uuid4(),
        phone="+212600000003",
        phone_verified=True,
        role=UserRole.COORDINATOR,
        full_name="منسق ميداني",
        language="ar",
    )
    db_session.add(user)
    await db_session.commit()

    return user


def get_auth_headers(user: User) -> dict:
    token = create_access_token({"sub": str(user.id), "role": user.role.value})
    return {"Authorization": f"Bearer {token}"}
