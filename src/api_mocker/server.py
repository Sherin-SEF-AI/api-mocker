from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
import uvicorn
from typing import Optional, Dict, Any
from .core import CoreEngine, RouteConfig
from .config import ConfigLoader
import logging

logger = logging.getLogger(__name__)

class MockServer:
    def __init__(self, config_path: Optional[str] = None, config_data: Optional[Dict[str, Any]] = None):
        self.app = FastAPI(title="api-mocker")
        self.config_path = config_path
        self.engine = CoreEngine()
        self.config = {}
        
        logging.basicConfig(level=logging.INFO)
        
        if config_data:
            self.config = config_data
            self._apply_config()
        elif config_path:
            self.load_config(config_path)
        
        self._setup_routes()

    def load_config(self, config_path: str):
        """Load configuration from file."""
        try:
            self.config = ConfigLoader.load(config_path)
            self._apply_config()
        except Exception as e:
            logger.error(f"Failed to load config {config_path}: {e}")

    def _apply_config(self):
        """Apply configuration to the engine."""
        routes_config = self.config.get("routes", [])
        logger.info(f"Loading {len(routes_config)} routes from config")
        
        for route_data in routes_config:
            logger.info(f"Adding route: {route_data['method']} {route_data['path']}")
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
                dynamic=route_data.get("dynamic", False),
                auth_required=route_data.get("auth", False)
            )
            self.engine.router.add_route(route)
        
        print(f"Total routes loaded: {len(self.engine.router.routes)}")

        # Process resources
        resources_config = self.config.get("resources", [])
        print(f"Loading {len(resources_config)} resources from config")
        
        for res_config in resources_config:
            name = res_config['name']
            base_path = res_config['path']
            id_field = res_config.get('id_field', 'id')
            
            print(f"Adding resource: {name} at {base_path}")
            
            # Import here to avoid circular imports
            from .resources import ResourceHandler
            handler = ResourceHandler(name, id_field)
            
            # Add standard CRUD routes
            # LIST
            self.engine.router.add_route(RouteConfig(
                path=base_path, 
                method="GET", 
                response=handler.list,
                delay=res_config.get('delay', 0)
            ))
            # CREATE
            self.engine.router.add_route(RouteConfig(
                path=base_path, 
                method="POST", 
                response=handler.create,
                delay=res_config.get('delay', 0)
            ))
            # GET Item
            self.engine.router.add_route(RouteConfig(
                path=f"{base_path}/{{id}}", 
                method="GET", 
                response=handler.get,
                delay=res_config.get('delay', 0)
            ))
            # UPDATE
            self.engine.router.add_route(RouteConfig(
                path=f"{base_path}/{{id}}", 
                method="PUT", 
                response=handler.update,
                delay=res_config.get('delay', 0)
            ))
            self.engine.router.add_route(RouteConfig(
                path=f"{base_path}/{{id}}", 
                method="PATCH", 
                response=handler.update,
                delay=res_config.get('delay', 0)
            ))
            # DELETE
            self.engine.router.add_route(RouteConfig(
                path=f"{base_path}/{{id}}", 
                method="DELETE", 
                response=handler.delete,
                delay=res_config.get('delay', 0)
            ))

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
            
            # Get query parameters
            query_params = dict(request.query_params)
            
            # Process request through core engine
            response = self.engine.process_request(path, method, headers, body, query_params)
            
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