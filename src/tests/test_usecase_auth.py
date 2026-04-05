import pytest
from unittest.mock import AsyncMock, patch
from uuid import UUID

from src.application.use_case.auth import DummyLoginUseCase, RegisterUseCase, LoginUseCase
from src.core.domain.models import User
from src.infrastructure.auth.jwt import DUMMY_ADMIN_UUID, DUMMY_USER_UUID


def _make_user(uid: UUID, role: str, email: str = "test@test.com", hashed_password: str = None) -> User:
    return User(id=uid, email=email, role=role, hashed_password=hashed_password, created_at=None)


@pytest.mark.asyncio
async def test_dummy_login_admin_returns_token():
    mock_repo = AsyncMock()
    mock_repo.get_or_create_dummy.return_value = _make_user(UUID(DUMMY_ADMIN_UUID), "admin")

    with patch("src.application.use_case.auth.create_token", return_value="mocked_token") as mock_create:
        use_case = DummyLoginUseCase(mock_repo)
        token = await use_case.execute("admin")

    mock_create.assert_called_once_with(user_id=DUMMY_ADMIN_UUID, role="admin")
    assert token == "mocked_token"


@pytest.mark.asyncio
async def test_dummy_login_user_returns_token():
    mock_repo = AsyncMock()
    mock_repo.get_or_create_dummy.return_value = _make_user(UUID(DUMMY_USER_UUID), "user")

    with patch("src.application.use_case.auth.create_token", return_value="user_token"):
        use_case = DummyLoginUseCase(mock_repo)
        token = await use_case.execute("user")

    assert token == "user_token"


@pytest.mark.asyncio
async def test_dummy_login_invalid_role():
    mock_repo = AsyncMock()
    use_case = DummyLoginUseCase(mock_repo)
    with pytest.raises(ValueError, match="INVALID_REQUEST"):
        await use_case.execute("superuser")


@pytest.mark.asyncio
async def test_register_success():
    mock_repo = AsyncMock()
    new_uid = UUID("ffffffff-ffff-ffff-ffff-ffffffffffff")
    mock_repo.get_by_email.return_value = None
    mock_repo.create.return_value = _make_user(new_uid, "user", email="new@test.com", hashed_password="hashed")

    use_case = RegisterUseCase(mock_repo)
    user = await use_case.execute("new@test.com", "password123")

    mock_repo.create.assert_called_once()
    assert user.email == "new@test.com"


@pytest.mark.asyncio
async def test_register_duplicate_email():
    mock_repo = AsyncMock()
    existing = _make_user(UUID(DUMMY_USER_UUID), "user", email="exists@test.com")
    mock_repo.get_by_email.return_value = existing

    use_case = RegisterUseCase(mock_repo)
    with pytest.raises(ValueError, match="INVALID_REQUEST"):
        await use_case.execute("exists@test.com", "password123")


@pytest.mark.asyncio
async def test_login_success():
    from passlib.context import CryptContext
    pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")
    hashed = pwd_ctx.hash("correct_password")

    mock_repo = AsyncMock()
    mock_repo.get_by_email.return_value = _make_user(
        UUID(DUMMY_USER_UUID), "user", email="u@test.com", hashed_password=hashed
    )

    with patch("src.application.use_case.auth.create_token", return_value="login_token"):
        use_case = LoginUseCase(mock_repo)
        token = await use_case.execute("u@test.com", "correct_password")

    assert token == "login_token"


@pytest.mark.asyncio
async def test_login_wrong_password():
    from passlib.context import CryptContext
    pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")
    hashed = pwd_ctx.hash("correct_password")

    mock_repo = AsyncMock()
    mock_repo.get_by_email.return_value = _make_user(
        UUID(DUMMY_USER_UUID), "user", email="u@test.com", hashed_password=hashed
    )

    use_case = LoginUseCase(mock_repo)
    with pytest.raises(ValueError, match="UNAUTHORIZED"):
        await use_case.execute("u@test.com", "wrong_password")


@pytest.mark.asyncio
async def test_login_user_not_found():
    mock_repo = AsyncMock()
    mock_repo.get_by_email.return_value = None

    use_case = LoginUseCase(mock_repo)
    with pytest.raises(ValueError, match="UNAUTHORIZED"):
        await use_case.execute("nobody@test.com", "password")
