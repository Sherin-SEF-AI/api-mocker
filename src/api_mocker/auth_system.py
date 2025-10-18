"""
Advanced Authentication System

This module provides comprehensive authentication capabilities including:
- OAuth2 with multiple providers (Google, GitHub, Microsoft, etc.)
- JWT token management with refresh tokens
- API key authentication
- Role-based access control (RBAC)
- Multi-factor authentication (MFA)
- Session management
- Password policies and validation
"""

import jwt
import hashlib
import secrets
import time
from typing import Any, Dict, List, Optional, Union, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import json
import base64
import hmac
import pyotp
import qrcode
from io import BytesIO


class AuthProvider(Enum):
    """Authentication providers"""
    LOCAL = "local"
    GOOGLE = "google"
    GITHUB = "github"
    MICROSOFT = "microsoft"
    FACEBOOK = "facebook"
    TWITTER = "twitter"
    LINKEDIN = "linkedin"
    DISCORD = "discord"


class TokenType(Enum):
    """Token types"""
    ACCESS = "access"
    REFRESH = "refresh"
    API_KEY = "api_key"
    MFA = "mfa"


class UserRole(Enum):
    """User roles"""
    ADMIN = "admin"
    USER = "user"
    MODERATOR = "moderator"
    GUEST = "guest"
    API_USER = "api_user"


@dataclass
class User:
    """User model"""
    id: str
    username: str
    email: str
    password_hash: str
    roles: List[UserRole] = field(default_factory=lambda: [UserRole.USER])
    is_active: bool = True
    is_verified: bool = False
    created_at: datetime = field(default_factory=datetime.now)
    last_login: Optional[datetime] = None
    mfa_secret: Optional[str] = None
    mfa_enabled: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Token:
    """Token model"""
    token: str
    token_type: TokenType
    user_id: str
    expires_at: datetime
    created_at: datetime = field(default_factory=datetime.now)
    is_revoked: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class APIKey:
    """API Key model"""
    key: str
    name: str
    user_id: str
    permissions: List[str] = field(default_factory=list)
    rate_limit: Optional[int] = None
    expires_at: Optional[datetime] = None
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.now)
    last_used: Optional[datetime] = None
    usage_count: int = 0


@dataclass
class OAuth2Provider:
    """OAuth2 provider configuration"""
    name: AuthProvider
    client_id: str
    client_secret: str
    authorization_url: str
    token_url: str
    user_info_url: str
    scope: List[str] = field(default_factory=list)
    redirect_uri: str = ""


@dataclass
class AuthSession:
    """Authentication session"""
    session_id: str
    user_id: str
    ip_address: str
    user_agent: str
    created_at: datetime = field(default_factory=datetime.now)
    last_activity: datetime = field(default_factory=datetime.now)
    expires_at: datetime = field(default_factory=lambda: datetime.now() + timedelta(hours=24))
    is_active: bool = True


class PasswordValidator:
    """Password validation utility"""
    
    def __init__(self, min_length: int = 8, require_uppercase: bool = True,
                 require_lowercase: bool = True, require_numbers: bool = True,
                 require_special: bool = True):
        self.min_length = min_length
        self.require_uppercase = require_uppercase
        self.require_lowercase = require_lowercase
        self.require_numbers = require_numbers
        self.require_special = require_special
    
    def validate(self, password: str) -> Dict[str, Any]:
        """Validate password and return validation result"""
        errors = []
        
        if len(password) < self.min_length:
            errors.append(f"Password must be at least {self.min_length} characters long")
        
        if self.require_uppercase and not any(c.isupper() for c in password):
            errors.append("Password must contain at least one uppercase letter")
        
        if self.require_lowercase and not any(c.islower() for c in password):
            errors.append("Password must contain at least one lowercase letter")
        
        if self.require_numbers and not any(c.isdigit() for c in password):
            errors.append("Password must contain at least one number")
        
        if self.require_special and not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
            errors.append("Password must contain at least one special character")
        
        return {
            "is_valid": len(errors) == 0,
            "errors": errors,
            "strength": self._calculate_strength(password)
        }
    
    def _calculate_strength(self, password: str) -> str:
        """Calculate password strength"""
        score = 0
        
        if len(password) >= 8:
            score += 1
        if len(password) >= 12:
            score += 1
        if any(c.isupper() for c in password):
            score += 1
        if any(c.islower() for c in password):
            score += 1
        if any(c.isdigit() for c in password):
            score += 1
        if any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
            score += 1
        
        if score <= 2:
            return "weak"
        elif score <= 4:
            return "medium"
        else:
            return "strong"


