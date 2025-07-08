"""
Advanced features for api-mocker including rate limiting, authentication, caching, and more.
"""

import time
import hashlib
import asyncio
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from fastapi import HTTPException, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import json
import logging

# Optional imports for advanced features
try:
    import jwt
except ImportError:
    jwt = None

try:
    import redis
except ImportError:
    redis = None

logger = logging.getLogger(__name__)

@dataclass
class RateLimitConfig:
    """Rate limiting configuration."""
    requests_per_minute: int = 60
    requests_per_hour: int = 1000
    burst_size: int = 10
    window_size: int = 60  # seconds

@dataclass
class CacheConfig:
    """Caching configuration."""
    enabled: bool = True
    ttl_seconds: int = 300
    max_size: int = 1000
    strategy: str = "lru"  # lru, fifo, random

@dataclass
class AuthConfig:
    """Authentication configuration."""
    enabled: bool = False
    secret_key: str = "your-secret-key"
    algorithm: str = "HS256"
    token_expiry_hours: int = 24
    require_auth: List[str] = field(default_factory=list)  # List of paths that require auth

class RateLimiter:
    """Rate limiting implementation using sliding window."""
    
    def __init__(self, config: RateLimitConfig):
        self.config = config
        self.requests = {}  # client_id -> list of timestamps
        
    def is_allowed(self, client_id: str) -> bool:
        """Check if request is allowed based on rate limits."""
        now = time.time()
        
        if client_id not in self.requests:
            self.requests[client_id] = []
            
        # Remove old requests outside the window
        window_start = now - self.config.window_size
        self.requests[client_id] = [
            req_time for req_time in self.requests[client_id] 
            if req_time > window_start
        ]
        
        # Check if we're within limits
        if len(self.requests[client_id]) >= self.config.requests_per_minute:
            return False
            
        # Add current request
        self.requests[client_id].append(now)
        return True
        
    def get_remaining_requests(self, client_id: str) -> int:
        """Get remaining requests for a client."""
        now = time.time()
        window_start = now - self.config.window_size
        
        if client_id not in self.requests:
            return self.config.requests_per_minute
            
        recent_requests = len([
            req_time for req_time in self.requests[client_id] 
            if req_time > window_start
        ])
        
        return max(0, self.config.requests_per_minute - recent_requests)

class CacheManager:
    """Simple in-memory cache with TTL support."""
    
    def __init__(self, config: CacheConfig):
        self.config = config
        self.cache = {}
        self.access_times = {}
        self.max_size = config.max_size
        
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        if not self.config.enabled:
            return None
            
        if key not in self.cache:
            return None
            
        # Check TTL
        if time.time() - self.access_times[key] > self.config.ttl_seconds:
            self.delete(key)
            return None
            
        # Update access time
        self.access_times[key] = time.time()
        return self.cache[key]
        
    def set(self, key: str, value: Any) -> None:
        """Set value in cache."""
        if not self.config.enabled:
            return
            
        # Evict if cache is full
        if len(self.cache) >= self.max_size:
            self._evict_oldest()
            
        self.cache[key] = value
        self.access_times[key] = time.time()
        
    def delete(self, key: str) -> None:
        """Delete key from cache."""
        self.cache.pop(key, None)
        self.access_times.pop(key, None)
        
    def clear(self) -> None:
        """Clear all cache."""
        self.cache.clear()
        self.access_times.clear()
        
    def _evict_oldest(self) -> None:
        """Evict oldest entry based on strategy."""
        if not self.access_times:
            return
            
        if self.config.strategy == "lru":
            oldest_key = min(self.access_times.keys(), key=lambda k: self.access_times[k])
        elif self.config.strategy == "fifo":
            oldest_key = min(self.access_times.keys(), key=lambda k: self.access_times[k])
        else:  # random
            import random
            oldest_key = random.choice(list(self.access_times.keys()))
            
        self.delete(oldest_key)

class AuthManager:
    """JWT-based authentication manager."""
    
    def __init__(self, config: AuthConfig):
        self.config = config
        self.security = HTTPBearer()
        
    def create_token(self, user_id: str, roles: Optional[List[str]] = None) -> str:
        """Create JWT token for user."""
        if jwt is None:
            raise HTTPException(status_code=500, detail="JWT library not available")
            
        payload = {
            "user_id": user_id,
            "roles": roles or [],
            "exp": datetime.utcnow() + timedelta(hours=self.config.token_expiry_hours),
            "iat": datetime.utcnow()
        }
        return jwt.encode(payload, self.config.secret_key, algorithm=self.config.algorithm)
        
    def verify_token(self, token: str) -> Dict[str, Any]:
        """Verify JWT token and return payload."""
        if jwt is None:
            raise HTTPException(status_code=500, detail="JWT library not available")
            
        try:
            payload = jwt.decode(token, self.config.secret_key, algorithms=[self.config.algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token has expired")
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=401, detail="Invalid token")
            
    async def get_current_user(self, credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer())):
        """Dependency to get current user from token."""
        if not self.config.enabled:
            return None
            
        token = credentials.credentials
        payload = self.verify_token(token)
        return payload

