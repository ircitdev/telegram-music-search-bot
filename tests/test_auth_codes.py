"""Tests for authentication codes system."""
import os
import pytest
import tempfile
import time


class TestAuthCodes:
    """Test auth codes generation and verification."""

    @pytest.fixture(autouse=True)
    def setup(self, tmp_path):
        """Setup test environment."""
        # Use temp file for auth codes
        self.auth_file = tmp_path / "auth_codes.json"

        # Patch the auth codes file path
        import src.utils.auth_codes as auth_module
        self._original_path = auth_module.AUTH_CODES_FILE
        auth_module.AUTH_CODES_FILE = self.auth_file

        yield

        # Restore original path
        auth_module.AUTH_CODES_FILE = self._original_path

    def test_generate_auth_code(self):
        """Test generating auth code."""
        from src.utils.auth_codes import generate_auth_code

        code = generate_auth_code(123456789, "testuser")

        assert code is not None
        assert len(code) > 20
        assert isinstance(code, str)

    def test_verify_auth_code_valid(self):
        """Test verifying valid auth code."""
        from src.utils.auth_codes import generate_auth_code, verify_auth_code

        code = generate_auth_code(123456789, "testuser")
        result = verify_auth_code(code)

        assert result is not None
        assert result["user_id"] == 123456789
        assert result["username"] == "testuser"
        assert result["is_admin"] == True
        assert "session_token" in result

    def test_verify_auth_code_invalid(self):
        """Test verifying invalid auth code."""
        from src.utils.auth_codes import verify_auth_code

        result = verify_auth_code("invalid_code_here")

        assert result is None

    def test_auth_code_single_use(self):
        """Test that auth code can only be used once."""
        from src.utils.auth_codes import generate_auth_code, verify_auth_code

        code = generate_auth_code(123456789, "testuser")

        # First use should succeed
        result1 = verify_auth_code(code)
        assert result1 is not None

        # Second use should fail
        result2 = verify_auth_code(code)
        assert result2 is None

    def test_create_session(self):
        """Test creating session token."""
        from src.utils.auth_codes import create_session

        token = create_session(123456789, "testuser")

        assert token is not None
        assert len(token) > 30

    def test_verify_session_valid(self):
        """Test verifying valid session."""
        from src.utils.auth_codes import create_session, verify_session

        token = create_session(123456789, "testuser")
        result = verify_session(token)

        assert result is not None
        assert result["user_id"] == 123456789
        assert result["is_admin"] == True

    def test_verify_session_invalid(self):
        """Test verifying invalid session."""
        from src.utils.auth_codes import verify_session

        result = verify_session("invalid_session_token")

        assert result is None

    def test_invalidate_session(self):
        """Test invalidating session."""
        from src.utils.auth_codes import create_session, verify_session, invalidate_session

        token = create_session(123456789, "testuser")

        # Session should be valid
        assert verify_session(token) is not None

        # Invalidate
        invalidate_session(token)

        # Session should be invalid now
        assert verify_session(token) is None
