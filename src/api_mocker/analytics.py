"""
Analytics and metrics tracking for api-mocker.
"""

import json
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any
import sqlite3
import threading
from dataclasses import dataclass, asdict
import hashlib
import platform
import psutil
import requests
from contextlib import contextmanager

@dataclass
class RequestMetrics:
    """Metrics for a single request."""
    request_id: str
    timestamp: float
    method: str
    path: str
    status_code: int
    response_time_ms: float
    request_size_bytes: int
    response_size_bytes: int
    user_agent: str
    ip_address: str
    path_params: Dict[str, str]
    query_params: Dict[str, str]

@dataclass
class ServerMetrics:
    """Overall server metrics."""
    server_id: str
    start_time: float
    uptime_seconds: float
    total_requests: int
    requests_per_minute: float
    average_response_time_ms: float
    error_rate: float
    memory_usage_mb: float
    cpu_usage_percent: float
    active_connections: int

@dataclass
class UserSession:
    """User session tracking."""
    session_id: str
    start_time: float
    last_activity: float
    total_requests: int
    unique_endpoints: int
    user_agent: str
    ip_address: str

class AnalyticsManager:
    """Manages analytics and metrics collection."""
    
    def __init__(self, db_path: str = "api_mocker_analytics.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self.server_id = str(uuid.uuid4())
        self.start_time = time.time()
        self._init_database()
        
    def _init_database(self):
        """Initialize the analytics database."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS request_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    request_id TEXT NOT NULL,
                    timestamp REAL NOT NULL,
                    method TEXT NOT NULL,
                    path TEXT NOT NULL,
                    status_code INTEGER NOT NULL,
                    response_time_ms REAL NOT NULL,
                    request_size_bytes INTEGER NOT NULL,
                    response_size_bytes INTEGER NOT NULL,
                    user_agent TEXT,
                    ip_address TEXT,
                    path_params TEXT,
                    query_params TEXT,
                    server_id TEXT NOT NULL
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS server_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    server_id TEXT NOT NULL,
                    timestamp REAL NOT NULL,
                    uptime_seconds REAL NOT NULL,
                    total_requests INTEGER NOT NULL,
                    requests_per_minute REAL NOT NULL,
                    average_response_time_ms REAL NOT NULL,
                    error_rate REAL NOT NULL,
                    memory_usage_mb REAL NOT NULL,
                    cpu_usage_percent REAL NOT NULL,
                    active_connections INTEGER NOT NULL
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS user_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    start_time REAL NOT NULL,
                    last_activity REAL NOT NULL,
                    total_requests INTEGER NOT NULL,
                    unique_endpoints INTEGER NOT NULL,
                    user_agent TEXT,
                    ip_address TEXT,
                    server_id TEXT NOT NULL
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS feature_usage (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    feature_name TEXT NOT NULL,
                    usage_count INTEGER NOT NULL,
                    last_used REAL NOT NULL,
                    server_id TEXT NOT NULL
                )
            """)
            
            # Create indexes for better performance
            conn.execute("CREATE INDEX IF NOT EXISTS idx_request_timestamp ON request_metrics(timestamp)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_request_path ON request_metrics(path)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_server_metrics_timestamp ON server_metrics(timestamp)")
            
    def track_request(self, metrics: RequestMetrics):
        """Track a single request."""
        with self._lock:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO request_metrics 
                    (request_id, timestamp, method, path, status_code, response_time_ms,
                     request_size_bytes, response_size_bytes, user_agent, ip_address,
                     path_params, query_params, server_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    metrics.request_id, metrics.timestamp, metrics.method, metrics.path,
                    metrics.status_code, metrics.response_time_ms, metrics.request_size_bytes,
                    metrics.response_size_bytes, metrics.user_agent, metrics.ip_address,
                    json.dumps(metrics.path_params), json.dumps(metrics.query_params),
                    self.server_id
                ))
                
    def get_server_metrics(self) -> ServerMetrics:
        """Get current server metrics."""
        with sqlite3.connect(self.db_path) as conn:
            # Get total requests
            total_requests = conn.execute(
                "SELECT COUNT(*) FROM request_metrics WHERE server_id = ?", 
                (self.server_id,)
            ).fetchone()[0]
            
            # Get requests in last minute
            one_minute_ago = time.time() - 60
            recent_requests = conn.execute(
                "SELECT COUNT(*) FROM request_metrics WHERE server_id = ? AND timestamp > ?",
                (self.server_id, one_minute_ago)
            ).fetchone()[0]
            
            # Get average response time
            avg_response_time = conn.execute(
                "SELECT AVG(response_time_ms) FROM request_metrics WHERE server_id = ?",
                (self.server_id,)
            ).fetchone()[0] or 0
            
            # Get error rate
            total_errors = conn.execute(
                "SELECT COUNT(*) FROM request_metrics WHERE server_id = ? AND status_code >= 400",
                (self.server_id,)
            ).fetchone()[0]
            error_rate = (total_errors / total_requests * 100) if total_requests > 0 else 0
            
            # System metrics
            memory_usage = psutil.virtual_memory().percent
            cpu_usage = psutil.cpu_percent()
            
            return ServerMetrics(
                server_id=self.server_id,
                start_time=self.start_time,
                uptime_seconds=time.time() - self.start_time,
                total_requests=total_requests,
                requests_per_minute=recent_requests,
                average_response_time_ms=avg_response_time,
                error_rate=error_rate,
                memory_usage_mb=memory_usage,
                cpu_usage_percent=cpu_usage,
                active_connections=0  # TODO: Implement connection tracking
            )
            
    def track_feature_usage(self, feature_name: str):
        """Track feature usage."""
        with self._lock:
            with sqlite3.connect(self.db_path) as conn:
                # Check if feature exists
                existing = conn.execute(
                    "SELECT usage_count FROM feature_usage WHERE feature_name = ? AND server_id = ?",
                    (feature_name, self.server_id)
                ).fetchone()
                
                if existing:
                    conn.execute("""
                        UPDATE feature_usage 
                        SET usage_count = usage_count + 1, last_used = ?
                        WHERE feature_name = ? AND server_id = ?
                    """, (time.time(), feature_name, self.server_id))
                else:
                    conn.execute("""
                        INSERT INTO feature_usage (feature_name, usage_count, last_used, server_id)
                        VALUES (?, 1, ?, ?)
                    """, (feature_name, time.time(), self.server_id))
                    
    def get_analytics_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get analytics summary for the specified time period."""
        since = time.time() - (hours * 3600)
        
        with sqlite3.connect(self.db_path) as conn:
            # Request statistics
            total_requests = conn.execute(
                "SELECT COUNT(*) FROM request_metrics WHERE server_id = ? AND timestamp > ?",
                (self.server_id, since)
            ).fetchone()[0]
            
            # Method distribution
            methods = conn.execute("""
                SELECT method, COUNT(*) as count 
                FROM request_metrics 
                WHERE server_id = ? AND timestamp > ?
                GROUP BY method
            """, (self.server_id, since)).fetchall()
            
            # Status code distribution
            status_codes = conn.execute("""
                SELECT status_code, COUNT(*) as count 
                FROM request_metrics 
                WHERE server_id = ? AND timestamp > ?
                GROUP BY status_code
            """, (self.server_id, since)).fetchall()
            
            # Most popular endpoints
            popular_endpoints = conn.execute("""
                SELECT path, COUNT(*) as count 
                FROM request_metrics 
                WHERE server_id = ? AND timestamp > ?
                GROUP BY path 
                ORDER BY count DESC 
                LIMIT 10
            """, (self.server_id, since)).fetchall()
            
            # Average response times by endpoint
            response_times = conn.execute("""
                SELECT path, AVG(response_time_ms) as avg_time 
                FROM request_metrics 
                WHERE server_id = ? AND timestamp > ?
                GROUP BY path 
                ORDER BY avg_time DESC 
                LIMIT 10
            """, (self.server_id, since)).fetchall()
            
            # Feature usage
            feature_usage = conn.execute("""
                SELECT feature_name, usage_count 
                FROM feature_usage 
                WHERE server_id = ?
                ORDER BY usage_count DESC
            """, (self.server_id,)).fetchall()
            
            return {
                "period_hours": hours,
                "total_requests": total_requests,
                "methods": dict(methods),
                "status_codes": dict(status_codes),
                "popular_endpoints": dict(popular_endpoints),
                "slowest_endpoints": dict(response_times),
                "feature_usage": dict(feature_usage),
                "server_metrics": asdict(self.get_server_metrics())
            }
            
    def export_analytics(self, output_path: str, format: str = "json"):
        """Export analytics data."""
        summary = self.get_analytics_summary()
        
        if format.lower() == "json":
            with open(output_path, 'w') as f:
                json.dump(summary, f, indent=2)
        elif format.lower() == "csv":
            # TODO: Implement CSV export
            pass
            
    def cleanup_old_data(self, days: int = 30):
        """Clean up old analytics data."""
        cutoff = time.time() - (days * 24 * 3600)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "DELETE FROM request_metrics WHERE timestamp < ?",
                (cutoff,)
            )
            conn.execute(
                "DELETE FROM server_metrics WHERE timestamp < ?",
                (cutoff,)
            )
            conn.execute(
                "DELETE FROM user_sessions WHERE last_activity < ?",
                (cutoff,)
            )

class AnalyticsMiddleware:
    """FastAPI middleware for automatic analytics tracking."""
    
    def __init__(self, analytics_manager: AnalyticsManager):
        self.analytics = analytics_manager
        
    async def __call__(self, request, call_next):
        start_time = time.time()
        
        # Track feature usage
        self.analytics.track_feature_usage("http_request")
        
        # Process request
        response = await call_next(request)
        
        # Calculate metrics
        end_time = time.time()
        response_time_ms = (end_time - start_time) * 1000
        
        # Get request size (approximate)
        request_size = len(str(request.headers)) + len(str(request.query_params))
        if hasattr(request, 'body'):
            request_size += len(str(request.body))
            
        # Get response size (approximate)
        response_size = len(str(response.headers))
        if hasattr(response, 'body'):
            response_size += len(str(response.body))
            
        # Create metrics
        metrics = RequestMetrics(
            request_id=str(uuid.uuid4()),
            timestamp=start_time,
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            response_time_ms=response_time_ms,
            request_size_bytes=request_size,
            response_size_bytes=response_size,
            user_agent=request.headers.get("user-agent", ""),
            ip_address=request.client.host if request.client else "",
            path_params=dict(request.path_params),
            query_params=dict(request.query_params)
        )
        
        # Track the request
        self.analytics.track_request(metrics)
        
        return response 