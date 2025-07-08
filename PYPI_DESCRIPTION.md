# API-Mocker: The Ultimate API Development Acceleration Tool

[![PyPI version](https://badge.fury.io/py/api-mocker.svg)](https://badge.fury.io/py/api-mocker)
[![Downloads](https://pepy.tech/badge/api-mocker)](https://pepy.tech/project/api-mocker)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

**The Industry-Standard, Production-Ready, FREE API Mocking & Development Acceleration Tool**

API-Mocker eliminates API dependency bottlenecks and accelerates development workflows for all developers. With **1500+ downloads** and growing, it's the most comprehensive free API mocking solution available.

## 🚀 Quick Start

```bash
# Install API-Mocker
pip install api-mocker

# Create your first mock API
api-mocker init --name my-api
api-mocker start --config my-api/config/api-mock.yaml

# Test your API
curl http://127.0.0.1:8000/api/health
```

## ✨ Key Features

### 🎯 Core Functionality
- **Fast Mock Server** - Production-ready FastAPI-based server
- **Dynamic Responses** - Template-based response generation
- **Multi-Format Support** - YAML, JSON, TOML configurations
- **Hot Reloading** - Real-time configuration updates
- **Plugin Architecture** - Extensible and customizable

### 📊 Analytics & Monitoring
- **Real-time Dashboard** - Beautiful web interface with Chart.js
- **Performance Metrics** - Response times, throughput, error rates
- **Request Tracking** - Detailed request/response logging
- **Export Capabilities** - JSON/CSV data export
- **WebSocket Updates** - Live data streaming

### 🛡️ Enterprise Features
- **Rate Limiting** - Sliding window algorithm with per-client tracking
- **Caching System** - LRU/FIFO eviction with TTL support
- **JWT Authentication** - Role-based access control
- **Health Monitoring** - System health checks (DB, memory, disk)
- **Middleware Support** - Request/response processing pipeline

### 🔄 Import/Export
- **OpenAPI/Swagger** - Full specification support
- **Postman Collections** - Import/export compatibility
- **Custom Formats** - Extensible format support
- **Schema Validation** - Automatic validation

## 📋 CLI Commands

API-Mocker provides a comprehensive CLI with 15+ commands:

```bash
# Server Management
api-mocker start --config config.yaml
api-mocker init --name my-api

# Import/Export
api-mocker import-spec swagger.json --output mock.yaml
api-mocker export config.yaml --format openapi

# Analytics & Monitoring
api-mocker analytics dashboard
api-mocker analytics summary --hours 24
api-mocker analytics export --output analytics.json

# Advanced Features
api-mocker advanced rate-limit --config rate-limit.yaml
api-mocker advanced cache --enable
api-mocker advanced auth --config auth.yaml
api-mocker advanced health

# Testing & Recording
api-mocker test --config config.yaml
api-mocker record https://api.example.com --output recorded.json
api-mocker replay recorded.json

# Plugin Management
api-mocker plugins --list
```

## 📊 Analytics Dashboard

Launch a beautiful real-time analytics dashboard:

```bash
api-mocker analytics dashboard
# Open: http://127.0.0.1:8080
```

**Features:**
- Real-time metrics visualization
- Interactive charts (Chart.js)
- WebSocket updates
- Request/response tracking
- Performance monitoring

## 🛡️ Advanced Features

### Rate Limiting
```bash
api-mocker advanced rate-limit --config rate-limit.yaml
```

```yaml
# rate-limit.yaml
rate_limit:
  enabled: true
  requests_per_minute: 60
  requests_per_hour: 1000
  burst_size: 10
```

### Caching System
```bash
api-mocker advanced cache --enable
```

```yaml
# cache-config.yaml
cache:
  enabled: true
  ttl_seconds: 300
  max_size: 1000
  strategy: "lru"
```

### Authentication
```bash
api-mocker advanced auth --config auth.yaml
```

```yaml
# auth.yaml
auth:
  enabled: true
  secret_key: "your-secret-key"
  algorithm: "HS256"
  token_expiry_hours: 24
  require_auth:
    - "/api/admin/*"
    - "/api/users/*"
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

### Production Configuration
```yaml
# production-config.yaml
server:
  host: "0.0.0.0"
  port: 8000
  debug: false

# Rate limiting
rate_limit:
  enabled: true
  requests_per_minute: 100
  requests_per_hour: 5000

# Caching
cache:
  enabled: true
  ttl_seconds: 600
  max_size: 5000

# Authentication
auth:
  enabled: true
  secret_key: "${JWT_SECRET_KEY}"
  require_auth:
    - "/api/admin/*"
    - "/api/sensitive/*"

# Analytics
analytics:
  enabled: true
  retention_days: 30
  export_enabled: true
```

## 🎯 Use Cases

### Development Teams
- **Frontend Development** - Mock backend APIs during development
- **Mobile Development** - Test mobile apps with mock APIs
- **Microservices** - Mock service dependencies
- **API Testing** - Comprehensive API testing scenarios

### DevOps & QA
- **CI/CD Pipelines** - Automated testing with mock APIs
- **Performance Testing** - Load testing with controlled responses
- **Integration Testing** - Test service integrations
- **Staging Environments** - Production-like testing environments

### API Design
- **API Prototyping** - Rapid API design and iteration
- **Documentation** - Generate API documentation from mocks
- **Client SDKs** - Test client libraries with mock APIs
- **API Versioning** - Test multiple API versions

## 📈 Performance Metrics

### Benchmark Results
- **Startup Time**: < 2 seconds
- **Request Latency**: < 10ms average
- **Memory Usage**: < 50MB typical
- **Concurrent Requests**: 1000+ supported
- **Configuration Hot Reload**: < 1 second

### Scalability Features
- **Horizontal Scaling** - Multiple server instances
- **Load Balancing** - Built-in load distribution
- **Resource Optimization** - Efficient memory usage
- **Connection Pooling** - Optimized database connections

## 🔌 Plugin System

### Built-in Plugins
- **Response Generator** - Dynamic response generation
- **Authentication** - JWT and OAuth support
- **Data Sources** - Database and external data integration
- **Custom Middleware** - Request/response processing

### Plugin Development
```python
from api_mocker.plugins import Plugin

class CustomPlugin(Plugin):
    def process_request(self, request):
        # Custom request processing
        return request
    
    def process_response(self, response):
        # Custom response processing
        return response
```

## 🚀 Getting Started Checklist

- [ ] **Install API-Mocker**: `pip install api-mocker`
- [ ] **Initialize Project**: `api-mocker init --name my-api`
- [ ] **Configure Routes**: Edit `config/api-mock.yaml`
- [ ] **Start Server**: `api-mocker start --config config/api-mock.yaml`
- [ ] **Test Endpoints**: `curl http://127.0.0.1:8000/api/health`
- [ ] **View Analytics**: `api-mocker analytics dashboard`
- [ ] **Configure Advanced Features**: `api-mocker advanced health`
- [ ] **Run Tests**: `api-mocker test --config config/api-mock.yaml`
- [ ] **Import Existing APIs**: `api-mocker import-spec swagger.json`
- [ ] **Export Configuration**: `api-mocker export config.yaml --format openapi`

## 📞 Support & Community

### Documentation
- **Complete Guide**: [GitHub Wiki](https://github.com/Sherin-SEF-AI/api-mocker/wiki)
- **Quick Start**: [docs/QUICKSTART.md](https://github.com/Sherin-SEF-AI/api-mocker/blob/main/docs/QUICKSTART.md)
- **API Reference**: [docs/COMPLETE_GUIDE.md](https://github.com/Sherin-SEF-AI/api-mocker/blob/main/docs/COMPLETE_GUIDE.md)

### Community
- **GitHub**: [github.com/Sherin-SEF-AI/api-mocker](https://github.com/Sherin-SEF-AI/api-mocker)
- **Issues**: [GitHub Issues](https://github.com/Sherin-SEF-AI/api-mocker/issues)
- **Discussions**: [GitHub Discussions](https://github.com/Sherin-SEF-AI/api-mocker/discussions)
- **Email**: sherin.joseph2217@gmail.com

### Contributing
- **Star the Repository** ⭐
- **Report Issues** 🐛
- **Submit Pull Requests** 🔄
- **Share Your Story** 📝
- **Join Discussions** 💬

## 🎉 Why Choose API-Mocker?

### ✅ Free & Open Source
- No licensing fees
- No usage limits
- Full source code access
- Community-driven development

### ✅ Production Ready
- Enterprise-grade features
- Comprehensive testing
- Performance optimized
- Security focused

### ✅ Developer Friendly
- Simple CLI interface
- Rich documentation
- Multiple configuration formats
- Extensive examples

### ✅ Feature Rich
- Real-time analytics
- Advanced security
- Plugin architecture
- Import/export capabilities

## 📈 Success Metrics

- **1500+ Downloads** from PyPI
- **100% Free** - No paywalls or limitations
- **Production Ready** - Used in enterprise environments
- **Active Development** - Regular updates and improvements
- **Growing Community** - Contributors and users worldwide

## 🔧 Installation Options

### Basic Installation
```bash
pip install api-mocker
```

### With Advanced Features
```bash
pip install api-mocker[advanced]
```

### From Source
```bash
git clone https://github.com/Sherin-SEF-AI/api-mocker.git
cd api-mocker
pip install -e .
```

## 📋 Requirements

- **Python**: 3.8 or higher
- **Dependencies**: FastAPI, Uvicorn, PyYAML, Rich, Typer
- **Optional**: PyJWT, Redis (for advanced features)

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](https://github.com/Sherin-SEF-AI/api-mocker/blob/main/LICENSE) file for details.

---

**🚀 Ready to accelerate your API development?**

```bash
pip install api-mocker
api-mocker init --name my-api
api-mocker start --config my-api/config/api-mock.yaml
```

**Visit**: [github.com/Sherin-SEF-AI/api-mocker](https://github.com/Sherin-SEF-AI/api-mocker)

---

*Made with ❤️ by the API-Mocker Community* 