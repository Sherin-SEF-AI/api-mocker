# 🚀 API-Mocker Complete Guide

**The Industry-Standard, Production-Ready, Free API Mocking and Development Acceleration Tool**

## 📋 Table of Contents

1. [Quick Start](#-quick-start)
2. [Installation](#-installation)
3. [Core Concepts](#-core-concepts)
4. [CLI Commands Reference](#-cli-commands-reference)
5. [Analytics & Monitoring](#-analytics--monitoring)
6. [Advanced Features](#-advanced-features)
7. [Configuration Examples](#-configuration-examples)
8. [Best Practices](#-best-practices)
9. [Troubleshooting](#-troubleshooting)
10. [API Reference](#-api-reference)

## ⚡ Quick Start

### 1. Install API-Mocker
```bash
pip install api-mocker
```

### 2. Create Your First Mock API
```bash
# Initialize a new project
api-mocker init --name my-first-api

# Start the server
api-mocker start --config my-first-api/config/api-mock.yaml
```

### 3. Test Your API
```bash
curl http://127.0.0.1:8000/api/health
```

## 📦 Installation

### Prerequisites
- Python 3.8 or higher
- pip package manager

### Installation Options

#### From PyPI (Recommended)
```bash
pip install api-mocker
```

#### With Advanced Features
```bash
pip install api-mocker[advanced]
```

#### From Source
```bash
git clone https://github.com/Sherin-SEF-AI/api-mocker.git
cd api-mocker
pip install -e .
```

### Verify Installation
```bash
api-mocker --version
api-mocker --help
```

## 🎯 Core Concepts

### What is API-Mocker?
API-Mocker is a comprehensive API mocking solution that helps developers:
- **Accelerate Development** by eliminating API dependencies
- **Test Applications** with realistic mock data
- **Monitor Performance** with built-in analytics
- **Scale Applications** with enterprise features

### Key Features
- 🚀 **Fast Mock Server** - Production-ready FastAPI-based server
- 📊 **Real-time Analytics** - Beautiful dashboard with metrics
- 🛡️ **Rate Limiting** - Protect your APIs from abuse
- ⚡ **Caching System** - Improve performance with smart caching
- 🔐 **Authentication** - JWT-based security
- 📈 **Health Monitoring** - System health checks
- 🔄 **Import/Export** - OpenAPI, Postman, and more
- 🎯 **Plugin System** - Extensible architecture

## 🖥️ CLI Commands Reference

### Server Management

#### `start` - Start Mock Server
Start the API mock server with configuration.

```bash
api-mocker start [OPTIONS]
```

**Options:**
- `--config, -c TEXT` - Path to config file (YAML/JSON/TOML)
- `--host, -h TEXT` - Host to bind server [default: 127.0.0.1]
- `--port, -p INTEGER` - Port to bind server [default: 8000]
- `--reload` - Enable hot-reloading
- `--verbose, -v` - Enable verbose logging

**Examples:**
```bash
# Basic start
api-mocker start --config config.yaml

# Custom host and port
api-mocker start --config config.yaml --host 0.0.0.0 --port 9000

# With hot reload
api-mocker start --config config.yaml --reload --verbose
```

#### `init` - Initialize Project
Create a new API-Mocker project with templates.

```bash
api-mocker init [OPTIONS]
```

**Options:**
- `--name, -n TEXT` - Project name [default: my-api-mock]
- `--template, -t TEXT` - Template (basic, rest, graphql) [default: basic]
- `--output, -o TEXT` - Output directory [default: .]

**Examples:**
```bash
# Create basic project
api-mocker init --name my-api

# Create REST API project
api-mocker init --name my-rest-api --template rest

# Create in specific directory
api-mocker init --name my-api --output /path/to/projects
```

### Import & Export

#### `import-spec` - Import Specifications
Import OpenAPI/Swagger or Postman collections.

```bash
api-mocker import-spec FILE_PATH [OPTIONS]
```

**Options:**
- `--output, -o TEXT` - Output config file [default: api-mock.yaml]
- `--format, -f TEXT` - Input format (openapi, postman, auto) [default: auto]

**Examples:**
```bash
# Import OpenAPI spec
api-mocker import-spec swagger.json --output my-mock.yaml

# Import Postman collection
api-mocker import-spec collection.json --format postman

# Auto-detect format
api-mocker import-spec api-spec.yaml --output config.yaml
```

#### `export` - Export Configurations
Export mock configurations to different formats.

```bash
api-mocker export CONFIG [OPTIONS]
```

**Options:**
- `--format TEXT` - Export format (openapi, postman) [default: openapi]
- `--output TEXT` - Output file path

**Examples:**
```bash
# Export to OpenAPI
api-mocker export config.yaml --format openapi --output api-spec.yaml

# Export to Postman
api-mocker export config.yaml --format postman --output collection.json
```

### Recording & Replay

#### `record` - Record API Interactions
Record real API calls for later replay.

```bash
api-mocker record TARGET_URL [OPTIONS]
```

**Options:**
- `--output, -o TEXT` - Output file [default: recorded-requests.json]
- `--session, -s TEXT` - Session ID
- `--filter TEXT` - Regex pattern to filter paths

**Examples:**
```bash
# Record API calls
api-mocker record https://api.example.com --output recorded.json

# Record with session ID
api-mocker record https://api.example.com --session user-session

# Filter specific paths
api-mocker record https://api.example.com --filter "/api/users/*"
```

#### `replay` - Replay Recorded Requests
Replay recorded requests as mock responses.

```bash
api-mocker replay RECORDING_FILE [OPTIONS]
```

**Options:**
- `--host TEXT` - Host to bind replay server [default: 127.0.0.1]
- `--port INTEGER` - Port to bind replay server [default: 8000]

**Examples:**
```bash
# Replay recorded requests
api-mocker replay recorded.json

# Replay on custom port
api-mocker replay recorded.json --port 8001
```

### Testing & Monitoring

#### `test` - Run Tests
Run tests against mock server.

```bash
api-mocker test [OPTIONS]
```

**Options:**
- `--config TEXT` - Path to mock server config
- `--test-file TEXT` - Path to test file
- `--verbose, -v` - Verbose test output

**Examples:**
```bash
# Test with config
api-mocker test --config config.yaml

# Test with specific test file
api-mocker test --config config.yaml --test-file tests.yaml --verbose
```

#### `monitor` - Monitor Server
Monitor mock server requests in real-time.

```bash
api-mocker monitor [OPTIONS]
```

**Options:**
- `--host TEXT` - Mock server host [default: 127.0.0.1]
- `--port INTEGER` - Mock server port [default: 8000]
- `--interval FLOAT` - Monitoring interval [default: 1.0]

**Examples:**
```bash
# Monitor server
api-mocker monitor --host 127.0.0.1 --port 8000

# Monitor with custom interval
api-mocker monitor --interval 2.0
```

### Plugin Management

#### `plugins` - Manage Plugins
Manage API-Mocker plugins.

```bash
api-mocker plugins [OPTIONS]
```

**Options:**
- `--list, -l` - List all available plugins
- `--install TEXT` - Install a plugin
- `--configure TEXT` - Configure a plugin

**Examples:**
```bash
# List plugins
api-mocker plugins --list

# Install plugin
api-mocker plugins --install auth-plugin

# Configure plugin
api-mocker plugins --configure auth-plugin
```

## 📊 Analytics & Monitoring

### Overview
API-Mocker includes a comprehensive analytics system that tracks:
- Request/response metrics
- Performance data
- Error rates
- Feature usage
- System health

### Analytics Commands

#### `analytics dashboard` - Start Analytics Dashboard
Launch the real-time analytics dashboard.

```bash
api-mocker analytics dashboard
```

**Features:**
- Real-time metrics visualization
- Interactive charts (Chart.js)
- WebSocket updates
- Request/response tracking
- Performance monitoring

**Access:** http://127.0.0.1:8080

#### `analytics summary` - View Analytics Summary
Display analytics summary for specified time period.

```bash
api-mocker analytics summary [OPTIONS]
```

**Options:**
- `--hours INTEGER` - Time period in hours [default: 24]

**Examples:**
```bash
# Last 24 hours
api-mocker analytics summary

# Last 48 hours
api-mocker analytics summary --hours 48

# Last week
api-mocker analytics summary --hours 168
```

#### `analytics export` - Export Analytics Data
Export analytics data to various formats.

```bash
api-mocker analytics export [OPTIONS]
```

**Options:**
- `--output TEXT` - Output file path
- `--format TEXT` - Export format (json, csv) [default: json]

**Examples:**
```bash
# Export to JSON
api-mocker analytics export --output analytics.json

# Export to CSV
api-mocker analytics export --format csv --output analytics.csv

# Auto-named export
api-mocker analytics export
```

### Analytics Dashboard Features

#### Real-time Metrics
- **Uptime** - Server uptime tracking
- **Total Requests** - Request count
- **Requests/Minute** - Throughput
- **Average Response Time** - Performance
- **Error Rate** - Reliability
- **Memory Usage** - System health
- **CPU Usage** - System performance

#### Visualizations
- **Request Methods Distribution** - Pie chart
- **Status Codes Distribution** - Bar chart
- **Popular Endpoints** - Top endpoints
- **Slowest Endpoints** - Performance bottlenecks

#### Data Export
- **JSON Format** - For external analysis
- **CSV Format** - For spreadsheet analysis
- **Real-time Updates** - Live data streaming

## 🛡️ Advanced Features

### Overview
Enterprise-grade features for production deployments:
- Rate limiting
- Caching system
- Authentication
- Health monitoring
- Performance optimization

### Advanced Commands

#### `advanced rate-limit` - Configure Rate Limiting
Set up rate limiting to protect your APIs.

```bash
api-mocker advanced rate-limit [OPTIONS]
```

**Options:**
- `--config TEXT` - Configuration file path
- `--enable/--disable` - Enable or disable feature

**Examples:**
```bash
# Basic rate limiting
api-mocker advanced rate-limit

# With config file
api-mocker advanced rate-limit --config rate-limit.yaml

# Disable rate limiting
api-mocker advanced rate-limit --disable
```

**Configuration Example:**
```yaml
rate_limit:
  enabled: true
  requests_per_minute: 60
  requests_per_hour: 1000
  burst_size: 10
  window_size: 60
```

#### `advanced cache` - Configure Caching
Set up caching system for improved performance.

```bash
api-mocker advanced cache [OPTIONS]
```

**Options:**
- `--config TEXT` - Configuration file path
- `--enable/--disable` - Enable or disable feature

**Examples:**
```bash
# Basic caching
api-mocker advanced cache

# With config file
api-mocker advanced cache --config cache.yaml

# Disable caching
api-mocker advanced cache --disable
```

**Configuration Example:**
```yaml
cache:
  enabled: true
  ttl_seconds: 300
  max_size: 1000
  strategy: "lru"
```

#### `advanced auth` - Configure Authentication
Set up JWT-based authentication.

```bash
api-mocker advanced auth [OPTIONS]
```

**Options:**
- `--config TEXT` - Configuration file path
- `--enable/--disable` - Enable or disable feature

**Examples:**
```bash
# Basic authentication
api-mocker advanced auth

# With config file
api-mocker advanced auth --config auth.yaml

# Disable authentication
api-mocker advanced auth --disable
```

**Configuration Example:**
```yaml
auth:
  enabled: true
  secret_key: "your-secret-key"
  algorithm: "HS256"
  token_expiry_hours: 24
  require_auth:
    - "/api/admin/*"
    - "/api/users/*"
```

#### `advanced health` - Run Health Checks
Perform system health checks.

```bash
api-mocker advanced health
```

**Checks Performed:**
- **Database** - SQLite connectivity
- **Memory** - Memory usage (< 90%)
- **Disk** - Disk space (< 95%)

**Example Output:**
```
🏥 Running health checks...
Health Check Results 
┏━━━━━━━━━━┳━━━━━━━━┓
┃ Check    ┃ Status ┃
┡━━━━━━━━━━╇━━━━━━━━┩
│ database │ ✓      │
│ memory   │ ✓      │
│ disk     │ ✓      │
└──────────┴────────┘
Overall status: healthy
```

## 📝 Configuration Examples

### Basic Configuration
```yaml
# basic-config.yaml
server:
  host: "127.0.0.1"
  port: 8000
  debug: true

routes:
  - method: "GET"
    path: "/api/health"
    response:
      status_code: 200
      body:
        status: "healthy"
        timestamp: "{{ datetime.now().isoformat() }}"
        version: "1.0.0"

  - method: "GET"
    path: "/api/users"
    response:
      status_code: 200
      body:
        users:
          - id: 1
            name: "John Doe"
            email: "john@example.com"
          - id: 2
            name: "Jane Smith"
            email: "jane@example.com"
```

### Advanced Configuration
```yaml
# advanced-config.yaml
server:
  host: "127.0.0.1"
  port: 8000
  debug: true

# Rate limiting
rate_limit:
  enabled: true
  requests_per_minute: 60
  requests_per_hour: 1000

# Caching
cache:
  enabled: true
  ttl_seconds: 300
  max_size: 1000

# Authentication
auth:
  enabled: true
  secret_key: "your-secret-key"
  require_auth:
    - "/api/admin/*"

routes:
  - method: "GET"
    path: "/api/public/health"
    response:
      status_code: 200
      body:
        status: "healthy"

  - method: "GET"
    path: "/api/admin/users"
    response:
      status_code: 200
      body:
        users: []
```

### Analytics Configuration
```yaml
# analytics-config.yaml
analytics:
  enabled: true
  database_path: "analytics.db"
  retention_days: 30
  
  dashboard:
    enabled: true
    port: 8080
    host: "127.0.0.1"
    
  metrics:
    track_requests: true
    track_response_times: true
    track_error_rates: true
```

## 🎯 Best Practices

### 1. Project Structure
```
my-api-project/
├── config/
│   ├── api-mock.yaml
│   ├── analytics-config.yaml
│   └── advanced-features.yaml
├── tests/
│   └── test-config.yaml
├── recordings/
│   └── recorded-requests.json
└── README.md
```

### 2. Configuration Management
- Use separate config files for different environments
- Version control your configurations
- Use environment variables for sensitive data
- Document your mock API specifications

### 3. Testing Strategy
- Create comprehensive test suites
- Use realistic mock data
- Test error scenarios
- Monitor performance metrics

### 4. Production Deployment
- Enable rate limiting
- Configure authentication
- Set up monitoring
- Use caching for performance
- Regular health checks

### 5. Analytics Usage
- Monitor request patterns
- Track performance bottlenecks
- Analyze error rates
- Export data for external analysis

## 🔧 Troubleshooting

### Common Issues

#### Server Won't Start
```bash
# Check if port is in use
lsof -i :8000

# Try different port
api-mocker start --port 8001
```

#### Configuration Errors
```bash
# Validate YAML syntax
python -c "import yaml; yaml.safe_load(open('config.yaml'))"

# Check config file
api-mocker start --config config.yaml --verbose
```

#### Analytics Issues
```bash
# Check database permissions
ls -la api_mocker_analytics.db

# Reset analytics
rm api_mocker_analytics.db
```

#### Performance Issues
```bash
# Check system resources
api-mocker advanced health

# Monitor memory usage
api-mocker analytics dashboard
```

### Debug Mode
```bash
# Enable verbose logging
api-mocker start --config config.yaml --verbose

# Check logs
tail -f api-mocker.log
```

### Getting Help
```bash
# Command help
api-mocker <command> --help

# General help
api-mocker --help
```

## 📚 API Reference

### Python API
```python
from api_mocker import MockServer
from api_mocker.analytics import AnalyticsManager
from api_mocker.advanced import AdvancedFeatures

# Create server
server = MockServer(config_path="config.yaml")

# Start server
server.start(host="127.0.0.1", port=8000)

# Analytics
analytics = AnalyticsManager()
summary = analytics.get_analytics_summary(hours=24)

# Advanced features
advanced = AdvancedFeatures()
```

### Configuration Schema
```yaml
server:
  host: string          # Server host
  port: integer         # Server port
  debug: boolean        # Debug mode

routes:
  - method: string      # HTTP method
    path: string        # URL path
    response:
      status_code: integer
      body: object      # Response body
      headers: object   # Response headers

rate_limit:
  enabled: boolean
  requests_per_minute: integer
  requests_per_hour: integer

cache:
  enabled: boolean
  ttl_seconds: integer
  max_size: integer

auth:
  enabled: boolean
  secret_key: string
  require_auth: array
```

## 🚀 Getting Started Checklist

- [ ] Install API-Mocker: `pip install api-mocker`
- [ ] Initialize project: `api-mocker init --name my-api`
- [ ] Create configuration: Edit `config/api-mock.yaml`
- [ ] Start server: `api-mocker start --config config/api-mock.yaml`
- [ ] Test endpoints: `curl http://127.0.0.1:8000/api/health`
- [ ] View analytics: `api-mocker analytics dashboard`
- [ ] Configure advanced features: `api-mocker advanced health`
- [ ] Run tests: `api-mocker test --config config/api-mock.yaml`

## 📞 Support

- **Documentation**: [GitHub Wiki](https://github.com/Sherin-SEF-AI/api-mocker/wiki)
- **Issues**: [GitHub Issues](https://github.com/Sherin-SEF-AI/api-mocker/issues)
- **Discussions**: [GitHub Discussions](https://github.com/Sherin-SEF-AI/api-mocker/discussions)
- **Email**: sherin.joseph2217@gmail.com

---

**Made with ❤️ by the API-Mocker Community** 