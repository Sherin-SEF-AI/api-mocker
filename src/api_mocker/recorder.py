import json
import time
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, asdict
from datetime import datetime
import re

@dataclass
class RecordedRequest:
    """Represents a recorded HTTP request."""
    timestamp: str
    method: str
    path: str
    headers: Dict[str, str]
    body: Optional[Any]
    response_status: int
    response_headers: Dict[str, str]
    response_body: Any
    session_id: Optional[str] = None

class RequestRecorder:
    """Records real API interactions for later replay as mocks."""
    
    def __init__(self):
        self.recorded_requests: List[RecordedRequest] = []
        self.filters: List[Callable] = []
        self.sensitive_patterns: List[str] = [
            r'password',
            r'token',
            r'key',
            r'secret',
            r'auth'
        ]
    
    def add_filter(self, filter_func: Callable):
        """Add a custom filter function."""
        self.filters.append(filter_func)
    
    def add_sensitive_pattern(self, pattern: str):
        """Add a regex pattern for sensitive data."""
        self.sensitive_patterns.append(pattern)
    
    def record_request(self, request: RecordedRequest) -> bool:
        """Record a request if it passes all filters."""
        if self._should_record(request):
            self._sanitize_request(request)
            self.recorded_requests.append(request)
            return True
        return False
    
    def _should_record(self, request: RecordedRequest) -> bool:
        """Check if request should be recorded based on filters."""
        for filter_func in self.filters:
            if not filter_func(request):
                return False
        return True
    
    def _sanitize_request(self, request: RecordedRequest):
        """Remove sensitive information from request."""
        # Sanitize headers
        sanitized_headers = {}
        for key, value in request.headers.items():
            if not self._is_sensitive(key):
                sanitized_headers[key] = value
            else:
                sanitized_headers[key] = "[REDACTED]"
        request.headers = sanitized_headers
        
        # Sanitize body if it's a string
        if isinstance(request.body, str):
            request.body = self._sanitize_string(request.body)
        elif isinstance(request.body, dict):
            request.body = self._sanitize_dict(request.body)
    
    def _is_sensitive(self, key: str) -> bool:
        """Check if a key contains sensitive information."""
        key_lower = key.lower()
        return any(re.search(pattern, key_lower) for pattern in self.sensitive_patterns)
    
    def _sanitize_string(self, text: str) -> str:
        """Sanitize sensitive data in a string."""
        for pattern in self.sensitive_patterns:
            text = re.sub(pattern, '[REDACTED]', text, flags=re.IGNORECASE)
        return text
    
    def _sanitize_dict(self, data: Dict) -> Dict:
        """Sanitize sensitive data in a dictionary."""
        sanitized = {}
        for key, value in data.items():
            if self._is_sensitive(key):
                sanitized[key] = '[REDACTED]'
            elif isinstance(value, dict):
                sanitized[key] = self._sanitize_dict(value)
            elif isinstance(value, str):
                sanitized[key] = self._sanitize_string(value)
            else:
                sanitized[key] = value
        return sanitized
    
    def export_recording(self, file_path: str, format: str = 'json'):
        """Export recorded requests to file."""
        data = {
            'recorded_at': datetime.now().isoformat(),
            'requests': [asdict(req) for req in self.recorded_requests]
        }
        
        with open(file_path, 'w') as f:
            if format.lower() == 'json':
                json.dump(data, f, indent=2)
            else:
                # Could add other formats like YAML, CSV, etc.
                json.dump(data, f, indent=2)
    
    def load_recording(self, file_path: str):
        """Load recorded requests from file."""
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        self.recorded_requests = [
            RecordedRequest(**req_data) for req_data in data.get('requests', [])
        ]
    
    def get_requests_by_path(self, path: str) -> List[RecordedRequest]:
        """Get all recorded requests for a specific path."""
        return [req for req in self.recorded_requests if req.path == path]
    
    def get_requests_by_method(self, method: str) -> List[RecordedRequest]:
        """Get all recorded requests for a specific HTTP method."""
        return [req for req in self.recorded_requests if req.method.upper() == method.upper()]