class AdvancedFeatures:
    """Main class for advanced features."""
    
    def __init__(self, 
                 rate_limit_config: Optional[RateLimitConfig] = None,
                 cache_config: Optional[CacheConfig] = None,
                 auth_config: Optional[AuthConfig] = None):
        
        self.rate_limiter = RateLimiter(rate_limit_config or RateLimitConfig())
        self.cache_manager = CacheManager(cache_config or CacheConfig())
        self.auth_manager = AuthManager(auth_config or AuthConfig())
        
    def get_client_id(self, request: Request) -> str:
        """Get client identifier for rate limiting."""
        # Try to get from X-Forwarded-For header first
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
            
        # Fall back to client host
        return request.client.host if request.client else "unknown"
        
    def create_cache_key(self, method: str, path: str, query_params: str = "") -> str:
        """Create cache key for request."""
        key_data = f"{method}:{path}:{query_params}"
        return hashlib.md5(key_data.encode()).hexdigest()
        
    async def rate_limit_middleware(self, request: Request, call_next):
        """Rate limiting middleware."""
        client_id = self.get_client_id(request)
        
        if not self.rate_limiter.is_allowed(client_id):
            remaining = self.rate_limiter.get_remaining_requests(client_id)
            raise HTTPException(
                status_code=429, 
                detail=f"Rate limit exceeded. Try again in {60 - int(time.time() % 60)} seconds.",
                headers={"X-RateLimit-Remaining": str(remaining)}
            )
            
        response = await call_next(request)
        
        # Add rate limit headers
        remaining = self.rate_limiter.get_remaining_requests(client_id)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Limit"] = str(self.rate_limiter.config.requests_per_minute)
        
        return response
        
    async def cache_middleware(self, request: Request, call_next):
        """Caching middleware."""
        if request.method != "GET":
            return await call_next(request)
            
        cache_key = self.create_cache_key(
            request.method, 
            request.url.path, 
            str(request.query_params)
        )
        
        # Try to get from cache
        cached_response = self.cache_manager.get(cache_key)
        if cached_response:
            return cached_response
            
        # Process request
        response = await call_next(request)
        
        # Cache successful responses
        if response.status_code == 200:
            self.cache_manager.set(cache_key, response)
            
        return response
        
    async def auth_middleware(self, request: Request, call_next):
        """Authentication middleware."""
        if not self.auth_manager.config.enabled:
            return await call_next(request)
            
        # Check if path requires authentication
        if self.auth_manager.config.require_auth:
            path_requires_auth = any(
                request.url.path.startswith(auth_path) 
                for auth_path in self.auth_manager.config.require_auth
            )
            if path_requires_auth:
                # Verify token
                auth_header = request.headers.get("Authorization")
                if not auth_header or not auth_header.startswith("Bearer "):
                    raise HTTPException(status_code=401, detail="Authentication required")
                    
                token = auth_header.split(" ")[1]
                try:
                    payload = self.auth_manager.verify_token(token)
                    request.state.user = payload
                except HTTPException:
                    raise HTTPException(status_code=401, detail="Invalid token")
                    
        return await call_next(request)

class MetricsCollector:
    """Advanced metrics collection."""
    
    def __init__(self):
        self.metrics = {
            "rate_limit_hits": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "auth_failures": 0,
            "slow_queries": 0,
            "error_counts": {}
        }
        
    def increment(self, metric: str, value: int = 1):
        """Increment a metric."""
        if metric in self.metrics:
            if isinstance(self.metrics[metric], dict):
                self.metrics[metric][str(value)] = self.metrics[metric].get(str(value), 0) + 1
            else:
                self.metrics[metric] += value
                
    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics."""
        return self.metrics.copy()
        
    def reset_metrics(self):
        """Reset all metrics."""
        self.metrics = {
            "rate_limit_hits": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "auth_failures": 0,
            "slow_queries": 0,
            "error_counts": {}
        }

class HealthChecker:
    """Health check and monitoring."""
    
    def __init__(self):
        self.checks = {}
        
    def add_check(self, name: str, check_func: Callable[[], bool]):
        """Add a health check."""
        self.checks[name] = check_func
        
    def run_checks(self) -> Dict[str, bool]:
        """Run all health checks."""
        results = {}
        for name, check_func in self.checks.items():
            try:
                results[name] = check_func()
            except Exception as e:
                logger.error(f"Health check {name} failed: {e}")
                results[name] = False
        return results
        
    def get_health_status(self) -> Dict[str, Any]:
        """Get overall health status."""
        results = self.run_checks()
        overall_healthy = all(results.values())
        
        return {
            "status": "healthy" if overall_healthy else "unhealthy",
            "checks": results,
            "timestamp": datetime.utcnow().isoformat()
        }

# Predefined health checks
def check_database_connection():
    """Check database connectivity."""
    try:
        import sqlite3
        conn = sqlite3.connect(":memory:")
        conn.close()
        return True
    except:
        return False
        
def check_memory_usage():
    """Check if memory usage is acceptable."""
    import psutil
    memory_percent = psutil.virtual_memory().percent
    return memory_percent < 90  # Consider healthy if < 90%
    
def check_disk_space():
    """Check if disk space is sufficient."""
    import psutil
    disk_percent = psutil.disk_usage('/').percent
    return disk_percent < 95  # Consider healthy if < 95% 