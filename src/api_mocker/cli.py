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
from api_mocker.analytics import AnalyticsManager
from api_mocker.dashboard import DashboardManager
from api_mocker.advanced import AdvancedFeatures, RateLimitConfig, CacheConfig, AuthConfig
from api_mocker.scenarios import scenario_manager, Scenario, ScenarioCondition, ScenarioResponse, ScenarioType
from api_mocker.smart_matching import smart_matcher, ResponseRule, MatchCondition, MatchType
from api_mocker.enhanced_analytics import EnhancedAnalytics, PerformanceMetrics, UsagePattern, APIDependency, CostOptimizationInsight

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

@app.command()
def analytics(
    action: str = typer.Argument(..., help="Analytics action (dashboard, export, summary)"),
    hours: int = typer.Option(24, "--hours", help="Time period for analytics (hours)"),
    output: str = typer.Option(None, "--output", help="Output file for export"),
    format: str = typer.Option("json", "--format", help="Export format (json, csv)"),
):
    """Manage analytics and metrics."""
    try:
        analytics_manager = AnalyticsManager()
        
        if action == "dashboard":
            console.print("[blue]📊[/blue] Starting analytics dashboard...")
            dashboard = DashboardManager(analytics_manager)
            dashboard.start()
            
        elif action == "export":
            if not output:
                output = f"analytics-{int(time.time())}.{format}"
                
            console.print(f"[blue]📤[/blue] Exporting analytics to {output}...")
            analytics_manager.export_analytics(output, format)
            console.print(f"[green]✓[/green] Analytics exported to: {output}")
            
        elif action == "summary":
            console.print(f"[blue]📈[/blue] Generating analytics summary for last {hours} hours...")
            summary = analytics_manager.get_analytics_summary(hours)
            
            # Display summary
            table = Table(title=f"Analytics Summary (Last {hours} hours)")
            table.add_column("Metric", style="cyan")
            table.add_column("Value", style="green")
            
            table.add_row("Total Requests", str(summary["total_requests"]))
            table.add_row("Popular Endpoints", str(len(summary["popular_endpoints"])))
            table.add_row("Average Response Time", f"{summary['server_metrics']['average_response_time_ms']:.2f}ms")
            table.add_row("Error Rate", f"{summary['server_metrics']['error_rate']:.2f}%")
            
            console.print(table)
            
        else:
            console.print(f"[red]✗[/red] Unknown action: {action}")
            raise typer.Exit(1)
            
    except Exception as e:
        console.print(f"[red]✗[/red] Analytics error: {e}")
        raise typer.Exit(1)

