"""Tests for custom exception classes and handlers."""

from __future__ import annotations

from app.core.exceptions import (
    ConflictError,
    ForbiddenError,
    NotFoundError,
    UnauthorizedError,
    ValidationError,
)


class TestNotFoundError:
    def test_message_without_identifier(self):
        exc = NotFoundError("Stock")
        assert str(exc) == "Stock not found"

    def test_message_with_identifier(self):
        exc = NotFoundError("Stock", "RELIANCE")
        assert str(exc) == "Stock 'RELIANCE' not found"

    def test_attributes(self):
        exc = NotFoundError("User", "123")
        assert exc.resource == "User"
        assert exc.identifier == "123"


class TestUnauthorizedError:
    def test_default_message(self):
        exc = UnauthorizedError()
        assert exc.detail == "Not authenticated"

    def test_custom_message(self):
        exc = UnauthorizedError("Invalid token")
        assert exc.detail == "Invalid token"


class TestForbiddenError:
    def test_default_message(self):
        exc = ForbiddenError()
        assert exc.detail == "Not enough permissions"

    def test_custom_message(self):
        exc = ForbiddenError("Access denied")
        assert exc.detail == "Access denied"


class TestConflictError:
    def test_default_message(self):
        exc = ConflictError()
        assert exc.detail == "Resource already exists"

    def test_custom_message(self):
        exc = ConflictError("Email taken")
        assert exc.detail == "Email taken"


class TestValidationError:
    def test_default_message(self):
        exc = ValidationError()
        assert exc.detail == "Validation failed"

    def test_custom_message(self):
        exc = ValidationError("Bad input")
        assert exc.detail == "Bad input"
