import importlib
import importlib.util
import inspect
from typing import Dict, Any, List, Optional, Callable, Type
from abc import ABC, abstractmethod
from pathlib import Path
import json

class PluginBase(ABC):
    """Base class for all api-mocker plugins."""
    
    @abstractmethod
    def name(self) -> str:
        """Return the plugin name."""
        pass
    
    @abstractmethod
    def version(self) -> str:
        """Return the plugin version."""
        pass
    
    @abstractmethod
    def description(self) -> str:
        """Return the plugin description."""
        pass

class ResponseGeneratorPlugin(PluginBase):
    """Plugin for custom response generation."""
    
    @abstractmethod
    def generate_response(self, path: str, method: str, headers: Dict, body: Any, context: Dict) -> Dict[str, Any]:
        """Generate a custom response."""
        pass

class RequestProcessorPlugin(PluginBase):
    """Plugin for custom request processing."""
    
    @abstractmethod
    def process_request(self, path: str, method: str, headers: Dict, body: Any) -> tuple:
        """Process a request and return modified path, method, headers, body."""
        pass

class AuthenticationPlugin(PluginBase):
    """Plugin for custom authentication handling."""
    
    @abstractmethod
    def authenticate(self, headers: Dict, body: Any) -> bool:
        """Authenticate a request."""
        pass
    
    @abstractmethod
    def generate_auth_response(self, auth_failed: bool) -> Dict[str, Any]:
        """Generate authentication response."""
        pass

class DataSourcePlugin(PluginBase):
    """Plugin for custom data sources."""
    
    @abstractmethod
    def get_data(self, query: str, params: Dict) -> Any:
        """Get data from the source."""
        pass
    
    @abstractmethod
    def set_data(self, query: str, data: Any, params: Dict) -> bool:
        """Set data in the source."""
        pass

class PluginManager:
    """Manages plugin discovery, loading, and execution."""
    
    def __init__(self):
        self.plugins: Dict[str, PluginBase] = {}
        self.response_generators: List[ResponseGeneratorPlugin] = []
        self.request_processors: List[RequestProcessorPlugin] = []
        self.auth_providers: List[AuthenticationPlugin] = []
        self.data_sources: List[DataSourcePlugin] = []
        self.plugin_configs: Dict[str, Dict] = {}
    
    def discover_plugins(self, plugin_dir: Optional[str] = None):
        """Discover plugins in the specified directory."""
        if plugin_dir is None:
            plugin_dir = Path.home() / ".api-mocker" / "plugins"
        
        plugin_path = Path(plugin_dir)
        if not plugin_path.exists():
            return
        
        for plugin_file in plugin_path.glob("*.py"):
            if plugin_file.name.startswith("_"):
                continue
            
            try:
                self._load_plugin(plugin_file)
            except Exception as e:
                print(f"Failed to load plugin {plugin_file}: {e}")
    
    def _load_plugin(self, plugin_file: Path):
        """Load a single plugin from file."""
        module_name = plugin_file.stem
        spec = importlib.util.spec_from_file_location(module_name, plugin_file)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # Find plugin classes in the module
        for name, obj in inspect.getmembers(module):
            if (inspect.isclass(obj) and 
                issubclass(obj, PluginBase) and 
                obj != PluginBase):
                plugin_instance = obj()
                self.register_plugin(plugin_instance)
    
    def register_plugin(self, plugin: PluginBase):
        """Register a plugin instance."""
        plugin_name = plugin.name()
        self.plugins[plugin_name] = plugin
        
        # Categorize the plugin
        if isinstance(plugin, ResponseGeneratorPlugin):
            self.response_generators.append(plugin)
        elif isinstance(plugin, RequestProcessorPlugin):
            self.request_processors.append(plugin)
        elif isinstance(plugin, AuthenticationPlugin):
            self.auth_providers.append(plugin)
        elif isinstance(plugin, DataSourcePlugin):
            self.data_sources.append(plugin)
    
    def get_plugin(self, name: str) -> Optional[PluginBase]:
        """Get a plugin by name."""
        return self.plugins.get(name)
    
    def list_plugins(self) -> List[Dict[str, str]]:
        """List all registered plugins."""
        return [
            {
                'name': plugin.name(),
                'version': plugin.version(),
                'description': plugin.description(),
                'type': self._get_plugin_type(plugin)
            }
            for plugin in self.plugins.values()
        ]
    
    def _get_plugin_type(self, plugin: PluginBase) -> str:
        """Get the type of a plugin."""
        if isinstance(plugin, ResponseGeneratorPlugin):
            return "response_generator"
        elif isinstance(plugin, RequestProcessorPlugin):
            return "request_processor"
        elif isinstance(plugin, AuthenticationPlugin):
            return "authentication"
        elif isinstance(plugin, DataSourcePlugin):
            return "data_source"
        return "unknown"
    
    def configure_plugin(self, plugin_name: str, config: Dict):
        """Configure a plugin with settings."""
        self.plugin_configs[plugin_name] = config
    
    def get_plugin_config(self, plugin_name: str) -> Dict:
        """Get configuration for a plugin."""
        return self.plugin_configs.get(plugin_name, {})

# Example plugins

class ExampleResponseGenerator(ResponseGeneratorPlugin):
    """Example response generator plugin."""
    
    def name(self) -> str:
        return "example_response_generator"
    
    def version(self) -> str:
        return "1.0.0"
    
    def description(self) -> str:
        return "Generates example responses for demonstration"
    
    def generate_response(self, path: str, method: str, headers: Dict, body: Any, context: Dict) -> Dict[str, Any]:
        return {
            "status_code": 200,
            "body": {
                "message": f"Generated by {self.name()}",
                "path": path,
                "method": method,
                "timestamp": context.get("timestamp", "")
            }
        }

class ExampleAuthPlugin(AuthenticationPlugin):
    """Example authentication plugin."""
    
    def name(self) -> str:
        return "example_auth"
    
    def version(self) -> str:
        return "1.0.0"
    
    def description(self) -> str:
        return "Example authentication plugin"
    
    def authenticate(self, headers: Dict, body: Any) -> bool:
        # Simple API key check
        api_key = headers.get("X-API-Key")
        return api_key == "example-key"
    
    def generate_auth_response(self, auth_failed: bool) -> Dict[str, Any]:
        if auth_failed:
            return {
                "status_code": 401,
                "body": {"error": "Authentication failed"}
            }
        return {
            "status_code": 200,
            "body": {"message": "Authentication successful"}
        }

class ExampleDataSource(DataSourcePlugin):
    """Example data source plugin."""
    
    def name(self) -> str:
        return "example_data_source"
    
    def version(self) -> str:
        return "1.0.0"
    
    def description(self) -> str:
        return "Example data source plugin"
    
    def get_data(self, query: str, params: Dict) -> Any:
        # Return mock data based on query
        if "users" in query:
            return [
                {"id": 1, "name": "John Doe", "email": "john@example.com"},
                {"id": 2, "name": "Jane Smith", "email": "jane@example.com"}
            ]
        return {"message": "No data found"}
    
    def set_data(self, query: str, data: Any, params: Dict) -> bool:
        # Mock data storage
        return True

# Plugin registry for built-in plugins
BUILTIN_PLUGINS = [
    ExampleResponseGenerator(),
    ExampleAuthPlugin(),
    ExampleDataSource()
] 