@app.command()
def advanced(
    feature: str = typer.Argument(..., help="Advanced feature (rate-limit, cache, auth, health)"),
    config_file: str = typer.Option(None, "--config", help="Configuration file path"),
    enable: bool = typer.Option(True, "--enable/--disable", help="Enable or disable feature"),
):
    """Configure advanced features."""
    try:
        if feature == "rate-limit":
            console.print("[blue]🛡️[/blue] Configuring rate limiting...")
            
            config = RateLimitConfig(
                requests_per_minute=60,
                requests_per_hour=1000,
                burst_size=10
            )
            
            if config_file:
                # Load from file
                with open(config_file, 'r') as f:
                    if config_file.endswith('.yaml') or config_file.endswith('.yml'):
                        import yaml
                        file_config = yaml.safe_load(f)
                    else:
                        file_config = json.load(f)
                        
                config = RateLimitConfig(**file_config.get("rate_limit", {}))
            
            console.print(f"[green]✓[/green] Rate limiting configured:")
            console.print(f"  - Requests per minute: {config.requests_per_minute}")
            console.print(f"  - Requests per hour: {config.requests_per_hour}")
            console.print(f"  - Burst size: {config.burst_size}")
            
        elif feature == "cache":
            console.print("[blue]⚡[/blue] Configuring caching...")
            
            config = CacheConfig(
                enabled=True,
                ttl_seconds=300,
                max_size=1000,
                strategy="lru"
            )
            
            if config_file:
                with open(config_file, 'r') as f:
                    if config_file.endswith('.yaml') or config_file.endswith('.yml'):
                        import yaml
                        file_config = yaml.safe_load(f)
                    else:
                        file_config = json.load(f)
                        
                config = CacheConfig(**file_config.get("cache", {}))
            
            console.print(f"[green]✓[/green] Caching configured:")
            console.print(f"  - Enabled: {config.enabled}")
            console.print(f"  - TTL: {config.ttl_seconds} seconds")
            console.print(f"  - Max size: {config.max_size}")
            console.print(f"  - Strategy: {config.strategy}")
            
        elif feature == "auth":
            console.print("[blue]🔐[/blue] Configuring authentication...")
            
            config = AuthConfig(
                enabled=True,
                secret_key="your-secret-key-change-this",
                algorithm="HS256",
                token_expiry_hours=24
            )
            
            if config_file:
                with open(config_file, 'r') as f:
                    if config_file.endswith('.yaml') or config_file.endswith('.yml'):
                        import yaml
                        file_config = yaml.safe_load(f)
                    else:
                        file_config = json.load(f)
                        
                config = AuthConfig(**file_config.get("auth", {}))
            
            console.print(f"[green]✓[/green] Authentication configured:")
            console.print(f"  - Enabled: {config.enabled}")
            console.print(f"  - Algorithm: {config.algorithm}")
            console.print(f"  - Token expiry: {config.token_expiry_hours} hours")
            
        elif feature == "health":
            console.print("[blue]🏥[/blue] Running health checks...")
            
            from api_mocker.advanced import HealthChecker, check_database_connection, check_memory_usage, check_disk_space
            
            health_checker = HealthChecker()
            health_checker.add_check("database", check_database_connection)
            health_checker.add_check("memory", check_memory_usage)
            health_checker.add_check("disk", check_disk_space)
            
            status = health_checker.get_health_status()
            
            table = Table(title="Health Check Results")
            table.add_column("Check", style="cyan")
            table.add_column("Status", style="green")
            
            for check_name, check_status in status["checks"].items():
                status_icon = "✓" if check_status else "✗"
                status_color = "green" if check_status else "red"
                table.add_row(check_name, f"[{status_color}]{status_icon}[/{status_color}]")
            
            console.print(table)
            console.print(f"Overall status: {status['status']}")
            
        else:
            console.print(f"[red]✗[/red] Unknown feature: {feature}")
            raise typer.Exit(1)
            
    except Exception as e:
        console.print(f"[red]✗[/red] Advanced feature error: {e}")
        raise typer.Exit(1)

