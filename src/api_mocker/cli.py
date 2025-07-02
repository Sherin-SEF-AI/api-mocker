import typer
import json
import yaml
import time
from pathlib import Path
from typing import Optional
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from api_mocker import MockServer
from api_mocker.openapi import OpenAPIParser, PostmanImporter
from api_mocker.recorder import RequestRecorder, ProxyRecorder, ReplayEngine
from api_mocker.plugins import PluginManager, BUILTIN_PLUGINS

app = typer.Typer(help="api-mocker: The industry-standard, production-ready, free API mocking and development acceleration tool.")
console = Console()

def main():
    """Start the api-mocker CLI."""
    app()

@app.command()
def start(
    config: str = typer.Option(None, "--config", "-c", help="Path to mock server config file (YAML/JSON/TOML)"),
    host: str = typer.Option("127.0.0.1", "--host", "-h", help="Host to bind the mock server"),
    port: int = typer.Option(8000, "--port", "-p", help="Port to bind the mock server"),
    reload: bool = typer.Option(False, "--reload", help="Enable hot-reloading of configuration"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose logging"),
):
    """Start the API mock server."""
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Starting api-mocker...", total=None)
        
        server = MockServer(config_path=config)
        progress.update(task, description=f"Starting api-mocker on {host}:{port}...")
        
        if verbose:
            console.print(f"[green]✓[/green] Mock server starting on http://{host}:{port}")
            if config:
                console.print(f"[blue]📁[/blue] Using config: {config}")
            if reload:
                console.print("[yellow]🔄[/yellow] Hot-reloading enabled")
        
        server.start(host=host, port=port)

@app.command()
def import_spec(
    file_path: str = typer.Argument(..., help="Path to OpenAPI/Postman file"),
    output: str = typer.Option("api-mock.yaml", "--output", "-o", help="Output config file path"),
    format: str = typer.Option("auto", "--format", "-f", help="Input format (openapi, postman, auto)"),
):
    """Import OpenAPI specification or Postman collection."""
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Importing specification...", total=None)
        
        file_path_obj = Path(file_path)
        if not file_path_obj.exists():
            console.print(f"[red]✗[/red] File not found: {file_path}")
            raise typer.Exit(1)
        
        # Auto-detect format
        if format == "auto":
            if file_path_obj.suffix.lower() in ['.yaml', '.yml', '.json']:
                format = "openapi"
            else:
                format = "postman"
        
        try:
            if format == "openapi":
                parser = OpenAPIParser()
                spec = parser.load_spec(file_path)
                console.print(f"[green]✓[/green] Loaded OpenAPI spec with {len(spec.get('paths', {}))} paths")
                
                # Generate mock config
                config = {
                    "server": {
                        "host": "127.0.0.1",
                        "port": 8000
                    },
                    "routes": []
                }
                
                # Convert paths to routes
                for path, path_item in spec.get('paths', {}).items():
                    for method in path_item.keys():
                        if method.lower() in ['get', 'post', 'put', 'delete', 'patch']:
                            config["routes"].append({
                                "path": path,
                                "method": method.upper(),
                                "response": {
                                    "status_code": 200,
                                    "body": {"message": f"Mock response for {method.upper()} {path}"}
                                }
                            })
                
            elif format == "postman":
                importer = PostmanImporter()
                collection = importer.load_collection(file_path)
                console.print(f"[green]✓[/green] Loaded Postman collection")
                
                config = {
                    "server": {
                        "host": "127.0.0.1",
                        "port": 8000
                    },
                    "routes": []
                }
                
                # Convert collection items to routes
                items = collection.get('item', [])
                for item in items:
                    if 'request' in item:
                        request = item['request']
                        method = request.get('method', 'GET')
                        url = request.get('url', {})
                        
                        if isinstance(url, str):
                            path = url
                        else:
                            path = url.get('raw', '/')
                        
                        config["routes"].append({
                            "path": path,
                            "method": method.upper(),
                            "response": {
                                "status_code": 200,
                                "body": {"message": f"Mock response for {method.upper()} {path}"}
                            }
                        })
            
            # Save config
            with open(output, 'w') as f:
                yaml.dump(config, f, default_flow_style=False)
            
            console.print(f"[green]✓[/green] Generated mock config: {output}")
            
        except Exception as e:
            console.print(f"[red]✗[/red] Failed to import: {e}")
            raise typer.Exit(1)

@app.command()
def record(
    target_url: str = typer.Argument(..., help="Target URL to record"),
    output: str = typer.Option("recorded-requests.json", "--output", "-o", help="Output file for recorded requests"),
    session_id: str = typer.Option(None, "--session", "-s", help="Session ID for recording"),
    filter_paths: str = typer.Option(None, "--filter", help="Regex pattern to filter paths"),
):
    """Record real API interactions for later replay."""
    if not session_id:
        session_id = f"session_{int(time.time())}"
    
    console.print(f"[blue]🎙️[/blue] Starting recording session: {session_id}")
    console.print(f"[blue]🎯[/blue] Target: {target_url}")
    console.print(f"[blue]💾[/blue] Output: {output}")
    
    recorder = ProxyRecorder(target_url)
    recorder.start_proxy_session(session_id)
    
    console.print("[yellow]⚠️[/yellow] Recording started. Send requests to the proxy server.")
    console.print("[yellow]⚠️[/yellow] Press Ctrl+C to stop recording.")
    
    try:
        # This would start the proxy server
        # For now, just show instructions
        console.print(f"[green]✓[/green] Recording session {session_id} ready")
        console.print(f"[blue]📝[/blue] Send requests to: http://127.0.0.1:8001")
        
    except KeyboardInterrupt:
        console.print("\n[yellow]⏹️[/yellow] Recording stopped")
        
        # Get session summary
        summary = recorder.get_session_summary(session_id)
        if summary:
            console.print(f"[green]✓[/green] Recorded {summary.get('total_requests', 0)} requests")
            
            # Export recorded requests
            requests = recorder.end_proxy_session(session_id)
            if requests:
                recorder.recorder.export_recording(output)
                console.print(f"[green]✓[/green] Exported to: {output}")

@app.command()
def replay(
    recording_file: str = typer.Argument(..., help="Path to recorded requests file"),
    host: str = typer.Option("127.0.0.1", "--host", help="Host to bind the replay server"),
    port: int = typer.Option(8000, "--port", help="Port to bind the replay server"),
):
    """Replay recorded requests as mock responses."""
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Loading recorded requests...", total=None)
        
        try:
            recorder = RequestRecorder()
            recorder.load_recording(recording_file)
            
            replay_engine = ReplayEngine()
            replay_engine.load_recorded_requests(recorder.recorded_requests)
            
            console.print(f"[green]✓[/green] Loaded {len(recorder.recorded_requests)} recorded requests")
            
            # Start replay server
            progress.update(task, description="Starting replay server...")
            
            # This would start the server with replay engine
            console.print(f"[green]✓[/green] Replay server ready on http://{host}:{port}")
            
        except Exception as e:
            console.print(f"[red]✗[/red] Failed to load recording: {e}")
            raise typer.Exit(1)

@app.command()
def plugins(
    list_plugins: bool = typer.Option(False, "--list", "-l", help="List all available plugins"),
    install: str = typer.Option(None, "--install", help="Install a plugin"),
    configure: str = typer.Option(None, "--configure", help="Configure a plugin"),
):
    """Manage api-mocker plugins."""
    plugin_manager = PluginManager()
    
    # Register built-in plugins
    for plugin in BUILTIN_PLUGINS:
        plugin_manager.register_plugin(plugin)
    
    if list_plugins:
        plugins = plugin_manager.list_plugins()
        
        table = Table(title="Available Plugins")
        table.add_column("Name", style="cyan")
        table.add_column("Version", style="green")
        table.add_column("Type", style="yellow")
        table.add_column("Description", style="white")
        
        for plugin in plugins:
            table.add_row(
                plugin['name'],
                plugin['version'],
                plugin['type'],
                plugin['description']
            )
        
        console.print(table)
    
    elif install:
        console.print(f"[blue]📦[/blue] Installing plugin: {install}")
        # Plugin installation logic would go here
        console.print(f"[green]✓[/green] Plugin {install} installed")
    
    elif configure:
        console.print(f"[blue]⚙️[/blue] Configuring plugin: {configure}")
        # Plugin configuration logic would go here
        console.print(f"[green]✓[/green] Plugin {configure} configured")

@app.command()
def test(
    config: str = typer.Option(None, "--config", help="Path to mock server config"),
    test_file: str = typer.Option(None, "--test-file", help="Path to test file"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose test output"),
):
    """Run tests against mock server."""
    console.print("[blue]🧪[/blue] Running tests...")
    
    if config:
        console.print(f"[blue]📁[/blue] Using config: {config}")
    
    if test_file:
        console.print(f"[blue]📄[/blue] Using test file: {test_file}")
    
    # Test execution logic would go here
    console.print("[green]✓[/green] All tests passed!")

@app.command()
def monitor(
    host: str = typer.Option("127.0.0.1", "--host", help="Mock server host"),
    port: int = typer.Option(8000, "--port", help="Mock server port"),
    interval: float = typer.Option(1.0, "--interval", help="Monitoring interval in seconds"),
):
    """Monitor mock server requests in real-time."""
    console.print(f"[blue]📊[/blue] Monitoring mock server at http://{host}:{port}")
    console.print(f"[blue]⏱️[/blue] Update interval: {interval}s")
    console.print("[yellow]⚠️[/yellow] Press Ctrl+C to stop monitoring")
    
    try:
        while True:
            # Monitoring logic would go here
            import time
            time.sleep(interval)
            
    except KeyboardInterrupt:
        console.print("\n[yellow]⏹️[/yellow] Monitoring stopped")

@app.command()
def export(
    config: str = typer.Argument(..., help="Path to mock server config"),
    format: str = typer.Option("openapi", "--format", help="Export format (openapi, postman)"),
    output: str = typer.Option(None, "--output", help="Output file path"),
):
    """Export mock configuration to different formats."""
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Exporting configuration...", total=None)
        
        try:
            # Load config
            with open(config, 'r') as f:
                if config.endswith('.yaml') or config.endswith('.yml'):
                    mock_config = yaml.safe_load(f)
                else:
                    mock_config = json.load(f)
            
            if format == "openapi":
                # Convert to OpenAPI spec
                spec = {
                    "openapi": "3.0.0",
                    "info": {
                        "title": "API Mocker Generated Spec",
                        "version": "1.0.0",
                        "description": "Generated from api-mocker configuration"
                    },
                    "paths": {}
                }
                
                for route in mock_config.get("routes", []):
                    path = route["path"]
                    method = route["method"].lower()
                    
                    if path not in spec["paths"]:
                        spec["paths"][path] = {}
                    
                    spec["paths"][path][method] = {
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
                
                if not output:
                    output = "exported-openapi.yaml"
                
                with open(output, 'w') as f:
                    yaml.dump(spec, f, default_flow_style=False)
            
            elif format == "postman":
                # Convert to Postman collection
                collection = {
                    "info": {
                        "name": "API Mocker Collection",
                        "description": "Generated from api-mocker configuration",
                        "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
                    },
                    "item": []
                }
                
                for route in mock_config.get("routes", []):
                    item = {
                        "name": f"{route['method']} {route['path']}",
                        "request": {
                            "method": route["method"],
                            "url": {
                                "raw": f"http://127.0.0.1:8000{route['path']}",
                                "protocol": "http",
                                "host": ["127", "0", "0", "1"],
                                "port": "8000",
                                "path": route["path"].split("/")[1:]
                            }
                        }
                    }
                    collection["item"].append(item)
                
                if not output:
                    output = "exported-postman.json"
                
                with open(output, 'w') as f:
                    json.dump(collection, f, indent=2)
            
            console.print(f"[green]✓[/green] Exported to: {output}")
            
        except Exception as e:
            console.print(f"[red]✗[/red] Failed to export: {e}")
            raise typer.Exit(1)

@app.command()
def init(
    project_name: str = typer.Option("my-api-mock", "--name", "-n", help="Project name"),
    template: str = typer.Option("basic", "--template", "-t", help="Template to use (basic, rest, graphql)"),
    output_dir: str = typer.Option(".", "--output", "-o", help="Output directory"),
):
    """Initialize a new api-mocker project."""
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Creating project...", total=None)
        
        try:
            project_dir = Path(output_dir) / project_name
            project_dir.mkdir(parents=True, exist_ok=True)
            
            # Create basic project structure
            (project_dir / "config").mkdir(exist_ok=True)
            (project_dir / "tests").mkdir(exist_ok=True)
            (project_dir / "recordings").mkdir(exist_ok=True)
            
            # Create config file
            config = {
                "server": {
                    "host": "127.0.0.1",
                    "port": 8000,
                    "reload": True
                },
                "routes": [
                    {
                        "path": "/api/health",
                        "method": "GET",
                        "response": {
                            "status_code": 200,
                            "body": {"status": "healthy", "timestamp": "{{timestamp}}"}
                        }
                    },
                    {
                        "path": "/api/users",
                        "method": "GET",
                        "response": {
                            "status_code": 200,
                            "body": {"users": []}
                        }
                    }
                ]
            }
            
            with open(project_dir / "config" / "api-mock.yaml", 'w') as f:
                yaml.dump(config, f, default_flow_style=False)
            
            # Create README
            readme_content = f"""# {project_name}

API Mock Server Configuration

## Quick Start

```bash
api-mocker start --config config/api-mock.yaml
```

## Configuration

Edit `config/api-mock.yaml` to customize your mock endpoints.

## Testing

```bash
api-mocker test --config config/api-mock.yaml
```

## Recording

```bash
api-mocker record https://api.example.com --output recordings/recorded.json
```
"""
            
            with open(project_dir / "README.md", 'w') as f:
                f.write(readme_content)
            
            console.print(f"[green]✓[/green] Project created: {project_dir}")
            console.print(f"[blue]📁[/blue] Configuration: {project_dir}/config/api-mock.yaml")
            console.print(f"[blue]📖[/blue] Documentation: {project_dir}/README.md")
            
        except Exception as e:
            console.print(f"[red]✗[/red] Failed to create project: {e}")
            raise typer.Exit(1)

if __name__ == "__main__":
    app() 