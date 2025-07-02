import re
import json
import random
from typing import Dict, Any, List, Optional, Callable, Union
from dataclasses import dataclass
from datetime import datetime, timedelta
import uuid

@dataclass
class RouteConfig:
    path: str
    method: str
    response: Union[Dict, Callable, str]
    status_code: int = 200
    headers: Optional[Dict[str, str]] = None
    delay: float = 0
    dynamic: bool = False

class DynamicResponseGenerator:
    """Generates realistic fake data for API responses."""
    
    @staticmethod
    def generate_user():
        return {
            "id": str(uuid.uuid4()),
            "name": f"User {random.randint(1000, 9999)}",
            "email": f"user{random.randint(1000, 9999)}@example.com",
            "created_at": datetime.now().isoformat()
        }
    
    @staticmethod
    def generate_product():
        return {
            "id": random.randint(1, 1000),
            "name": f"Product {random.randint(1, 100)}",
            "price": round(random.uniform(10, 1000), 2),
            "category": random.choice(["electronics", "clothing", "books", "home"])
        }
    
    @staticmethod
    def generate_list(item_type: str, count: int = 10):
        generators = {
            "user": DynamicResponseGenerator.generate_user,
            "product": DynamicResponseGenerator.generate_product
        }
        generator = generators.get(item_type, DynamicResponseGenerator.generate_user)
        return [generator() for _ in range(count)]

class AdvancedRouter:
    """Handles advanced routing with regex patterns, path parameters, and dynamic matching."""
    
    def __init__(self):
        self.routes: List[RouteConfig] = []
        self.path_params = {}
    
    def add_route(self, route: RouteConfig):
        self.routes.append(route)
    
    def find_route(self, path: str, method: str) -> Optional[RouteConfig]:
        # Normalize path - ensure it starts with /
        if not path.startswith('/'):
            path = '/' + path
        
        print(f"Looking for route: {method} {path}")
        print(f"Available routes: {[(r.method, r.path) for r in self.routes]}")
        for route in self.routes:
            if self._match_route(route, path, method):
                return route
        return None
    
    def _match_route(self, route: RouteConfig, path: str, method: str) -> bool:
        if route.method.upper() != method.upper():
            return False
        
        # Convert route path to regex pattern
        pattern = self._path_to_regex(route.path)
        print(f"Comparing: '{path}' with pattern '{pattern}'")
        match = re.match(pattern, path)
        if match:
            self.path_params = match.groupdict()
            return True
        return False
    
    def _path_to_regex(self, path: str) -> str:
        """Convert path with parameters to regex pattern."""
        # Replace {param} with regex groups
        pattern = re.sub(r'\{(\w+)\}', r'(?P<\1>[^/]+)', path)
        return f"^{pattern}$"
    
    def get_path_params(self) -> Dict[str, str]:
        return self.path_params.copy()

class SchemaValidator:
    """Validates requests and generates responses based on OpenAPI schemas."""
    
    def __init__(self):
        self.schemas = {}
    
    def add_schema(self, name: str, schema: Dict):
        self.schemas[name] = schema
    
    def validate_request(self, schema_name: str, data: Dict) -> bool:
        # Placeholder for schema validation
        return True
    
    def generate_from_schema(self, schema_name: str) -> Dict:
        schema = self.schemas.get(schema_name, {})
        return self._generate_data(schema)
    
    def _generate_data(self, schema: Dict) -> Any:
        if "type" not in schema:
            return {}
        
        schema_type = schema["type"]
        if schema_type == "object":
            return self._generate_object(schema)
        elif schema_type == "array":
            return self._generate_array(schema)
        elif schema_type == "string":
            return self._generate_string(schema)
        elif schema_type == "integer":
            return self._generate_integer(schema)
        elif schema_type == "number":
            return self._generate_number(schema)
        elif schema_type == "boolean":
            return random.choice([True, False])
        return None
    
    def _generate_object(self, schema: Dict) -> Dict:
        result = {}
        properties = schema.get("properties", {})
        for prop_name, prop_schema in properties.items():
            result[prop_name] = self._generate_data(prop_schema)
        return result
    
    def _generate_array(self, schema: Dict) -> List:
        items_schema = schema.get("items", {})
        count = schema.get("minItems", 1)
        return [self._generate_data(items_schema) for _ in range(count)]
    
    def _generate_string(self, schema: Dict) -> str:
        if "enum" in schema:
            return random.choice(schema["enum"])
        elif "format" in schema:
            return self._generate_formatted_string(schema["format"])
        return f"string_{random.randint(1000, 9999)}"
    
    def _generate_integer(self, schema: Dict) -> int:
        minimum = schema.get("minimum", 0)
        maximum = schema.get("maximum", 100)
        return random.randint(minimum, maximum)
    
    def _generate_number(self, schema: Dict) -> float:
        minimum = schema.get("minimum", 0.0)
        maximum = schema.get("maximum", 100.0)
        return round(random.uniform(minimum, maximum), 2)
    
    def _generate_formatted_string(self, format_type: str) -> str:
        if format_type == "email":
            return f"user{random.randint(1000, 9999)}@example.com"
        elif format_type == "date":
            return datetime.now().date().isoformat()
        elif format_type == "datetime":
            return datetime.now().isoformat()
        elif format_type == "uuid":
            return str(uuid.uuid4())
        return f"formatted_{format_type}_{random.randint(1000, 9999)}"

class StateManager:
    """Manages state across requests for CRUD operations and data persistence."""
    
    def __init__(self):
        self.data: Dict[str, Any] = {}
        self.counters: Dict[str, int] = {}
    
    def get_data(self, key: str) -> Any:
        return self.data.get(key)
    
    def set_data(self, key: str, value: Any):
        self.data[key] = value
    
    def delete_data(self, key: str) -> bool:
        if key in self.data:
            del self.data[key]
            return True
        return False
    
    def get_next_id(self, resource: str) -> int:
        if resource not in self.counters:
            self.counters[resource] = 0
        self.counters[resource] += 1
        return self.counters[resource]
    
    def reset(self):
        self.data.clear()
        self.counters.clear()

class CoreEngine:
    """The main engine that orchestrates all core functionality."""
    
    def __init__(self):
        self.router = AdvancedRouter()
        self.schema_validator = SchemaValidator()
        self.state_manager = StateManager()
        self.response_generator = DynamicResponseGenerator()
        self.middleware: List[Callable] = []
    
    def add_middleware(self, middleware_func: Callable):
        self.middleware.append(middleware_func)
    
    def process_request(self, path: str, method: str, headers: Dict, body: Any = None) -> Dict:
        # Apply middleware
        for middleware in self.middleware:
            path, method, headers, body = middleware(path, method, headers, body)
        
        # Find matching route
        route = self.router.find_route(path, method)
        if not route:
            return {"status_code": 404, "body": {"error": "Route not found"}}
        
        # Generate response
        response = self._generate_response(route, path, method, headers, body)
        
        # Apply delay if specified
        if route.delay > 0:
            import time
            time.sleep(route.delay)
        
        return response
    
    def _generate_response(self, route: RouteConfig, path: str, method: str, headers: Dict, body: Any) -> Dict:
        if callable(route.response):
            return route.response(path, method, headers, body, self)
        elif isinstance(route.response, str):
            return {"status_code": route.status_code, "body": route.response}
        else:
            return {"status_code": route.status_code, "body": route.response} 