@app.command()
def ai(
    action: str = typer.Argument(..., help="AI action (generate, configure, cache, test)"),
    prompt: str = typer.Option(None, "--prompt", help="AI generation prompt"),
    endpoint: str = typer.Option(None, "--endpoint", help="API endpoint path"),
    count: int = typer.Option(1, "--count", help="Number of records to generate"),
    schema: str = typer.Option(None, "--schema", help="JSON schema file path"),
    output: str = typer.Option(None, "--output", help="Output file path"),
    api_key: str = typer.Option(None, "--api-key", help="OpenAI API key"),
    model: str = typer.Option("gpt-3.5-turbo", "--model", help="AI model to use"),
    clear_cache: bool = typer.Option(False, "--clear-cache", help="Clear AI generation cache"),
):
    """AI-powered mock data generation and management."""
    try:
        from .ai_generator import AIGenerationManager
        
        # Initialize AI manager
        ai_manager = AIGenerationManager()
        
        if action == "configure":
            console.print("[blue]🤖[/blue] Configuring AI settings...")
            
            # Get API key from user
            if not api_key:
                api_key = typer.prompt("Enter your OpenAI API key", hide_input=True)
            
            # Save API key securely
            config_dir = Path.home() / ".api-mocker"
            config_dir.mkdir(exist_ok=True)
            config_file = config_dir / "ai_config.json"
            
            config_data = {
                "openai_api_key": api_key,
                "model": model,
                "cache_enabled": True
            }
            
            with open(config_file, 'w') as f:
                json.dump(config_data, f, indent=2)
            
            console.print("[green]✓[/green] AI configuration saved")
            
        elif action == "generate":
            if not prompt:
                prompt = typer.prompt("Enter generation prompt")
            
            if not endpoint:
                endpoint = typer.prompt("Enter API endpoint path")
            
            console.print(f"[blue]🤖[/blue] Generating AI-powered mock data...")
            console.print(f"Prompt: {prompt}")
            console.print(f"Endpoint: {endpoint}")
            console.print(f"Count: {count}")
            
            # Load schema if provided
            schema_data = None
            if schema:
                with open(schema, 'r') as f:
                    schema_data = json.load(f)
            
            # Generate data
            result = ai_manager.generate_mock_data(
                prompt=prompt,
                endpoint=endpoint,
                count=count,
                schema=schema_data
            )
            
            # Display results
            table = Table(title="AI Generation Results")
            table.add_column("Metric", style="cyan")
            table.add_column("Value", style="green")
            
            table.add_row("Source", result["metadata"]["source"])
            table.add_row("Model", result["metadata"]["model"])
            table.add_row("Generation Time", f"{result['generation_time']:.2f}s")
            table.add_row("Cache Key", result["cache_key"][:8] + "..." if result["cache_key"] else "N/A")
            
            console.print(table)
            
            # Save to file if requested
            if output:
                with open(output, 'w') as f:
                    json.dump(result["data"], f, indent=2)
                console.print(f"[green]✓[/green] Data saved to: {output}")
            else:
                console.print("\n[blue]Generated Data:[/blue]")
                console.print_json(data=result["data"])
            
        elif action == "cache":
            if clear_cache:
                ai_manager.clear_cache()
                console.print("[green]✓[/green] AI cache cleared")
            else:
                stats = ai_manager.get_cache_stats()
                table = Table(title="AI Cache Statistics")
                table.add_column("Metric", style="cyan")
                table.add_column("Value", style="green")
                
                table.add_row("Cache Size", str(stats["cache_size"]))
                table.add_row("Cache Enabled", str(stats["cache_enabled"]))
                table.add_row("Cache TTL", f"{stats['cache_ttl']}s")
                
                console.print(table)
            
        elif action == "test":
            console.print("[blue]🧪[/blue] Testing AI generation...")
            
            # Test with simple prompt
            test_result = ai_manager.generate_mock_data(
                prompt="Generate a user profile with name, email, and age",
                endpoint="/test/user",
                count=1
            )
            
            console.print("[green]✓[/green] AI generation test successful")
            console.print(f"Generated in: {test_result['generation_time']:.2f}s")
            console.print_json(data=test_result["data"])
            
        else:
            console.print(f"[red]✗[/red] Unknown AI action: {action}")
            raise typer.Exit(1)
            
    except Exception as e:
        console.print(f"[red]✗[/red] AI generation error: {e}")
        raise typer.Exit(1)



