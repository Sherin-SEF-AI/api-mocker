import pytest
from datetime import datetime, timedelta
from api_mocker.auth_system import (
    AdvancedAuthSystem, UserRole, TokenType, 
    create_user, authenticate, auth_system
)
import jwt

# Test Data
VALID_USERNAME = "testuser"
VALID_EMAIL = "test@example.com"
VALID_PASSWORD = "StrongPassword123!"

@pytest.fixture
def auth():
    """Fresh auth system instance for each test"""
    return AdvancedAuthSystem(secret_key="test-secret-key")

def test_password_hashing(auth):
    """Test that passwords are hashed and not stored in plain text"""
    password = "MySecreTPassword123!"
    hashed = auth.hash_password(password)
    
    assert hashed != password
    assert auth.verify_password(password, hashed)
    assert not auth.verify_password("WrongPassword", hashed)

def test_register_user_success(auth):
    """Test successful user registration"""
    result = auth.register_user(
        username=VALID_USERNAME, 
        email=VALID_EMAIL, 
        password=VALID_PASSWORD
    )
    
    assert result["success"] is True
    assert "user_id" in result
    
    user = auth.users[result["user_id"]]
    assert user.username == VALID_USERNAME
    assert user.email == VALID_EMAIL
    assert user.password_hash != VALID_PASSWORD

def test_register_user_duplicate_email(auth):
    """Test registration with duplicate email"""
    auth.register_user(VALID_USERNAME, VALID_EMAIL, VALID_PASSWORD)
    
    # Try again
    result = auth.register_user("otheruser", VALID_EMAIL, VALID_PASSWORD)
    assert result["success"] is False
    assert "already registered" in result["error"]

def test_authenticate_success(auth):
    """Test successful authentication"""
    # Register first
    auth.register_user(VALID_USERNAME, VALID_EMAIL, VALID_PASSWORD)
    
    # Login
    result = auth.authenticate_user(VALID_EMAIL, VALID_PASSWORD)
    
    assert result["success"] is True
    assert "access_token" in result
    assert "refresh_token" in result
    assert result["user"]["email"] == VALID_EMAIL

def test_authenticate_invalid_credentials(auth):
    """Test login with wrong password"""
    auth.register_user(VALID_USERNAME, VALID_EMAIL, VALID_PASSWORD)
    
    result = auth.authenticate_user(VALID_EMAIL, "WrongPassword!")
    assert result["success"] is False
    assert "Invalid credentials" in result["error"]

def test_jwt_token_validation(auth):
    """Test JWT token creation and verification"""
    auth.register_user(VALID_USERNAME, VALID_EMAIL, VALID_PASSWORD)
    login_result = auth.authenticate_user(VALID_EMAIL, VALID_PASSWORD)
    token = login_result["access_token"]
    
    # Valid token
    validation = auth.verify_token(token)
    assert validation["valid"] is True
    assert validation["user_id"] == login_result["user"]["id"]
    
    # Invalid token
    invalid_validation = auth.verify_token(token + "invalid")
    assert invalid_validation["valid"] is False

def test_api_key_system(auth):
    """Test API key creation and verification"""
    reg = auth.register_user(VALID_USERNAME, VALID_EMAIL, VALID_PASSWORD)
    user_id = reg["user_id"]
    
    # Create valid key
    key_result = auth.create_api_key(user_id, "Test Key")
    assert key_result["success"] is True
    api_key = key_result["api_key"]
    
    # Verify key
    verify = auth.verify_api_key(api_key)
    assert verify["valid"] is True
    assert verify["user_id"] == user_id
    
    # Verify invalid key
    assert auth.verify_api_key("invalid_key")["valid"] is False

def test_password_policy(auth):
    """Test weak password rejection"""
    # Use password long enough (8 chars) but simple (fails complexity)
    result = auth.register_user("weak", "weak@test.com", "password123")
    assert result["success"] is False
    assert "errors" in result
    assert len(result["errors"]) > 0

def test_mfa_flow(auth):
    """Test MFA setup and verification"""
    reg = auth.register_user(VALID_USERNAME, VALID_EMAIL, VALID_PASSWORD)
    user_id = reg["user_id"]
    
    # Setup MFA
    setup = auth.setup_mfa(user_id)
    assert setup["success"] is True
    secret = setup["secret"]
    
    # Generate valid TOTP
    import pyotp
    totp = pyotp.TOTP(secret)
    valid_code = totp.now()
    
    # Enable MFA
    enable = auth.enable_mfa(user_id, valid_code)
    assert enable["success"] is True
    assert auth.users[user_id].mfa_enabled is True
    
    # Verify Code
    assert auth.verify_mfa(user_id, valid_code) is True
    assert auth.verify_mfa(user_id, "000000") is False

def test_rate_limiting(auth):
    """Test login rate limiting"""
    auth.max_login_attempts = 2
    
    # Fail twice
    auth.authenticate_user("hacker@example.com", "wrong")
    auth.authenticate_user("hacker@example.com", "wrong")
    
    # Third attempt should be blocked even if password matches (conceptually)
    # But here we verify the "Too many login attempts" error comes back on next try
    result = auth.authenticate_user("hacker@example.com", "wrong")
    assert result["success"] is False
    assert "Too many login attempts" in result["error"]
