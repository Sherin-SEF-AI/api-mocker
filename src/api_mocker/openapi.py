import json
import yaml
from typing import Dict, List, Any, Optional
from pathlib import Path
from .core import RouteConfig, CoreEngine

class OpenAPIParser:
    """Parses OpenAPI specifications and converts them to mock routes."""
    
    def __init__(self):
        self.spec: Dict[str, Any] = {}
        self.base_path = ""
        self.schemas = {}
    
    def load_spec(self, file_path: str) -> Dict[str, Any]:
        """Load OpenAPI specification from file."""
        path = Path(file_path)
        with open(path, 'r') as f:
            if path.suffix.lower() in ['.yaml', '.yml']:
                self.spec = yaml.safe_load(f)
            else:
                self.spec = json.load(f)
        
        self.base_path = self.spec.get('servers', [{}])[0].get('basePath', '')
        self.schemas = self.spec.get('components', {}).get('schemas', {})
        return self.spec
    
    def generate_routes(self, engine: CoreEngine) -> List[RouteConfig]:
        """Generate mock routes from OpenAPI specification."""
        routes = []
        paths = self.spec.get('paths', {})
        
        for path, path_item in paths.items():
            full_path = f"{self.base_path}{path}"
            
            for method, operation in path_item.items():
                if method.lower() in ['get', 'post', 'put', 'delete', 'patch']:
                    route = self._create_route(full_path, method, operation)
                    routes.append(route)
                    engine.router.add_route(route)
        
        return routes
    
    def _create_route(self, path: str, method: str, operation: Dict) -> RouteConfig:
        """Create a RouteConfig from OpenAPI operation."""
        response_schema = self._get_response_schema(operation)
        
        def dynamic_response(path: str, method: str, headers: Dict, body: Any, engine: CoreEngine):
            # Generate response based on schema
            if response_schema:
                response_data = engine.schema_validator.generate_from_schema(response_schema)
            else:
                response_data = {"message": f"Mock response for {method.upper()} {path}"}
            
            return {
                "status_code": 200,
                "body": response_data
            }
        
        return RouteConfig(
            path=path,
            method=method.upper(),
            response=dynamic_response,
            status_code=200,
            headers={"Content-Type": "application/json"}
        )
    
    def _get_response_schema(self, operation: Dict) -> Optional[str]:
        """Extract response schema from operation."""
        responses = operation.get('responses', {})
        
        # Look for 200 response first
        if '200' in responses:
            response = responses['200']
            if 'content' in response:
                content = response['content']
                if 'application/json' in content:
                    schema_ref = content['application/json'].get('schema', {})
                    return self._resolve_schema_ref(schema_ref)
        
        # Fallback to first available response
        for status_code, response in responses.items():
            if 'content' in response:
                content = response['content']
                if 'application/json' in content:
                    schema_ref = content['application/json'].get('schema', {})
                    return self._resolve_schema_ref(schema_ref)
        
        return None
    
    def _resolve_schema_ref(self, schema_ref: Dict) -> Optional[str]:
        """Resolve schema reference to actual schema."""
        if '$ref' in schema_ref:
            ref_path = schema_ref['$ref']
            if ref_path.startswith('#/components/schemas/'):
                schema_name = ref_path.split('/')[-1]
                return schema_name
        return None
    
    def export_spec(self, engine: CoreEngine, output_path: str):
        """Export current mock configuration as OpenAPI specification."""
        spec = {
            "openapi": "3.0.0",
            "info": {
                "title": "API Mocker Generated Spec",
                "version": "1.0.0",
                "description": "Generated from api-mocker configuration"
            },
            "paths": {}
        }
        
        for route in engine.router.routes:
            if route.path not in spec["paths"]:
                spec["paths"][route.path] = {}
            
            spec["paths"][route.path][route.method.lower()] = {
                "responses": {
                    "200": {
                        "description": "Mock response",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object"
                                }
                            }
                        }
                    }
                }
            }
        
        with open(output_path, 'w') as f:
            json.dump(spec, f, indent=2)

class PostmanImporter:
    """Imports Postman collections and converts them to mock routes."""
    
    def __init__(self):
        self.collection: Dict[str, Any] = {}
    
    def load_collection(self, file_path: str) -> Dict[str, Any]:
        """Load Postman collection from file."""
        with open(file_path, 'r') as f:
            self.collection = json.load(f)
        return self.collection
    
    def generate_routes(self, engine: CoreEngine) -> List[RouteConfig]:
        """Generate mock routes from Postman collection."""
        routes = []
        items = self.collection.get('item', [])
        
        for item in items:
            routes.extend(self._process_item(item, engine))
        
        return routes
    
    def _process_item(self, item: Dict, engine: CoreEngine) -> List[RouteConfig]:
        """Process a Postman collection item."""
        routes = []
        
        if 'request' in item:
            # This is a request item
            route = self._create_route_from_request(item['request'])
            routes.append(route)
            engine.router.add_route(route)
        elif 'item' in item:
            # This is a folder, process its items
            for sub_item in item['item']:
                routes.extend(self._process_item(sub_item, engine))
        
        return routes
    
    def _create_route_from_request(self, request: Dict) -> RouteConfig:
        """Create a RouteConfig from Postman request."""
        method = request.get('method', 'GET')
        url = request.get('url', {})
        
        if isinstance(url, str):
            path = url
        else:
            path = url.get('raw', '/')
        
        # Extract path from URL
        if path.startswith('http'):
            from urllib.parse import urlparse
            parsed = urlparse(path)
            path = parsed.path
        
        def dynamic_response(path: str, method: str, headers: Dict, body: Any, engine: CoreEngine):
            return {
                "status_code": 200,
                "body": {"message": f"Mock response for {method.upper()} {path}"}
            }
        
        return RouteConfig(
            path=path,
            method=method.upper(),
            response=dynamic_response,
            status_code=200,
            headers={"Content-Type": "application/json"}
        ) 