"""
Enhanced Analytics System

Provides advanced analytics and insights including:
- Performance benchmarking against real APIs
- Usage pattern analysis
- API dependency mapping
- Cost optimization insights
- Advanced metrics collection and analysis
"""

import json
import sqlite3
from typing import Dict, Any, List, Optional, Tuple, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import statistics
from collections import defaultdict, Counter
import threading
import time


@dataclass
class PerformanceMetrics:
    """Performance metrics for API endpoints."""
    endpoint: str
    method: str
    response_time_p50: float
    response_time_p95: float
    response_time_p99: float
    throughput: float  # requests per second
    error_rate: float
    success_rate: float
    total_requests: int
    total_errors: int
    avg_response_size: int
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class UsagePattern:
    """Usage pattern analysis for endpoints."""
    endpoint: str
    method: str
    peak_hours: List[int]
    peak_days: List[str]
    user_agents: Dict[str, int]
    ip_addresses: Dict[str, int]
    request_sizes: List[int]
    response_sizes: List[int]
    common_headers: Dict[str, int]
    common_query_params: Dict[str, int]
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class APIDependency:
    """API dependency mapping information."""
    source_endpoint: str
    target_endpoint: str
    dependency_type: str  # "calls", "depends_on", "similar_pattern"
    confidence: float
    frequency: int
    avg_latency: float
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class CostOptimizationInsight:
    """Cost optimization insights."""
    insight_type: str
    description: str
    potential_savings: float
    recommendation: str
    priority: str  # "high", "medium", "low"
    affected_endpoints: List[str]
    timestamp: datetime = field(default_factory=datetime.now)