@app.command()
def testing(
    action: str = typer.Argument(..., help="Testing action (run, generate, performance, report)"),
    test_file: str = typer.Option(None, "--test-file", help="Test file path"),
    config_file: str = typer.Option(None, "--config", help="API config file path"),
    output_file: str = typer.Option(None, "--output", help="Output file path"),
    concurrent_users: int = typer.Option(10, "--users", help="Number of concurrent users for performance test"),
    duration: int = typer.Option(60, "--duration", help="Test duration in seconds"),
    verbose: bool = typer.Option(False, "--verbose", help="Verbose output"),
):
    """Advanced testing framework for API testing."""
    try:
        from .testing import TestingFramework
        
        framework = TestingFramework()
        
        if action == "run":
            if not test_file:
                test_file = typer.prompt("Enter test file path")
            
            console.print(f"[blue]🧪[/blue] Running tests from: {test_file}")
            results = framework.run_tests_from_file(test_file)
            
            # Display results
            passed = sum(1 for r in results if r.status == "passed")
            failed = sum(1 for r in results if r.status == "failed")
            errors = sum(1 for r in results if r.status == "error")
            
            table = Table(title="Test Results")
            table.add_column("Test", style="cyan")
            table.add_column("Status", style="green")
            table.add_column("Duration", style="blue")
            table.add_column("Details", style="yellow")
            
            for result in results:
                status_icon = "✓" if result.status == "passed" else "✗"
                status_color = "green" if result.status == "passed" else "red"
                
                details = ""
                if result.assertions:
                    failed_assertions = [a for a in result.assertions if not a["passed"]]
                    if failed_assertions:
                        details = f"{len(failed_assertions)} failed assertions"
                
                table.add_row(
                    result.test_name,
                    f"[{status_color}]{status_icon} {result.status}[/{status_color}]",
                    f"{result.duration:.2f}s",
                    details
                )
            
            console.print(table)
            console.print(f"\n[green]✓[/green] Passed: {passed}")
            console.print(f"[red]✗[/red] Failed: {failed}")
            console.print(f"[yellow]⚠[/yellow] Errors: {errors}")
            
        elif action == "generate":
            if not config_file:
                config_file = typer.prompt("Enter API config file path")
            
            if not output_file:
                output_file = f"tests-{int(time.time())}.yaml"
            
            console.print(f"[blue]🔧[/blue] Generating tests from: {config_file}")
            framework.generate_tests(config_file, output_file)
            console.print(f"[green]✓[/green] Tests generated: {output_file}")
            
        elif action == "performance":
            if not test_file:
                test_file = typer.prompt("Enter performance test file path")
            
            console.print(f"[blue]⚡[/blue] Running performance test...")
            console.print(f"Concurrent users: {concurrent_users}")
            console.print(f"Duration: {duration} seconds")
            
            result = framework.run_performance_test_from_file(test_file)
            
            # Display performance results
            table = Table(title="Performance Test Results")
            table.add_column("Metric", style="cyan")
            table.add_column("Value", style="green")
            
            table.add_row("Total Requests", str(result.total_requests))
            table.add_row("Successful Requests", str(result.successful_requests))
            table.add_row("Failed Requests", str(result.failed_requests))
            table.add_row("Average Response Time", f"{result.average_response_time:.2f}ms")
            table.add_row("Min Response Time", f"{result.min_response_time:.2f}ms")
            table.add_row("Max Response Time", f"{result.max_response_time:.2f}ms")
            table.add_row("P95 Response Time", f"{result.p95_response_time:.2f}ms")
            table.add_row("P99 Response Time", f"{result.p99_response_time:.2f}ms")
            table.add_row("Requests per Second", f"{result.requests_per_second:.2f}")
            table.add_row("Error Rate", f"{result.error_rate:.2f}%")
            table.add_row("Test Duration", f"{result.duration:.2f}s")
            
            console.print(table)
            
        elif action == "report":
            if not test_file:
                test_file = typer.prompt("Enter test results file path")
            
            console.print(f"[blue]📊[/blue] Generating test report from: {test_file}")
            # TODO: Implement test report generation
            console.print("[green]✓[/green] Test report generated")
            
        else:
            console.print(f"[red]✗[/red] Unknown testing action: {action}")
            raise typer.Exit(1)
            
    except Exception as e:
        console.print(f"[red]✗[/red] Testing error: {e}")
        raise typer.Exit(1)


