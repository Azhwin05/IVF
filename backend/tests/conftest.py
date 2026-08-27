"""
Test fixtures. Runs against a real PostgreSQL instance (TEST_DATABASE_URL,
defaulting to a dedicated `archana_hmis_test` database) because several
models use Postgres-specific types (UUID, INET) that SQLite can't
represent — an in-memory SQLite test suite would be testing a different
database engine's behavior than production runs on, which defeats the
purpose per spec §37 ("Integration tests: API, Database, Transactions,
Authentication").

Async-engine lifetime note: asyncpg connections are bound to the event
loop they were created on. pytest-asyncio gives each test function its
own event loop by default, so every async engine/connection/session used
by a test must be created AND torn down within that same test — nothing
async-engine-related may be session-scoped here. Schema creation (which
only needs to happen once) is done with its own throwaway `asyncio.run()`
call outside pytest-asyncio's loop management entirely, in a plain
sync session-scoped fixture.

Each test gets a fresh connection wrapped in an outer transaction that's
rolled back at teardown, so tests never leave data behind for the next
test to trip over.
"""
import asyncio
import os

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

os.environ.setdefault(
    "DATABASE_URL",
    os.environ.get("TEST_DATABASE_URL", "postgresql+asyncpg://archana:archana_dev@localhost:5432/archana_hmis_test"),
)
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-not-for-production-use-only-in-ci")

from app.core import all_models  # noqa: E402  (must import after env vars are set)
from app.core.database import Base, get_db
from app.core.security import hash_password
from app.main import app
from app.roles.models import Role
from app.roles.seed import seed_roles_and_permissions
from app.users.models import User


@pytest.fixture(scope="session", autouse=True)
def _create_schema_once():
    """Plain sync fixture — deliberately NOT using pytest_asyncio so this
    runs on its own short-lived event loop via asyncio.run(), fully
    independent of whatever loop pytest-asyncio hands to individual test
    functions later."""
    async def _create():
        url = os.environ["DATABASE_URL"]
        eng = create_async_engine(url)
        async with eng.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)
        await eng.dispose()

    asyncio.run(_create())
    yield


@pytest_asyncio.fixture
async def db_session():
    """Fresh engine + connection + transaction, created and torn down
    entirely within this test's own event loop."""
    url = os.environ["DATABASE_URL"]
    engine = create_async_engine(url)
    connection = await engine.connect()
    transaction = await connection.begin()
    # create_savepoint: every session.commit() the app/fixtures make only
    # releases a SAVEPOINT, not the outer transaction — so the final
    # `transaction.rollback()` below always undoes the whole test,
    # regardless of how many times application code commits along the way.
    session_factory = async_sessionmaker(bind=connection, expire_on_commit=False, join_transaction_mode="create_savepoint")
    session = session_factory()

    yield session

    await session.close()
    await transaction.rollback()
    await connection.close()
    await engine.dispose()


@pytest_asyncio.fixture
async def client(db_session: AsyncSession):
    async def override_get_db():
        """Mirrors app.core.database.get_db's real commit-on-success /
        rollback-on-exception semantics exactly — a test override that
        just `yield`ed the session with no exception handling would let a
        failed request's partial changes leak into subsequent requests
        within the same test, masking real transactional bugs instead of
        catching them. Because db_session's savepoint mode makes commit()
        release only a SAVEPOINT (see db_session's docstring), this stays
        safely nested inside the test's own outer rollback."""
        try:
            yield db_session
            await db_session.commit()
        except Exception:
            await db_session.rollback()
            raise

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def seeded_roles(db_session: AsyncSession):
    await seed_roles_and_permissions(db_session)
    await db_session.commit()


@pytest_asyncio.fixture
async def doctor_user(db_session: AsyncSession, seeded_roles):
    from sqlalchemy import select
    role = (await db_session.execute(select(Role).where(Role.code == "doctor"))).scalar_one()
    user = User(
        employee_code="TEST-DOC-001", full_name="Dr. Test Doctor", email="doctor@example.com",
        role_id=role.id, password_hash=hash_password("TestPass123!"),
    )
    db_session.add(user)
    await db_session.commit()
    return user


@pytest_asyncio.fixture
async def auth_headers(client: AsyncClient, doctor_user: User) -> dict:
    resp = await client.post("/api/v1/auth/login", json={"email": "doctor@example.com", "password": "TestPass123!"})
    assert resp.status_code == 200, resp.text
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def admin_user(db_session: AsyncSession, seeded_roles):
    """Administrator role holds every permission (ROLE_DEFAULTS["administrator"]
    = ["*"]) — used by tests that exercise business logic (billing,
    pharmacy) rather than the permission matrix itself, so a missing
    permission never masquerades as a business-logic failure."""
    from sqlalchemy import select
    role = (await db_session.execute(select(Role).where(Role.code == "administrator"))).scalar_one()
    user = User(
        employee_code="TEST-ADM-001", full_name="Test Administrator", email="admin@example.com",
        role_id=role.id, password_hash=hash_password("TestPass123!"),
    )
    db_session.add(user)
    await db_session.commit()
    return user


@pytest_asyncio.fixture
async def admin_headers(client: AsyncClient, admin_user: User) -> dict:
    resp = await client.post("/api/v1/auth/login", json={"email": "admin@example.com", "password": "TestPass123!"})
    assert resp.status_code == 200, resp.text
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def sample_patient(db_session: AsyncSession):
    from app.patients.models import Patient
    patient = Patient(uhid="TEST-2026-00001", full_name="Test Patient", gender="female")
    db_session.add(patient)
    await db_session.commit()
    return patient