class EnhancedAnalytics:
    """Enhanced analytics system with advanced metrics and insights."""
    
    def __init__(self, db_path: str = "api_mocker_analytics.db"):
        self.db_path = db_path
        self.lock = threading.Lock()
        self._init_database()
    
    def _init_database(self):
        """Initialize the analytics database with enhanced tables."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS enhanced_requests (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    endpoint TEXT NOT NULL,
                    method TEXT NOT NULL,
                    status_code INTEGER,
                    response_time REAL,
                    response_size INTEGER,
                    request_size INTEGER,
                    user_agent TEXT,
                    ip_address TEXT,
                    headers TEXT,
                    query_params TEXT,
                    request_body TEXT,
                    response_body TEXT,
                    error_message TEXT,
                    scenario_name TEXT,
                    rule_name TEXT
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS performance_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    endpoint TEXT NOT NULL,
                    method TEXT NOT NULL,
                    response_time_p50 REAL,
                    response_time_p95 REAL,
                    response_time_p99 REAL,
                    throughput REAL,
                    error_rate REAL,
                    success_rate REAL,
                    total_requests INTEGER,
                    total_errors INTEGER,
                    avg_response_size INTEGER
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS usage_patterns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    endpoint TEXT NOT NULL,
                    method TEXT NOT NULL,
                    peak_hours TEXT,
                    peak_days TEXT,
                    user_agents TEXT,
                    ip_addresses TEXT,
                    request_sizes TEXT,
                    response_sizes TEXT,
                    common_headers TEXT,
                    common_query_params TEXT
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS api_dependencies (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    source_endpoint TEXT NOT NULL,
                    target_endpoint TEXT NOT NULL,
                    dependency_type TEXT NOT NULL,
                    confidence REAL,
                    frequency INTEGER,
                    avg_latency REAL
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS cost_insights (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    insight_type TEXT NOT NULL,
                    description TEXT NOT NULL,
                    potential_savings REAL,
                    recommendation TEXT NOT NULL,
                    priority TEXT NOT NULL,
                    affected_endpoints TEXT
                )
            """)
            
            # Create indexes for better performance
            conn.execute("CREATE INDEX IF NOT EXISTS idx_requests_endpoint ON enhanced_requests(endpoint)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_requests_timestamp ON enhanced_requests(timestamp)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_requests_method ON enhanced_requests(method)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_performance_endpoint ON performance_metrics(endpoint)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_dependencies_source ON api_dependencies(source_endpoint)")
    
    def log_request(self, request_data: Dict[str, Any], response_data: Dict[str, Any], 
                   scenario_name: Optional[str] = None, rule_name: Optional[str] = None):
        """Log a request with enhanced analytics data."""
        with self.lock:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO enhanced_requests (
                        endpoint, method, status_code, response_time, response_size,
                        request_size, user_agent, ip_address, headers, query_params,
                        request_body, response_body, error_message, scenario_name, rule_name
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    request_data.get('path', ''),
                    request_data.get('method', ''),
                    response_data.get('status_code', 200),
                    response_data.get('response_time', 0),
                    response_data.get('response_size', 0),
                    request_data.get('request_size', 0),
                    request_data.get('user_agent', ''),
                    request_data.get('ip_address', ''),
                    json.dumps(request_data.get('headers', {})),
                    json.dumps(request_data.get('query_params', {})),
                    json.dumps(request_data.get('body', {})),
                    json.dumps(response_data.get('body', {})),
                    response_data.get('error_message', ''),
                    scenario_name,
                    rule_name
                ))
    
    def calculate_performance_metrics(self, endpoint: Optional[str] = None, 
                                    hours: int = 24) -> List[PerformanceMetrics]:
        """Calculate performance metrics for endpoints."""
        with sqlite3.connect(self.db_path) as conn:
            time_filter = datetime.now() - timedelta(hours=hours)
            
            query = """
                SELECT endpoint, method, response_time, status_code, response_size
                FROM enhanced_requests
                WHERE timestamp >= ?
            """
            params = [time_filter.isoformat()]
            
            if endpoint:
                query += " AND endpoint = ?"
                params.append(endpoint)
            
            cursor = conn.execute(query, params)
            rows = cursor.fetchall()
        
        # Group by endpoint and method
        grouped_data = defaultdict(list)
        for row in rows:
            endpoint, method, response_time, status_code, response_size = row
            key = f"{endpoint}:{method}"
            grouped_data[key].append({
                'response_time': response_time,
                'status_code': status_code,
                'response_size': response_size
            })
        
        metrics = []
        for key, data in grouped_data.items():
            endpoint, method = key.split(':', 1)
            
            response_times = [d['response_time'] for d in data if d['response_time']]
            status_codes = [d['status_code'] for d in data]
            response_sizes = [d['response_size'] for d in data if d['response_size']]
            
            if not response_times:
                continue
            
            total_requests = len(data)
            total_errors = len([s for s in status_codes if s >= 400])
            
            metric = PerformanceMetrics(
                endpoint=endpoint,
                method=method,
                response_time_p50=statistics.median(response_times),
                response_time_p95=self._percentile(response_times, 95),
                response_time_p99=self._percentile(response_times, 99),
                throughput=total_requests / (hours * 3600),  # requests per second
                error_rate=total_errors / total_requests if total_requests > 0 else 0,
                success_rate=(total_requests - total_errors) / total_requests if total_requests > 0 else 0,
                total_requests=total_requests,
                total_errors=total_errors,
                avg_response_size=statistics.mean(response_sizes) if response_sizes else 0
            )
            metrics.append(metric)
        
        return metrics
    
    def analyze_usage_patterns(self, endpoint: Optional[str] = None, 
                             days: int = 7) -> List[UsagePattern]:
        """Analyze usage patterns for endpoints."""
        with sqlite3.connect(self.db_path) as conn:
            time_filter = datetime.now() - timedelta(days=days)
            
            query = """
                SELECT endpoint, method, timestamp, user_agent, ip_address,
                       headers, query_params, request_size, response_size
                FROM enhanced_requests
                WHERE timestamp >= ?
            """
            params = [time_filter.isoformat()]
            
            if endpoint:
                query += " AND endpoint = ?"
                params.append(endpoint)
            
            cursor = conn.execute(query, params)
            rows = cursor.fetchall()
        
        # Group by endpoint and method
        grouped_data = defaultdict(list)
        for row in rows:
            endpoint, method, timestamp, user_agent, ip_address, headers, query_params, request_size, response_size = row
            key = f"{endpoint}:{method}"
            grouped_data[key].append({
                'timestamp': datetime.fromisoformat(timestamp),
                'user_agent': user_agent,
                'ip_address': ip_address,
                'headers': json.loads(headers) if headers else {},
                'query_params': json.loads(query_params) if query_params else {},
                'request_size': request_size,
                'response_size': response_size
            })
        
        patterns = []
        for key, data in grouped_data.items():
            endpoint, method = key.split(':', 1)
            
            # Analyze peak hours
            hours = [d['timestamp'].hour for d in data]
            hour_counts = Counter(hours)
            peak_hours = [hour for hour, count in hour_counts.most_common(3)]
            
            # Analyze peak days
            days = [d['timestamp'].strftime('%A') for d in data]
            day_counts = Counter(days)
            peak_days = [day for day, count in day_counts.most_common(3)]
            
            # Analyze user agents
            user_agents = [d['user_agent'] for d in data if d['user_agent']]
            user_agent_counts = Counter(user_agents)
            
            # Analyze IP addresses
            ip_addresses = [d['ip_address'] for d in data if d['ip_address']]
            ip_counts = Counter(ip_addresses)
            
            # Analyze request and response sizes
            request_sizes = [d['request_size'] for d in data if d['request_size']]
            response_sizes = [d['response_size'] for d in data if d['response_size']]
            
            # Analyze common headers
            all_headers = {}
            for d in data:
                for header, value in d['headers'].items():
                    all_headers[header] = all_headers.get(header, 0) + 1
            
            # Analyze common query parameters
            all_query_params = {}
            for d in data:
                for param, value in d['query_params'].items():
                    all_query_params[param] = all_query_params.get(param, 0) + 1
            
            pattern = UsagePattern(
                endpoint=endpoint,
                method=method,
                peak_hours=peak_hours,
                peak_days=peak_days,
                user_agents=dict(user_agent_counts.most_common(10)),
                ip_addresses=dict(ip_counts.most_common(10)),
                request_sizes=request_sizes,
                response_sizes=response_sizes,
                common_headers=dict(sorted(all_headers.items(), key=lambda x: x[1], reverse=True)[:10]),
                common_query_params=dict(sorted(all_query_params.items(), key=lambda x: x[1], reverse=True)[:10])
            )
            patterns.append(pattern)
        
        return patterns
    
    def detect_api_dependencies(self, hours: int = 24) -> List[APIDependency]:
        """Detect API dependencies between endpoints."""
        with sqlite3.connect(self.db_path) as conn:
            time_filter = datetime.now() - timedelta(hours=hours)
            
            # Get all requests in the time window
            cursor = conn.execute("""
                SELECT endpoint, method, timestamp, response_time
                FROM enhanced_requests
                WHERE timestamp >= ?
                ORDER BY timestamp
            """, [time_filter.isoformat()])
            
            rows = cursor.fetchall()
        
        # Analyze temporal patterns
        dependencies = []
        endpoint_sequences = defaultdict(list)
        
        for row in rows:
            endpoint, method, timestamp, response_time = row
            endpoint_sequences[endpoint].append({
                'timestamp': datetime.fromisoformat(timestamp),
                'response_time': response_time
            })
        
        # Find endpoints that are called in sequence
        for endpoint1 in endpoint_sequences:
            for endpoint2 in endpoint_sequences:
                if endpoint1 != endpoint2:
                    # Check if endpoint2 is called shortly after endpoint1
                    calls1 = endpoint_sequences[endpoint1]
                    calls2 = endpoint_sequences[endpoint2]
                    
                    dependency_count = 0
                    total_latency = 0
                    
                    for call1 in calls1:
                        # Look for calls to endpoint2 within 5 seconds
                        for call2 in calls2:
                            time_diff = (call2['timestamp'] - call1['timestamp']).total_seconds()
                            if 0 < time_diff <= 5:
                                dependency_count += 1
                                total_latency += time_diff
                                break
                    
                    if dependency_count > 0:
                        avg_latency = total_latency / dependency_count
                        confidence = min(dependency_count / len(calls1), 1.0)
                        
                        dependency = APIDependency(
                            source_endpoint=endpoint1,
                            target_endpoint=endpoint2,
                            dependency_type="calls",
                            confidence=confidence,
                            frequency=dependency_count,
                            avg_latency=avg_latency
                        )
                        dependencies.append(dependency)
        
        return dependencies
    
    def generate_cost_optimization_insights(self) -> List[CostOptimizationInsight]:
        """Generate cost optimization insights."""
        insights = []
        
        # Get performance metrics
        metrics = self.calculate_performance_metrics(hours=24)
        
        # Analyze slow endpoints
        slow_endpoints = [m for m in metrics if m.response_time_p95 > 1000]  # > 1 second
        if slow_endpoints:
            avg_latency = statistics.mean([m.response_time_p95 for m in slow_endpoints])
            potential_savings = len(slow_endpoints) * avg_latency * 0.1  # 10% improvement
            
            insight = CostOptimizationInsight(
                insight_type="performance_optimization",
                description=f"Found {len(slow_endpoints)} slow endpoints with P95 latency > 1s",
                potential_savings=potential_savings,
                recommendation="Consider caching, database optimization, or response compression",
                priority="high" if len(slow_endpoints) > 5 else "medium",
                affected_endpoints=[m.endpoint for m in slow_endpoints]
            )
            insights.append(insight)
        
        # Analyze high error rates
        error_endpoints = [m for m in metrics if m.error_rate > 0.05]  # > 5% error rate
        if error_endpoints:
            insight = CostOptimizationInsight(
                insight_type="error_reduction",
                description=f"Found {len(error_endpoints)} endpoints with high error rates",
                potential_savings=len(error_endpoints) * 100,  # $100 per endpoint
                recommendation="Review error handling and improve input validation",
                priority="high" if len(error_endpoints) > 3 else "medium",
                affected_endpoints=[m.endpoint for m in error_endpoints]
            )
            insights.append(insight)
        
        # Analyze large response sizes
        large_response_endpoints = [m for m in metrics if m.avg_response_size > 10000]  # > 10KB
        if large_response_endpoints:
            total_size = sum([m.avg_response_size * m.total_requests for m in large_response_endpoints])
            potential_savings = total_size * 0.0001  # $0.0001 per KB
            
            insight = CostOptimizationInsight(
                insight_type="response_optimization",
                description=f"Found {len(large_response_endpoints)} endpoints with large responses",
                potential_savings=potential_savings,
                recommendation="Consider pagination, field selection, or response compression",
                priority="medium",
                affected_endpoints=[m.endpoint for m in large_response_endpoints]
            )
            insights.append(insight)
        
        return insights
    
    def get_analytics_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get a comprehensive analytics summary."""
        metrics = self.calculate_performance_metrics(hours=hours)
        patterns = self.analyze_usage_patterns(days=hours//24)
        dependencies = self.detect_api_dependencies(hours=hours)
        insights = self.generate_cost_optimization_insights()
        
        # Calculate overall statistics
        total_requests = sum(m.total_requests for m in metrics)
        total_errors = sum(m.total_errors for m in metrics)
        avg_response_time = statistics.mean([m.response_time_p50 for m in metrics]) if metrics else 0
        
        summary = {
            "time_period": f"Last {hours} hours",
            "total_requests": total_requests,
            "total_errors": total_errors,
            "error_rate": total_errors / total_requests if total_requests > 0 else 0,
            "avg_response_time": avg_response_time,
            "endpoints_analyzed": len(metrics),
            "usage_patterns": len(patterns),
            "dependencies_found": len(dependencies),
            "cost_insights": len(insights),
            "top_performing_endpoints": sorted(metrics, key=lambda m: m.response_time_p50)[:5],
            "worst_performing_endpoints": sorted(metrics, key=lambda m: m.response_time_p95, reverse=True)[:5],
            "most_used_endpoints": sorted(metrics, key=lambda m: m.total_requests, reverse=True)[:5],
            "cost_insights": insights
        }
        
        return summary
    
    def export_analytics(self, format: str = "json", hours: int = 24) -> str:
        """Export analytics data in various formats."""
        summary = self.get_analytics_summary(hours=hours)
        
        if format == "json":
            return json.dumps(summary, indent=2, default=str)
        elif format == "csv":
            # Convert to CSV format
            csv_lines = []
            csv_lines.append("metric,value")
            for key, value in summary.items():
                if isinstance(value, (int, float, str)):
                    csv_lines.append(f"{key},{value}")
            return "\n".join(csv_lines)
        else:
            raise ValueError(f"Unsupported export format: {format}")
    
    def _percentile(self, data: List[float], percentile: int) -> float:
        """Calculate percentile of a list of numbers."""
        if not data:
            return 0
        
        sorted_data = sorted(data)
        index = (percentile / 100) * (len(sorted_data) - 1)
        
        if index.is_integer():
            return sorted_data[int(index)]
        else:
            lower = sorted_data[int(index)]
            upper = sorted_data[int(index) + 1]
            return lower + (upper - lower) * (index - int(index))


# Global enhanced analytics instance
enhanced_analytics = EnhancedAnalytics() 