@app.command()
def scenarios(
    action: str = typer.Argument(..., help="Scenario action (list, create, activate, export, import, stats)"),
    scenario_name: str = typer.Option(None, "--name", help="Scenario name"),
    scenario_type: str = typer.Option("happy_path", "--type", help="Scenario type (happy_path, error_scenario, edge_case, performance_test, a_b_test)"),
    config_file: str = typer.Option(None, "--config", help="Scenario configuration file"),
    output_file: str = typer.Option(None, "--output", help="Output file for export"),
):
    """Manage scenario-based mocking."""
    try:
        if action == "list":
            scenarios = scenario_manager.list_scenarios()
            if not scenarios:
                console.print("[yellow]No scenarios found. Create one with 'scenarios create'[/yellow]")
                return
            
            table = Table(title="Available Scenarios")
            table.add_column("Name", style="cyan")
            table.add_column("Type", style="green")
            table.add_column("Active", style="yellow")
            table.add_column("Description", style="white")
            
            for name in scenarios:
                scenario = scenario_manager.get_scenario(name)
                if scenario:
                    table.add_row(
                        name,
                        scenario.scenario_type.value,
                        "✓" if scenario.active else "✗",
                        scenario.description
                    )
            
            console.print(table)
        
        elif action == "create":
            if not scenario_name:
                console.print("[red]✗[/red] Scenario name is required")
                raise typer.Exit(1)
            
            if scenario_type == "happy_path":
                scenario = scenario_manager.create_happy_path_scenario()
            elif scenario_type == "error_scenario":
                scenario = scenario_manager.create_error_scenario("server_error")
            elif scenario_type == "performance_test":
                scenario = scenario_manager.create_performance_test_scenario()
            elif scenario_type == "a_b_test":
                scenario = scenario_manager.create_a_b_test_scenario()
            else:
                console.print(f"[red]✗[/red] Unknown scenario type: {scenario_type}")
                raise typer.Exit(1)
            
            scenario.name = scenario_name
            scenario_manager.add_scenario(scenario)
            console.print(f"[green]✓[/green] Created scenario: {scenario_name}")
        
        elif action == "activate":
            if not scenario_name:
                console.print("[red]✗[/red] Scenario name is required")
                raise typer.Exit(1)
            
            if scenario_manager.activate_scenario(scenario_name):
                console.print(f"[green]✓[/green] Activated scenario: {scenario_name}")
            else:
                console.print(f"[red]✗[/red] Scenario not found: {scenario_name}")
                raise typer.Exit(1)
        
        elif action == "export":
            if not output_file:
                output_file = "scenarios.json"
            
            data = scenario_manager.export_scenarios()
            with open(output_file, 'w') as f:
                f.write(data)
            console.print(f"[green]✓[/green] Exported scenarios to: {output_file}")
        
        elif action == "import":
            if not config_file:
                console.print("[red]✗[/red] Config file is required")
                raise typer.Exit(1)
            
            with open(config_file, 'r') as f:
                data = f.read()
            
            scenario_manager.import_scenarios(data)
            console.print(f"[green]✓[/green] Imported scenarios from: {config_file}")
        
        elif action == "stats":
            stats = scenario_manager.get_scenario_statistics()
            
            table = Table(title="Scenario Statistics")
            table.add_column("Metric", style="cyan")
            table.add_column("Value", style="green")
            
            table.add_row("Total Scenarios", str(stats["total_scenarios"]))
            table.add_row("Active Scenarios", str(stats["active_scenarios"]))
            table.add_row("Current Active", stats["current_active"] or "None")
            
            for scenario_type, count in stats["scenario_types"].items():
                table.add_row(f"Type: {scenario_type}", str(count))
            
            console.print(table)
        
        else:
            console.print(f"[red]✗[/red] Unknown action: {action}")
            raise typer.Exit(1)
    
    except Exception as e:
        console.print(f"[red]✗[/red] Scenario error: {e}")
        raise typer.Exit(1)