class JWTManager:
    """JWT token management"""
    
    def __init__(self, secret_key: str, algorithm: str = "HS256"):
        self.secret_key = secret_key
        self.algorithm = algorithm
    
    def create_token(self, user_id: str, token_type: TokenType, 
                    expires_in: int = 3600, **kwargs) -> str:
        """Create a JWT token"""
        now = datetime.utcnow()
        payload = {
            "user_id": user_id,
            "token_type": token_type.value,
            "iat": now,
            "exp": now + timedelta(seconds=expires_in),
            **kwargs
        }
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
    
    def verify_token(self, token: str) -> Dict[str, Any]:
        """Verify and decode a JWT token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return {"valid": True, "payload": payload}
        except jwt.ExpiredSignatureError:
            return {"valid": False, "error": "Token expired"}
        except jwt.InvalidTokenError:
            return {"valid": False, "error": "Invalid token"}
    
    def refresh_token(self, refresh_token: str) -> Optional[str]:
        """Refresh an access token using refresh token"""
        result = self.verify_token(refresh_token)
        if result["valid"] and result["payload"]["token_type"] == "refresh":
            user_id = result["payload"]["user_id"]
            return self.create_token(user_id, TokenType.ACCESS)
        return None


class MFAHandler:
    """Multi-factor authentication handler"""
    
    def __init__(self):
        self.totp = pyotp.TOTP
    
    def generate_secret(self) -> str:
        """Generate a TOTP secret"""
        return pyotp.random_base32()
    
    def generate_qr_code(self, user_email: str, secret: str, issuer: str = "API-Mocker") -> str:
        """Generate QR code for MFA setup"""
        totp_uri = pyotp.totp.TOTP(secret).provisioning_uri(
            name=user_email,
            issuer_name=issuer
        )
        return totp_uri
    
    def verify_code(self, secret: str, code: str) -> bool:
        """Verify TOTP code"""
        totp = pyotp.TOTP(secret)
        return totp.verify(code, valid_window=1)
    
    def generate_backup_codes(self, count: int = 10) -> List[str]:
        """Generate backup codes for MFA"""
        return [secrets.token_hex(4).upper() for _ in range(count)]


class AdvancedAuthSystem:
    """Main authentication system"""
    
    def __init__(self, secret_key: str = None):
        self.secret_key = secret_key or secrets.token_hex(32)
        self.jwt_manager = JWTManager(self.secret_key)
        self.mfa_handler = MFAHandler()
        self.password_validator = PasswordValidator()
        
        # Storage
        self.users: Dict[str, User] = {}
        self.tokens: Dict[str, Token] = {}
        self.api_keys: Dict[str, APIKey] = {}
        self.sessions: Dict[str, AuthSession] = {}
        self.oauth_providers: Dict[AuthProvider, OAuth2Provider] = {}
        
        # Rate limiting
        self.login_attempts: Dict[str, List[datetime]] = {}
        self.max_login_attempts = 5
        self.lockout_duration = 300  # 5 minutes
    
    def hash_password(self, password: str) -> str:
        """Hash a password using PBKDF2"""
        salt = secrets.token_hex(16)
        pwd_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
        return f"{salt}:{pwd_hash.hex()}"
    
    def verify_password(self, password: str, password_hash: str) -> bool:
        """Verify a password against its hash"""
        try:
            salt, hash_hex = password_hash.split(':')
            pwd_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
            return hmac.compare_digest(hash_hex, pwd_hash.hex())
        except ValueError:
            return False
    
    def register_user(self, username: str, email: str, password: str,
                     roles: List[UserRole] = None) -> Dict[str, Any]:
        """Register a new user"""
        # Validate password
        password_validation = self.password_validator.validate(password)
        if not password_validation["is_valid"]:
            return {
                "success": False,
                "errors": password_validation["errors"]
            }
        
        # Check if user already exists
        if any(user.email == email for user in self.users.values()):
            return {"success": False, "error": "Email already registered"}
        
        if any(user.username == username for user in self.users.values()):
            return {"success": False, "error": "Username already taken"}
        
        # Create user
        user_id = secrets.token_hex(16)
        user = User(
            id=user_id,
            username=username,
            email=email,
            password_hash=self.hash_password(password),
            roles=roles or [UserRole.USER]
        )
        
        self.users[user_id] = user
        
        return {
            "success": True,
            "user_id": user_id,
            "message": "User registered successfully"
        }
    
    def authenticate_user(self, email: str, password: str, 
                          ip_address: str = None, user_agent: str = None) -> Dict[str, Any]:
        """Authenticate a user with email and password"""
        # Check rate limiting
        if self._is_rate_limited(email):
            return {"success": False, "error": "Too many login attempts"}
        
        # Find user
        user = None
        for u in self.users.values():
            if u.email == email:
                user = u
                break
        
        if not user:
            self._record_failed_attempt(email)
            return {"success": False, "error": "Invalid credentials"}
        
        # Verify password
        if not self.verify_password(password, user.password_hash):
            self._record_failed_attempt(email)
            return {"success": False, "error": "Invalid credentials"}
        
        # Check if user is active
        if not user.is_active:
            return {"success": False, "error": "Account is disabled"}
        
        # Update last login
        user.last_login = datetime.now()
        
        # Create tokens
        access_token = self.jwt_manager.create_token(
            user.id, TokenType.ACCESS, expires_in=3600
        )
        refresh_token = self.jwt_manager.create_token(
            user.id, TokenType.REFRESH, expires_in=86400 * 7  # 7 days
        )
        
        # Create session
        session_id = secrets.token_hex(32)
        session = AuthSession(
            session_id=session_id,
            user_id=user.id,
            ip_address=ip_address or "unknown",
            user_agent=user_agent or "unknown"
        )
        self.sessions[session_id] = session
        
        # Clear failed attempts
        if email in self.login_attempts:
            del self.login_attempts[email]
        
        return {
            "success": True,
            "access_token": access_token,
            "refresh_token": refresh_token,
            "session_id": session_id,
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "roles": [role.value for role in user.roles],
                "mfa_enabled": user.mfa_enabled
            }
        }
    
    def verify_token(self, token: str) -> Dict[str, Any]:
        """Verify a JWT token"""
        result = self.jwt_manager.verify_token(token)
        if not result["valid"]:
            return result
        
        payload = result["payload"]
        user_id = payload.get("user_id")
        
        if user_id not in self.users:
            return {"valid": False, "error": "User not found"}
        
        user = self.users[user_id]
        if not user.is_active:
            return {"valid": False, "error": "User account is disabled"}
        
        return {
            "valid": True,
            "user_id": user_id,
            "payload": payload
        }
    
    def create_api_key(self, user_id: str, name: str, permissions: List[str] = None,
                      rate_limit: int = None, expires_in: int = None) -> Dict[str, Any]:
        """Create an API key for a user"""
        if user_id not in self.users:
            return {"success": False, "error": "User not found"}
        
        # Generate API key
        api_key = f"ak_{secrets.token_hex(32)}"
        
        # Set expiration
        expires_at = None
        if expires_in:
            expires_at = datetime.now() + timedelta(seconds=expires_in)
        
        key_obj = APIKey(
            key=api_key,
            name=name,
            user_id=user_id,
            permissions=permissions or [],
            rate_limit=rate_limit,
            expires_at=expires_at
        )
        
        self.api_keys[api_key] = key_obj
        
        return {
            "success": True,
            "api_key": api_key,
            "expires_at": expires_at.isoformat() if expires_at else None
        }
    
    def verify_api_key(self, api_key: str) -> Dict[str, Any]:
        """Verify an API key"""
        if api_key not in self.api_keys:
            return {"valid": False, "error": "Invalid API key"}
        
        key_obj = self.api_keys[api_key]
        
        if not key_obj.is_active:
            return {"valid": False, "error": "API key is disabled"}
        
        if key_obj.expires_at and datetime.now() > key_obj.expires_at:
            return {"valid": False, "error": "API key expired"}
        
        # Update usage
        key_obj.last_used = datetime.now()
        key_obj.usage_count += 1
        
        return {
            "valid": True,
            "user_id": key_obj.user_id,
            "permissions": key_obj.permissions,
            "rate_limit": key_obj.rate_limit
        }
    
    def setup_mfa(self, user_id: str) -> Dict[str, Any]:
        """Setup MFA for a user"""
        if user_id not in self.users:
            return {"success": False, "error": "User not found"}
        
        user = self.users[user_id]
        secret = self.mfa_handler.generate_secret()
        user.mfa_secret = secret
        
        qr_code_uri = self.mfa_handler.generate_qr_code(user.email, secret)
        backup_codes = self.mfa_handler.generate_backup_codes()
        
        return {
            "success": True,
            "secret": secret,
            "qr_code_uri": qr_code_uri,
            "backup_codes": backup_codes
        }
    
    def enable_mfa(self, user_id: str, code: str) -> Dict[str, Any]:
        """Enable MFA for a user"""
        if user_id not in self.users:
            return {"success": False, "error": "User not found"}
        
        user = self.users[user_id]
        if not user.mfa_secret:
            return {"success": False, "error": "MFA not set up"}
        
        if not self.mfa_handler.verify_code(user.mfa_secret, code):
            return {"success": False, "error": "Invalid MFA code"}
        
        user.mfa_enabled = True
        return {"success": True, "message": "MFA enabled successfully"}
    
    def verify_mfa(self, user_id: str, code: str) -> bool:
        """Verify MFA code"""
        if user_id not in self.users:
            return False
        
        user = self.users[user_id]
        if not user.mfa_enabled or not user.mfa_secret:
            return False
        
        return self.mfa_handler.verify_code(user.mfa_secret, code)
    
    def _is_rate_limited(self, email: str) -> bool:
        """Check if email is rate limited"""
        if email not in self.login_attempts:
            return False
        
        now = datetime.now()
        attempts = self.login_attempts[email]
        
        # Remove old attempts
        attempts = [attempt for attempt in attempts if now - attempt < timedelta(seconds=self.lockout_duration)]
        self.login_attempts[email] = attempts
        
        return len(attempts) >= self.max_login_attempts
    
    def _record_failed_attempt(self, email: str) -> None:
        """Record a failed login attempt"""
        if email not in self.login_attempts:
            self.login_attempts[email] = []
        
        self.login_attempts[email].append(datetime.now())
    
    def add_oauth_provider(self, provider: OAuth2Provider) -> None:
        """Add an OAuth2 provider"""
        self.oauth_providers[provider.name] = provider
    
    def get_oauth_authorization_url(self, provider: AuthProvider, state: str = None) -> str:
        """Get OAuth2 authorization URL"""
        if provider not in self.oauth_providers:
            raise ValueError(f"OAuth provider {provider} not configured")
        
        oauth_provider = self.oauth_providers[provider]
        state = state or secrets.token_urlsafe(32)
        
        params = {
            "client_id": oauth_provider.client_id,
            "redirect_uri": oauth_provider.redirect_uri,
            "scope": " ".join(oauth_provider.scope),
            "state": state,
            "response_type": "code"
        }
        
        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        return f"{oauth_provider.authorization_url}?{query_string}"
    
    def get_user_permissions(self, user_id: str) -> List[str]:
        """Get user permissions based on roles"""
        if user_id not in self.users:
            return []
        
        user = self.users[user_id]
        permissions = []
        
        for role in user.roles:
            if role == UserRole.ADMIN:
                permissions.extend(["read", "write", "delete", "admin"])
            elif role == UserRole.MODERATOR:
                permissions.extend(["read", "write", "moderate"])
            elif role == UserRole.USER:
                permissions.extend(["read", "write"])
            elif role == UserRole.API_USER:
                permissions.extend(["api_access"])
        
        return list(set(permissions))
    
    def check_permission(self, user_id: str, permission: str) -> bool:
        """Check if user has a specific permission"""
        user_permissions = self.get_user_permissions(user_id)
        return permission in user_permissions


# Global authentication system instance
auth_system = AdvancedAuthSystem()


# Convenience functions
def create_user(username: str, email: str, password: str, roles: List[UserRole] = None) -> Dict[str, Any]:
    """Create a new user"""
    return auth_system.register_user(username, email, password, roles)


def authenticate(email: str, password: str) -> Dict[str, Any]:
    """Authenticate a user"""
    return auth_system.authenticate_user(email, password)


def create_api_key(user_id: str, name: str, permissions: List[str] = None) -> Dict[str, Any]:
    """Create an API key"""
    return auth_system.create_api_key(user_id, name, permissions)


def setup_mfa(user_id: str) -> Dict[str, Any]:
    """Setup MFA for a user"""
    return auth_system.setup_mfa(user_id)
