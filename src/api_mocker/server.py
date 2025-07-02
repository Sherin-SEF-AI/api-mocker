from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
import uvicorn
from typing import Optional, Dict, Any
from .core import CoreEngine, RouteConfig
from .config import ConfigLoader

class MockServer:
    def __init__(self, config_path: Optional[str] = None):
        self.app = FastAPI(title="api-mocker")
        self.config_path = config_path
        self.engine = CoreEngine()
        self.config = {}
        
        if config_path:
            self.load_config(config_path)
        
        self._setup_routes()

    def load_config(self, config_path: str):
        """Load configuration from file."""
        try:
            self.config = ConfigLoader.load(config_path)
            self._apply_config()
        except Exception as e:
            print(f"Warning: Failed to load config {config_path}: {e}")

    def _apply_config(self):
        """Apply configuration to the engine."""
        routes_config = self.config.get("routes", [])
        print(f"Loading {len(routes_config)} routes from config")
        
        for route_data in routes_config:
            print(f"Adding route: {route_data['method']} {route_data['path']}")
            # Create a response function from the config
            response_config = route_data.get("response", {})
            
            def create_response_func(config):
                def response_func(path: str, method: str, headers: Dict, body: Any, engine):
                    return {
                        "status_code": config.get("status_code", 200),
                        "body": config.get("body", {}),
                        "headers": config.get("headers", {})
                    }
                return response_func
            
            route = RouteConfig(
                path=route_data["path"],
                method=route_data["method"],
                response=create_response_func(response_config),
                status_code=response_config.get("status_code", 200),
                headers=response_config.get("headers"),
                delay=route_data.get("delay", 0),
                dynamic=route_data.get("dynamic", False)
            )
            self.engine.router.add_route(route)
        
        print(f"Total routes loaded: {len(self.engine.router.routes)}")

    def _setup_routes(self):
        """Set up FastAPI routes using the core engine."""
        
        @self.app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"])
        async def handle_request(request: Request, path: str):
            # Get request details
            method = request.method
            headers = dict(request.headers)
            body = None
            
            print(f"Received request: {method} /{path}")
            
            if method in ["POST", "PUT", "PATCH"]:
                try:
                    body = await request.json()
                except:
                    body = await request.body()
            
            # Process request through core engine
            response = self.engine.process_request(path, method, headers, body)
            
            # Return response
            status_code = response.get("status_code", 200)
            response_body = response.get("body", {})
            response_headers = response.get("headers", {})
            
            return JSONResponse(
                content=response_body,
                status_code=status_code,
                headers=response_headers
            )

    def start(self, host: str = "127.0.0.1", port: int = 8000):
        """Start the mock server."""
        print(f"Starting api-mocker server on http://{host}:{port}")
        print(f"Loaded {len(self.engine.router.routes)} routes")
        uvicorn.run(self.app, host=host, port=port) 