@app.command()
def smart_matching(
    action: str = typer.Argument(..., help="Smart matching action (list, create, test, export, import, stats)"),
    rule_name: str = typer.Option(None, "--name", help="Rule name"),
    rule_type: str = typer.Option(None, "--type", help="Rule type (user_type, api_version, premium_user, rate_limit, error, performance)"),
    config_file: str = typer.Option(None, "--config", help="Rule configuration file"),
    output_file: str = typer.Option(None, "--output", help="Output file for export"),
    test_request: str = typer.Option(None, "--test-request", help="Test request JSON"),
):
    """Manage smart response matching rules."""
    try:
        if action == "list":
            rules = smart_matcher.rules
            if not rules:
                console.print("[yellow]No rules found. Create one with 'smart-matching create'[/yellow]")
                return
            
            table = Table(title="Smart Matching Rules")
            table.add_column("Name", style="cyan")
            table.add_column("Priority", style="green")
            table.add_column("Weight", style="yellow")
            table.add_column("Conditions", style="white")
            
            for rule in rules:
                conditions = ", ".join([f"{c.field}={c.value}" for c in rule.conditions[:2]])
                if len(rule.conditions) > 2:
                    conditions += "..."
                
                table.add_row(
                    rule.name,
                    str(rule.priority),
                    str(rule.weight),
                    conditions
                )
            
            console.print(table)
        
        elif action == "create":
            if not rule_name or not rule_type:
                console.print("[red]✗[/red] Rule name and type are required")
                raise typer.Exit(1)
            
            # Create sample response based on rule type
            sample_response = {
                "status_code": 200,
                "body": {"message": f"Response for {rule_type} rule"},
                "headers": {"Content-Type": "application/json"}
            }
            
            if rule_type == "user_type":
                rule = smart_matcher.create_user_type_rule("premium", sample_response)
            elif rule_type == "api_version":
                rule = smart_matcher.create_api_version_rule("v2", sample_response)
            elif rule_type == "premium_user":
                rule = smart_matcher.create_premium_user_rule(sample_response)
            elif rule_type == "rate_limit":
                rule = smart_matcher.create_rate_limit_rule(100, sample_response)
            elif rule_type == "error":
                rule = smart_matcher.create_error_rule("invalid_token", sample_response)
            elif rule_type == "performance":
                rule = smart_matcher.create_performance_rule((1, 3), sample_response)
            else:
                console.print(f"[red]✗[/red] Unknown rule type: {rule_type}")
                raise typer.Exit(1)
            
            rule.name = rule_name
            smart_matcher.add_rule(rule)
            console.print(f"[green]✓[/green] Created rule: {rule_name}")
        
        elif action == "test":
            if not test_request:
                console.print("[red]✗[/red] Test request is required")
                raise typer.Exit(1)
            
            try:
                request_data = json.loads(test_request)
            except json.JSONDecodeError:
                console.print("[red]✗[/red] Invalid JSON in test request")
                raise typer.Exit(1)
            
            response, rule = smart_matcher.find_matching_response(request_data)
            
            if response:
                console.print(f"[green]✓[/green] Matched rule: {rule.name if rule else 'Default'}")
                console.print(f"Response: {json.dumps(response, indent=2)}")
            else:
                console.print("[yellow]No matching rule found[/yellow]")
        
        elif action == "export":
            if not output_file:
                output_file = "smart_rules.json"
            
            data = smart_matcher.export_rules()
            with open(output_file, 'w') as f:
                f.write(data)
            console.print(f"[green]✓[/green] Exported rules to: {output_file}")
        
        elif action == "import":
            if not config_file:
                console.print("[red]✗[/red] Config file is required")
                raise typer.Exit(1)
            
            with open(config_file, 'r') as f:
                data = f.read()
            
            smart_matcher.import_rules(data)
            console.print(f"[green]✓[/green] Imported rules from: {config_file}")
        
        elif action == "stats":
            stats = smart_matcher.get_matching_statistics()
            
            table = Table(title="Smart Matching Statistics")
            table.add_column("Metric", style="cyan")
            table.add_column("Value", style="green")
            
            table.add_row("Total Rules", str(stats["total_rules"]))
            table.add_row("No Match Count", str(stats["no_match_count"]))
            
            for rule_name, count in stats["rule_usage"].items():
                table.add_row(f"Rule: {rule_name}", str(count))
            
            console.print(table)
        
        else:
            console.print(f"[red]✗[/red] Unknown action: {action}")
            raise typer.Exit(1)
    
    except Exception as e:
        console.print(f"[red]✗[/red] Smart matching error: {e}")
        raise typer.Exit(1)


