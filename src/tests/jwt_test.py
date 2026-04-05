import pytest
from unittest.mock import patch
from src.infrastructure.auth.jwt import create_token, decode_token


def test_create_and_decode_valid_token():
    with patch("src.infrastructure.auth.jwt.settings") as mock_settings:
        mock_settings.JWT_SECRET_KEY = "test_secret"
        mock_settings.JWT_ALGORITHM = "HS256"
        mock_settings.ACCESS_TOKEN_EXPIRE_MINUTES = 30

        user_id = "123e4567-e89b-12d3-a456-426614174000"
        role = "user"
        token = create_token(user_id, role)
        payload = decode_token(token)

        assert payload["user_id"] == user_id
        assert payload["role"] == role
        assert "exp" in payload


def test_decode_invalid_token():
    with patch("src.infrastructure.auth.jwt.settings") as mock_settings:
        mock_settings.JWT_SECRET_KEY = "test_secret"
        mock_settings.JWT_ALGORITHM = "HS256"

        with pytest.raises(ValueError, match="Invalid token"):
            decode_token("invalid.token.string")


def test_decode_token_wrong_secret():
    with patch("src.infrastructure.auth.jwt.settings") as mock_settings:
        mock_settings.JWT_SECRET_KEY = "secret_a"
        mock_settings.JWT_ALGORITHM = "HS256"
        mock_settings.ACCESS_TOKEN_EXPIRE_MINUTES = 30
        token = create_token("some_id", "user")

    with patch("src.infrastructure.auth.jwt.settings") as mock_settings2:
        mock_settings2.JWT_SECRET_KEY = "secret_b"
        mock_settings2.JWT_ALGORITHM = "HS256"

        with pytest.raises(ValueError, match="Invalid token"):
            decode_token(token)


def test_decode_expired_token():
    with patch("src.infrastructure.auth.jwt.settings") as mock_settings:
        mock_settings.JWT_SECRET_KEY = "test_secret"
        mock_settings.JWT_ALGORITHM = "HS256"
        mock_settings.ACCESS_TOKEN_EXPIRE_MINUTES = -1
        token = create_token("some_id", "admin")

    with patch("src.infrastructure.auth.jwt.settings") as mock_settings2:
        mock_settings2.JWT_SECRET_KEY = "test_secret"
        mock_settings2.JWT_ALGORITHM = "HS256"

        with pytest.raises(ValueError, match="Invalid token"):
            decode_token(token)


def test_token_contains_expected_fields():
    with patch("src.infrastructure.auth.jwt.settings") as mock_settings:
        mock_settings.JWT_SECRET_KEY = "test_secret"
        mock_settings.JWT_ALGORITHM = "HS256"
        mock_settings.ACCESS_TOKEN_EXPIRE_MINUTES = 30

        token = create_token("abc-123", "admin")
        payload = decode_token(token)

        assert payload["user_id"] == "abc-123"
        assert payload["role"] == "admin"