class ProxyRecorder:
    """Records requests by proxying them to real APIs."""
    
    def __init__(self, target_url: str):
        self.target_url = target_url
        self.recorder = RequestRecorder()
        self.session_requests: Dict[str, List[RecordedRequest]] = {}
    
    def start_proxy_session(self, session_id: str):
        """Start a new proxy recording session."""
        self.session_requests[session_id] = []
    
    def record_proxy_request(self, session_id: str, request: RecordedRequest):
        """Record a request during proxy session."""
        if session_id in self.session_requests:
            if self.recorder.record_request(request):
                self.session_requests[session_id].append(request)
    
    def end_proxy_session(self, session_id: str) -> List[RecordedRequest]:
        """End a proxy session and return recorded requests."""
        return self.session_requests.get(session_id, [])
    
    def get_session_summary(self, session_id: str) -> Dict[str, Any]:
        """Get summary statistics for a proxy session."""
        requests = self.session_requests.get(session_id, [])
        if not requests:
            return {}
        
        methods = {}
        paths = {}
        status_codes = {}
        
        for req in requests:
            methods[req.method] = methods.get(req.method, 0) + 1
            paths[req.path] = paths.get(req.path, 0) + 1
            status_codes[req.response_status] = status_codes.get(req.response_status, 0) + 1
        
        return {
            'total_requests': len(requests),
            'methods': methods,
            'paths': paths,
            'status_codes': status_codes,
            'duration': self._calculate_session_duration(requests)
        }
    
    def _calculate_session_duration(self, requests: List[RecordedRequest]) -> float:
        """Calculate the duration of a proxy session."""
        if len(requests) < 2:
            return 0.0
        
        start_time = datetime.fromisoformat(requests[0].timestamp)
        end_time = datetime.fromisoformat(requests[-1].timestamp)
        return (end_time - start_time).total_seconds()

class ReplayEngine:
    """Replays recorded requests as mock responses."""
    
    def __init__(self):
        self.recorded_responses: Dict[str, List[RecordedRequest]] = {}
        self.response_variations: Dict[str, List[Any]] = {}
    
    def load_recorded_requests(self, requests: List[RecordedRequest]):
        """Load recorded requests for replay."""
        for request in requests:
            key = f"{request.method}:{request.path}"
            if key not in self.recorded_responses:
                self.recorded_responses[key] = []
            self.recorded_responses[key].append(request)
    
    def get_response(self, method: str, path: str) -> Optional[Dict[str, Any]]:
        """Get a recorded response for the given method and path."""
        key = f"{method}:{path}"
        responses = self.recorded_responses.get(key, [])
        
        if not responses:
            return None
        
        # Return the most recent response by default
        response = responses[-1]
        
        return {
            'status_code': response.response_status,
            'headers': response.response_headers,
            'body': response.response_body
        }
    
    def get_response_variation(self, method: str, path: str) -> Optional[Dict[str, Any]]:
        """Get a random variation of recorded responses."""
        key = f"{method}:{path}"
        responses = self.recorded_responses.get(key, [])
        
        if not responses:
            return None
        
        # Return a random response
        import random
        response = random.choice(responses)
        
        return {
            'status_code': response.response_status,
            'headers': response.response_headers,
            'body': response.response_body
        }
    
    def generate_variations(self, method: str, path: str, count: int = 5):
        """Generate variations of recorded responses for more realistic testing."""
        key = f"{method}:{path}"
        responses = self.recorded_responses.get(key, [])
        
        if not responses:
            return
        
        variations = []
        for _ in range(count):
            # Create variations by modifying the response
            base_response = responses[0]
            variation = self._create_variation(base_response)
            variations.append(variation)
        
        self.response_variations[key] = variations
    
    def _create_variation(self, base_response: RecordedRequest) -> Dict[str, Any]:
        """Create a variation of a recorded response."""
        # This is a simple variation - could be made more sophisticated
        variation = {
            'status_code': base_response.response_status,
            'headers': base_response.response_headers.copy(),
            'body': base_response.response_body
        }
        
        # Add some random variation to the response
        if isinstance(variation['body'], dict):
            variation['body'] = variation['body'].copy()
            # Could add random variations here
        
        return variation 