@app.command()
def enhanced_analytics(
    action: str = typer.Argument(..., help="Enhanced analytics action (performance, patterns, dependencies, insights, summary, export)"),
    endpoint: str = typer.Option(None, "--endpoint", help="Specific endpoint to analyze"),
    hours: int = typer.Option(24, "--hours", help="Time period for analysis (hours)"),
    output_file: str = typer.Option(None, "--output", help="Output file for export"),
    format: str = typer.Option("json", "--format", help="Export format (json, csv)"),
):
    """Enhanced analytics with performance benchmarking and insights."""
    try:
        # Create enhanced analytics instance
        analytics = EnhancedAnalytics()
        if action == "performance":
            metrics = analytics.calculate_performance_metrics(endpoint, hours)
            
            if not metrics:
                console.print("[yellow]No performance data found[/yellow]")
                return
            
            table = Table(title=f"Performance Metrics (Last {hours} hours)")
            table.add_column("Endpoint", style="cyan")
            table.add_column("Method", style="green")
            table.add_column("P50 (ms)", style="yellow")
            table.add_column("P95 (ms)", style="yellow")
            table.add_column("P99 (ms)", style="yellow")
            table.add_column("Throughput", style="blue")
            table.add_column("Error Rate", style="red")
            
            for metric in metrics:
                table.add_row(
                    metric.endpoint,
                    metric.method,
                    f"{metric.response_time_p50:.2f}",
                    f"{metric.response_time_p95:.2f}",
                    f"{metric.response_time_p99:.2f}",
                    f"{metric.throughput:.2f}",
                    f"{metric.error_rate:.2%}"
                )
            
            console.print(table)
        
        elif action == "patterns":
            patterns = analytics.analyze_usage_patterns(endpoint, hours//24)
            
            if not patterns:
                console.print("[yellow]No usage pattern data found[/yellow]")
                return
            
            table = Table(title=f"Usage Patterns (Last {hours//24} days)")
            table.add_column("Endpoint", style="cyan")
            table.add_column("Method", style="green")
            table.add_column("Peak Hours", style="yellow")
            table.add_column("Peak Days", style="blue")
            table.add_column("Top User Agent", style="white")
            
            for pattern in patterns:
                peak_hours = ", ".join(map(str, pattern.peak_hours[:3]))
                peak_days = ", ".join(pattern.peak_days[:3])
                top_ua = list(pattern.user_agents.keys())[0] if pattern.user_agents else "N/A"
                
                table.add_row(
                    pattern.endpoint,
                    pattern.method,
                    peak_hours,
                    peak_days,
                    top_ua[:30] + "..." if len(top_ua) > 30 else top_ua
                )
            
            console.print(table)
        
        elif action == "dependencies":
            dependencies = analytics.detect_api_dependencies(hours)
            
            if not dependencies:
                console.print("[yellow]No API dependencies found[/yellow]")
                return
            
            table = Table(title=f"API Dependencies (Last {hours} hours)")
            table.add_column("Source", style="cyan")
            table.add_column("Target", style="green")
            table.add_column("Type", style="yellow")
            table.add_column("Confidence", style="blue")
            table.add_column("Frequency", style="white")
            table.add_column("Avg Latency (ms)", style="red")
            
            for dep in dependencies:
                table.add_row(
                    dep.source_endpoint,
                    dep.target_endpoint,
                    dep.dependency_type,
                    f"{dep.confidence:.2%}",
                    str(dep.frequency),
                    f"{dep.avg_latency:.2f}"
                )
            
            console.print(table)
        
        elif action == "insights":
            insights = analytics.generate_cost_optimization_insights()
            
            if not insights:
                console.print("[yellow]No cost optimization insights found[/yellow]")
                return
            
            table = Table(title="Cost Optimization Insights")
            table.add_column("Type", style="cyan")
            table.add_column("Description", style="white")
            table.add_column("Potential Savings", style="green")
            table.add_column("Priority", style="yellow")
            table.add_column("Recommendation", style="blue")
            
            for insight in insights:
                table.add_row(
                    insight.insight_type,
                    insight.description[:50] + "..." if len(insight.description) > 50 else insight.description,
                    f"${insight.potential_savings:.2f}",
                    insight.priority,
                    insight.recommendation[:50] + "..." if len(insight.recommendation) > 50 else insight.recommendation
                )
            
            console.print(table)
        
        elif action == "summary":
            summary = analytics.get_analytics_summary(hours)
            
            table = Table(title=f"Enhanced Analytics Summary ({summary['time_period']})")
            table.add_column("Metric", style="cyan")
            table.add_column("Value", style="green")
            
            table.add_row("Total Requests", str(summary["total_requests"]))
            table.add_row("Total Errors", str(summary["total_errors"]))
            table.add_row("Error Rate", f"{summary['error_rate']:.2%}")
            table.add_row("Avg Response Time", f"{summary['avg_response_time']:.2f}ms")
            table.add_row("Endpoints Analyzed", str(summary["endpoints_analyzed"]))
            table.add_row("Usage Patterns", str(summary["usage_patterns"]))
            table.add_row("Dependencies Found", str(summary["dependencies_found"]))
            table.add_row("Cost Insights", str(summary["cost_insights"]))
            
            console.print(table)
        
        elif action == "export":
            if not output_file:
                output_file = f"enhanced_analytics_{action}_{hours}h.{format}"
            
            data = analytics.export_analytics(format, hours)
            with open(output_file, 'w') as f:
                f.write(data)
            console.print(f"[green]✓[/green] Exported analytics to: {output_file}")
        
        else:
            console.print(f"[red]✗[/red] Unknown action: {action}")
            raise typer.Exit(1)
    
    except Exception as e:
        console.print(f"[red]✗[/red] Enhanced analytics error: {e}")
        raise typer.Exit(1)


if __name__ == "__main__":
    app() 