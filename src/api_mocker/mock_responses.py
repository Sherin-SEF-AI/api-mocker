"""
Mock API Response Management System

This module provides comprehensive functionality for creating and managing mock API responses
with support for pytest integration, automated testing, and efficient response management.
"""

import json
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union, Callable
from enum import Enum
import pytest
from pathlib import Path
import yaml


class ResponseType(Enum):
    """Types of mock responses"""
    STATIC = "static"
    DYNAMIC = "dynamic"
    TEMPLATED = "templated"
    CONDITIONAL = "conditional"
    DELAYED = "delayed"
    ERROR = "error"


class HTTPMethod(Enum):
    """HTTP methods supported by mock responses"""
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"
    HEAD = "HEAD"
    OPTIONS = "OPTIONS"


@dataclass
class MockAPIResponse:
    """
    Core class for creating and managing mock API responses.
    
    This class provides comprehensive functionality for defining mock responses
    with support for static data, dynamic generation, templating, and conditional logic.
    """
    
    # Basic response properties
    path: str
    method: HTTPMethod = HTTPMethod.GET
    status_code: int = 200
    headers: Dict[str, str] = field(default_factory=dict)
    body: Any = None
    
    # Response type and behavior
    response_type: ResponseType = ResponseType.STATIC
    delay_ms: int = 0
    error_probability: float = 0.0
    
    # Conditional logic
    conditions: List[Dict[str, Any]] = field(default_factory=list)
    priority: int = 0
    
    # Dynamic response properties
    template_vars: Dict[str, Any] = field(default_factory=dict)
    generator_func: Optional[Callable] = None
    cache_ttl: int = 300  # 5 minutes default
    
    # Metadata
    name: Optional[str] = None
    description: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    
    def __post_init__(self):
        """Initialize response after creation"""
        if self.name is None:
            # Clean up path for name generation - remove leading slash and replace with single underscore
            clean_path = self.path.lstrip('/').replace('/', '_').replace('{', '').replace('}', '')
            self.name = f"{self.method.value}_{clean_path}"
        
        # Set default headers if not provided
        if not self.headers:
            self.headers = {
                "Content-Type": "application/json",
                "X-Mock-Response": "true"
            }
    
    def matches_request(self, request_path: str, request_method: str, 
                       request_headers: Dict[str, str] = None,
                       **kwargs) -> bool:
        """
        Check if this response matches the given request.
        
        Args:
            request_path: The request path
            request_method: The HTTP method
            request_headers: Request headers
            request_body: Request body
            
        Returns:
            bool: True if response matches request
        """
        # Basic path and method matching
        if not self._path_matches(request_path) or self.method.value != request_method:
            return False
        
        # Check conditions if any
        if self.conditions:
            request_body = kwargs.get('body')
            return self._check_conditions(request_headers, request_body)
        
        return True
    
    def _path_matches(self, request_path: str) -> bool:
        """Check if the request path matches this response's path"""
        # Exact match
        if self.path == request_path:
            return True
        
        # Pattern matching with wildcards
        if '*' in self.path:
            return self._wildcard_match(request_path)
        
        # Parameter matching (e.g., /users/{id})
        if '{' in self.path:
            return self._parameter_match(request_path)
        
        return False
    
    def _wildcard_match(self, request_path: str) -> bool:
        """Match paths with wildcards"""
        import re
        pattern = self.path.replace('*', '.*')
        return bool(re.match(pattern, request_path))
    
    def _parameter_match(self, request_path: str) -> bool:
        """Match paths with parameters"""
        import re
        # Convert /users/{id} to regex pattern
        pattern = re.sub(r'\{[^}]+\}', r'[^/]+', self.path)
        # Add end anchor to prevent partial matches
        pattern = pattern + '$'
        return bool(re.match(pattern, request_path))
    
    def _check_conditions(self, headers: Dict[str, str] = None, 
                         body: Any = None) -> bool:
        """Check if request meets all conditions"""
        if not headers:
            headers = {}
        
        for condition in self.conditions:
            if not self._evaluate_condition(condition, headers, body):
                return False
        
        return True
    
    def _evaluate_condition(self, condition: Dict[str, Any], 
                           headers: Dict[str, str], body: Any) -> bool:
        """Evaluate a single condition"""
        condition_type = condition.get('type', 'header')
        
        if condition_type == 'header':
            header_name = condition.get('name')
            expected_value = condition.get('value')
            return headers.get(header_name) == expected_value
        
        elif condition_type == 'body':
            field_path = condition.get('field')
            expected_value = condition.get('value')
            actual_value = self._get_nested_value(body, field_path)
            return actual_value == expected_value
        
        elif condition_type == 'custom':
            func = condition.get('function')
            return func(headers, body) if callable(func) else False
        
        return False
    
    def _get_nested_value(self, obj: Any, path: str) -> Any:
        """Get nested value from object using dot notation"""
        if not path:
            return obj
        
        keys = path.split('.')
        current = obj
        
        for key in keys:
            if isinstance(current, dict):
                current = current.get(key)
            elif isinstance(current, list) and key.isdigit():
                current = current[int(key)]
            else:
                return None
        
        return current
    
    def generate_response(self, request_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Generate the actual response based on type and context.
        
        Args:
            request_context: Additional context for response generation
            
        Returns:
            Dict containing status_code, headers, and body
        """
        # Check for errors
        if self.error_probability > 0 and self._should_return_error():
            return self._generate_error_response()
        
        # Apply delay if specified
        if self.delay_ms > 0:
            time.sleep(self.delay_ms / 1000.0)
        
        # Generate response based on type
        if self.response_type == ResponseType.STATIC:
            body = self.body
        elif self.response_type == ResponseType.DYNAMIC:
            body = self._generate_dynamic_response(request_context)
        elif self.response_type == ResponseType.TEMPLATED:
            body = self._generate_templated_response(request_context)
        else:
            body = self.body
        
        return {
            'status_code': self.status_code,
            'headers': self.headers.copy(),
            'body': body
        }
    
    def _should_return_error(self) -> bool:
        """Determine if an error should be returned based on probability"""
        import random
        return random.random() < self.error_probability
    
    def _generate_error_response(self) -> Dict[str, Any]:
        """Generate an error response"""
        return {
            'status_code': 500,
            'headers': {
                'Content-Type': 'application/json',
                'X-Mock-Error': 'true'
            },
            'body': {
                'error': 'Internal Server Error',
                'message': 'Mock error response',
                'timestamp': time.time()
            }
        }
    
    def _generate_dynamic_response(self, context: Dict[str, Any] = None) -> Any:
        """Generate dynamic response using generator function"""
        if self.generator_func:
            return self.generator_func(context or {})
        return self.body
    
    def _generate_templated_response(self, context: Dict[str, Any] = None) -> Any:
        """Generate templated response with variable substitution"""
        if isinstance(self.body, dict):
            # Handle dictionary body with template variables
            result = {}
            vars_dict = {**self.template_vars, **(context or {})}
            
            for key, value in self.body.items():
                if isinstance(value, str):
                    # Replace template variables in string values
                    for var_key, var_value in vars_dict.items():
                        value = value.replace(f'{{{{{var_key}}}}}', str(var_value))
                result[key] = value
            return result
        elif isinstance(self.body, str):
            template = self.body
            vars_dict = {**self.template_vars, **(context or {})}
            
            for key, value in vars_dict.items():
                template = template.replace(f'{{{{{key}}}}}', str(value))
            
            try:
                return json.loads(template)
            except json.JSONDecodeError:
                return template
        
        return self.body
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert response to dictionary for serialization"""
        return {
            'name': self.name,
            'path': self.path,
            'method': self.method.value,
            'status_code': self.status_code,
            'headers': self.headers,
            'body': self.body,
            'response_type': self.response_type.value,
            'delay_ms': self.delay_ms,
            'error_probability': self.error_probability,
            'conditions': self.conditions,
            'priority': self.priority,
            'template_vars': self.template_vars,
            'description': self.description,
            'tags': self.tags,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MockAPIResponse':
        """Create response from dictionary"""
        data = data.copy()
        data['method'] = HTTPMethod(data['method'])
        data['response_type'] = ResponseType(data['response_type'])
        return cls(**data)
    
    def update(self, **kwargs) -> None:
        """Update response properties"""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        self.updated_at = time.time()


@dataclass
class MockSet:
    """
    Efficient collection for managing multiple mock responses.
    
    Provides fast lookup, filtering, and management capabilities for large
    collections of mock responses.
    """
    
    name: str
    responses: List[MockAPIResponse] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Initialize the mock set"""
        self._build_index()
    
    def _build_index(self) -> None:
        """Build internal indexes for fast lookup"""
        self._path_index = {}
        self._method_index = {}
        self._tag_index = {}
        self._name_index = {}
        
        for response in self.responses:
            # Index by path
            if response.path not in self._path_index:
                self._path_index[response.path] = []
            self._path_index[response.path].append(response)
            
            # Index by method
            method_key = response.method.value
            if method_key not in self._method_index:
                self._method_index[method_key] = []
            self._method_index[method_key].append(response)
            
            # Index by tags
            for tag in response.tags:
                if tag not in self._tag_index:
                    self._tag_index[tag] = []
                self._tag_index[tag].append(response)
            
            # Index by name
            self._name_index[response.name] = response
    
    def add_response(self, response: MockAPIResponse) -> None:
        """Add a response to the set"""
        self.responses.append(response)
        self._build_index()
    
    def remove_response(self, response_name: str) -> bool:
        """Remove a response by name"""
        if response_name in self._name_index:
            response = self._name_index[response_name]
            self.responses.remove(response)
            self._build_index()
            return True
        return False
    
    def find_matching_response(self, path: str, method: str, 
                              headers: Dict[str, str] = None,
                              body: Any = None) -> Optional[MockAPIResponse]:
        """
        Find the best matching response for a request.
        
        Returns the highest priority response that matches the request.
        """
        matching_responses = []
        
        # Find all responses that match the request
        for response in self.responses:
            if response.matches_request(path, method, headers, body):
                matching_responses.append(response)
        
        if not matching_responses:
            return None
        
        # Return the highest priority response
        return max(matching_responses, key=lambda r: r.priority)
    
    def get_by_path(self, path: str) -> List[MockAPIResponse]:
        """Get all responses for a specific path"""
        return self._path_index.get(path, [])
    
    def get_by_method(self, method: str) -> List[MockAPIResponse]:
        """Get all responses for a specific HTTP method"""
        return self._method_index.get(method, [])
    
    def get_by_tag(self, tag: str) -> List[MockAPIResponse]:
        """Get all responses with a specific tag"""
        return self._tag_index.get(tag, [])
    
    def get_by_name(self, name: str) -> Optional[MockAPIResponse]:
        """Get a response by name"""
        return self._name_index.get(name)
    
    def filter(self, **kwargs) -> List[MockAPIResponse]:
        """Filter responses by multiple criteria"""
        filtered = self.responses
        
        for key, value in kwargs.items():
            if key == 'status_code':
                filtered = [r for r in filtered if r.status_code == value]
            elif key == 'response_type':
                filtered = [r for r in filtered if r.response_type == value]
            elif key == 'tags':
                if isinstance(value, str):
                    filtered = [r for r in filtered if value in r.tags]
                else:
                    filtered = [r for r in filtered if any(tag in r.tags for tag in value)]
        
        return filtered
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert mock set to dictionary"""
        return {
            'name': self.name,
            'responses': [r.to_dict() for r in self.responses],
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MockSet':
        """Create mock set from dictionary"""
        responses = [MockAPIResponse.from_dict(r) for r in data['responses']]
        return cls(
            name=data['name'],
            responses=responses,
            metadata=data.get('metadata', {})
        )
    
    def save_to_file(self, filepath: str) -> None:
        """Save mock set to file"""
        with open(filepath, 'w') as f:
            yaml.dump(self.to_dict(), f, default_flow_style=False)
    
    @classmethod
    def load_from_file(cls, filepath: str) -> 'MockSet':
        """Load mock set from file"""
        with open(filepath, 'r') as f:
            data = yaml.safe_load(f)
        return cls.from_dict(data)


# Example subclasses for common API interactions
class CommitResponse(MockAPIResponse):
    """Mock response for Git commit operations"""
    
    def __init__(self, **kwargs):
        super().__init__(
            path="/repos/{owner}/{repo}/git/commits",
            method=HTTPMethod.POST,
            status_code=201,
            response_type=ResponseType.TEMPLATED,
            template_vars={
                'sha': 'abc123def456',
                'message': 'feat: add new feature',
                'author': 'John Doe'
            },
            body={
                'sha': '{{sha}}',
                'message': '{{message}}',
                'author': {
                    'name': '{{author}}',
                    'email': 'john@example.com'
                },
                'committer': {
                    'name': '{{author}}',
                    'email': 'john@example.com'
                }
            },
            **kwargs
        )


class ForkResponse(MockAPIResponse):
    """Mock response for repository fork operations"""
    
    def __init__(self, **kwargs):
        super().__init__(
            path="/repos/{owner}/{repo}/forks",
            method=HTTPMethod.POST,
            status_code=202,
            response_type=ResponseType.STATIC,
            body={
                'id': 12345,
                'name': 'forked-repo',
                'full_name': 'new-owner/forked-repo',
                'fork': True,
                'source': {
                    'id': 67890,
                    'name': 'original-repo',
                    'full_name': 'original-owner/original-repo'
                }
            },
            **kwargs
        )


class PushResponse(MockAPIResponse):
    """Mock response for Git push operations"""
    
    def __init__(self, **kwargs):
        super().__init__(
            path="/repos/{owner}/{repo}/git/refs/heads/{branch}",
            method=HTTPMethod.PATCH,
            status_code=200,
            response_type=ResponseType.TEMPLATED,
            template_vars={
                'ref': 'refs/heads/main',
                'sha': 'def456ghi789'
            },
            body={
                'ref': '{{ref}}',
                'sha': '{{sha}}',
                'url': 'https://api.github.com/repos/owner/repo/git/refs/heads/main'
            },
            **kwargs
        )


class ForcePushResponse(MockAPIResponse):
    """Mock response for force push operations"""
    
    def __init__(self, **kwargs):
        super().__init__(
            path="/repos/{owner}/{repo}/git/refs/heads/{branch}",
            method=HTTPMethod.PATCH,
            status_code=200,
            response_type=ResponseType.STATIC,
            body={
                'ref': 'refs/heads/main',
                'sha': 'force123push456',
                'force': True,
                'url': 'https://api.github.com/repos/owner/repo/git/refs/heads/main'
            },
            **kwargs
        )


# Pytest fixture for easy integration
@pytest.fixture
def setup_api_mocks():
    """
    Pytest fixture for setting up mock API responses in tests.
    
    Usage:
        def test_api_call(setup_api_mocks):
            mock_set = setup_api_mocks
            mock_set.add_response(CommitResponse())
            # Your test code here
    """
    mock_set = MockSet("test_mocks")
    return mock_set


# Convenience functions for common operations
def create_user_response(user_id: str = "123", name: str = "John Doe") -> MockAPIResponse:
    """Create a mock user response"""
    return MockAPIResponse(
        path=f"/users/{user_id}",
        method=HTTPMethod.GET,
        status_code=200,
        response_type=ResponseType.TEMPLATED,
        template_vars={'user_id': user_id, 'name': name},
        body={
            'id': '{{user_id}}',
            'name': '{{name}}',
            'email': 'john@example.com',
            'created_at': '2023-01-01T00:00:00Z'
        }
    )


def create_error_response(status_code: int = 404, message: str = "Not found") -> MockAPIResponse:
    """Create a mock error response"""
    return MockAPIResponse(
        path="*",
        method=HTTPMethod.GET,
        status_code=status_code,
        response_type=ResponseType.STATIC,
        body={
            'error': True,
            'message': message,
            'status_code': status_code
        }
    )


def create_delayed_response(delay_ms: int = 1000) -> MockAPIResponse:
    """Create a mock response with delay"""
    return MockAPIResponse(
        path="/slow-endpoint",
        method=HTTPMethod.GET,
        status_code=200,
        response_type=ResponseType.STATIC,
        delay_ms=delay_ms,
        body={'message': 'Response delayed'}
    ) 