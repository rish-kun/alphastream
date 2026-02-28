"""Tests for core security functions (JWT + bcrypt)."""

from __future__ import annotations

import time

import pytest

from app.core.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    verify_password,
    verify_token,
)


class TestHashPassword:
    def test_returns_string(self):
        result = hash_password("mypassword")
        assert isinstance(result, str)

    def test_produces_bcrypt_hash(self):
        result = hash_password("mypassword")
        assert result.startswith("$2b$")

    def test_different_passwords_different_hashes(self):
        h1 = hash_password("password1")
        h2 = hash_password("password2")
        assert h1 != h2

    def test_same_password_different_salt(self):
        h1 = hash_password("same")
        h2 = hash_password("same")
        assert h1 != h2  # Different salts each time


class TestVerifyPassword:
    def test_correct_password(self):
        hashed = hash_password("correct")
        assert verify_password("correct", hashed) is True

    def test_wrong_password(self):
        hashed = hash_password("correct")
        assert verify_password("wrong", hashed) is False

    def test_empty_password(self):
        hashed = hash_password("")
        assert verify_password("", hashed) is True

    def test_unicode_password(self):
        password = "p@$$w0rd_ñ_日本語"
        hashed = hash_password(password)
        assert verify_password(password, hashed) is True


class TestCreateAccessToken:
    def test_returns_string(self):
        token = create_access_token(data={"sub": "user-123"})
        assert isinstance(token, str)

    def test_contains_three_parts(self):
        token = create_access_token(data={"sub": "user-123"})
        parts = token.split(".")
        assert len(parts) == 3  # header.payload.signature

    def test_payload_contains_sub(self):
        token = create_access_token(data={"sub": "user-123"})
        payload = verify_token(token)
        assert payload["sub"] == "user-123"

    def test_payload_contains_type_access(self):
        token = create_access_token(data={"sub": "user-123"})
        payload = verify_token(token)
        assert payload["type"] == "access"

    def test_payload_contains_expiry(self):
        token = create_access_token(data={"sub": "user-123"})
        payload = verify_token(token)
        assert "exp" in payload


class TestCreateRefreshToken:
    def test_returns_string(self):
        token = create_refresh_token(data={"sub": "user-123"})
        assert isinstance(token, str)

    def test_payload_contains_type_refresh(self):
        token = create_refresh_token(data={"sub": "user-123"})
        payload = verify_token(token)
        assert payload["type"] == "refresh"

    def test_different_from_access_token(self):
        access = create_access_token(data={"sub": "user-123"})
        refresh = create_refresh_token(data={"sub": "user-123"})
        assert access != refresh


class TestVerifyToken:
    def test_valid_token(self):
        token = create_access_token(data={"sub": "user-123"})
        payload = verify_token(token)
        assert payload["sub"] == "user-123"

    def test_invalid_token_raises(self):
        with pytest.raises(ValueError, match="Invalid token"):
            verify_token("not.a.valid.token")

    def test_tampered_token_raises(self):
        token = create_access_token(data={"sub": "user-123"})
        # Tamper with the signature portion (after the last dot)
        parts = token.rsplit(".", 1)
        sig = parts[1]
        # Flip multiple characters in the signature to ensure invalidation
        tampered_sig = sig[:4] + "XXXX" + sig[8:]
        tampered = parts[0] + "." + tampered_sig
        with pytest.raises(ValueError):
            verify_token(tampered)

    def test_preserves_custom_data(self):
        token = create_access_token(data={"sub": "user-123", "custom": "value"})
        payload = verify_token(token)
        assert payload["custom"] == "value"
