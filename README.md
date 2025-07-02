# api-mocker

The industry-standard, production-ready, free API mocking and development acceleration tool.

## 🚀 Project Mission
Create the most comprehensive, user-friendly, and feature-rich API mocking solution to eliminate API dependency bottlenecks and accelerate development workflows for all developers.

## ✨ Features
- **Robust HTTP mock server** supporting all HTTP methods (GET, POST, PUT, DELETE, PATCH, etc.)
- **Dynamic and static response generation** with template support
- **OpenAPI/Swagger/Postman import/export** for seamless integration
- **CLI and Python API interfaces** for maximum flexibility
- **Hot-reloading** with config file support (JSON/YAML/TOML)
- **Request recording, replay, and proxy mode** for real API simulation
- **Schema-based data generation** and validation
- **Advanced routing, middleware, and authentication simulation**
- **Data persistence, state management, and in-memory DB**
- **Performance, monitoring, and analytics tools**
- **Framework integrations** (Django, Flask, FastAPI, Node.js, etc.)
- **Docker, CI/CD, and cloud deployment support**
- **Team collaboration and plugin architecture**

## 📦 Installation

### From PyPI (Recommended)
```bash
pip install api-mocker
```

### From Source
```bash
git clone https://github.com/your-username/api-mocker.git
cd api-mocker
pip install -e .
```

## 🚀 Quick Start

### 1. Basic Usage
Create a simple mock configuration:

```yaml
# simple-mock.yaml
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

  - method: "POST"
    path: "/api/users"
    response:
      status_code: 201
      body:
        id: "{{ random.randint(1000, 9999) }}"
        message: "User created successfully"
```

Start the mock server:
```bash
api-mocker start --config simple-mock.yaml
```

### 2. Test Your Mock API
```bash
# Test health endpoint
curl http://127.0.0.1:8000/api/health

# Test users endpoint
curl http://127.0.0.1:8000/api/users

# Create a new user
curl -X POST http://127.0.0.1:8000/api/users \
  -H "Content-Type: application/json" \
  -d '{"name": "New User", "email": "new@example.com"}'
```

## 📚 Complete Documentation

### CLI Commands

#### Start Server
```bash
# Basic start
api-mocker start --config config.yaml

# With custom host and port
api-mocker start --config config.yaml --host 0.0.0.0 --port 9000

# With verbose logging
api-mocker start --config config.yaml --verbose

# With hot reload
api-mocker start --config config.yaml --reload
```

#### Import Specifications
```bash
# Import OpenAPI/Swagger spec
api-mocker import openapi --file swagger.json --output mock-config.yaml

# Import Postman collection
api-mocker import postman --file collection.json --output mock-config.yaml

# Import with custom base URL
api-mocker import openapi --file api-spec.yaml --base-url https://api.example.com
```

#### Record and Replay
```bash
# Record real API calls
api-mocker record --target https://api.example.com --output recorded.yaml

# Replay recorded requests
api-mocker replay --file recorded.yaml --config mock-config.yaml
```

#### Plugin Management
```bash
# List available plugins
api-mocker plugins list

# Install plugin
api-mocker plugins install auth-plugin

# Enable plugin
api-mocker plugins enable auth-plugin
```

#### Testing
```bash
# Run test suite
api-mocker test --config mock-config.yaml --test-file tests.yaml

# Test specific endpoint
api-mocker test --config mock-config.yaml --endpoint "/api/users"
```

#### Monitoring
```bash
# Start monitoring dashboard
api-mocker monitor --config mock-config.yaml --port 8080

# Export metrics
api-mocker monitor --config mock-config.yaml --export metrics.json
```

#### Export
```bash
# Export to OpenAPI
api-mocker export openapi --config mock-config.yaml --output api-spec.yaml

# Export to Postman
api-mocker export postman --config mock-config.yaml --output collection.json
```

#### Project Management
```bash
# Initialize new project
api-mocker init --name my-api-project

# Create from template
api-mocker init --template rest-api --name my-rest-api
```

### Configuration Examples

#### Advanced Mock Configuration
```yaml
# advanced-mock.yaml
server:
  host: "127.0.0.1"
  port: 8000
  debug: true
  cors:
    enabled: true
    origins: ["http://localhost:3000", "https://myapp.com"]
  rate_limit:
    enabled: true
    requests_per_minute: 100

middleware:
  - name: "auth"
    config:
      type: "bearer"
      tokens: ["secret-token-123"]
  - name: "logging"
    config:
      level: "INFO"
      format: "json"

routes:
  - method: "GET"
    path: "/api/users/{user_id}"
    auth_required: true
    response:
      status_code: 200
      headers:
        Content-Type: "application/json"
      body:
        id: "{{ params.user_id }}"
        name: "{{ fake.name() }}"
        email: "{{ fake.email() }}"
        created_at: "{{ datetime.now().isoformat() }}"

  - method: "POST"
    path: "/api/users"
    auth_required: true
    validation:
      schema:
        type: "object"
        required: ["name", "email"]
        properties:
          name:
            type: "string"
            minLength: 2
          email:
            type: "string"
            format: "email"
    response:
      status_code: 201
      body:
        id: "{{ random.randint(1000, 9999) }}"
        name: "{{ request.body.name }}"
        email: "{{ request.body.email }}"
        created_at: "{{ datetime.now().isoformat() }}"

  - method: "GET"
    path: "/api/search"
    response:
      status_code: 200
      body:
        results:
          - "{{ fake.sentence() }}"
          - "{{ fake.sentence() }}"
          - "{{ fake.sentence() }}"
        total: "{{ random.randint(10, 100) }}"
        page: "{{ request.query.page or 1 }}"

database:
  type: "sqlite"
  path: "mock_data.db"
  tables:
    users:
      - id: 1
        name: "John Doe"
        email: "john@example.com"
      - id: 2
        name: "Jane Smith"
        email: "jane@example.com"

plugins:
  - name: "faker"
    config:
      locale: "en_US"
  - name: "jwt"
    config:
      secret: "your-secret-key"
```

#### Testing Configuration
```yaml
# tests.yaml
tests:
  - name: "Health Check"
    request:
      method: "GET"
      url: "/api/health"
    expected:
      status_code: 200
      body:
        status: "healthy"

  - name: "Create User"
    request:
      method: "POST"
      url: "/api/users"
      headers:
        Authorization: "Bearer secret-token-123"
        Content-Type: "application/json"
      body:
        name: "Test User"
        email: "test@example.com"
    expected:
      status_code: 201
      body:
        name: "Test User"
        email: "test@example.com"

  - name: "Get User"
    request:
      method: "GET"
      url: "/api/users/1"
      headers:
        Authorization: "Bearer secret-token-123"
    expected:
      status_code: 200
      body:
        id: "1"
```

### Python API Usage

#### Basic Server
```python
from api_mocker import MockServer

# Create server from config file
server = MockServer(config_path="config.yaml")
server.start()

# Or create server programmatically
from api_mocker import MockServer, Route, Response

routes = [
    Route(
        method="GET",
        path="/api/health",
        response=Response(
            status_code=200,
            body={"status": "healthy"}
        )
    )
]

server = MockServer(routes=routes)
server.start()
```

#### Advanced Usage
```python
from api_mocker import MockServer, Route, Response, Middleware
from api_mocker.plugins import FakerPlugin

# Create custom middleware
class CustomMiddleware(Middleware):
    def process_request(self, request):
        print(f"Processing request: {request.method} {request.path}")
        return request

    def process_response(self, response):
        response.headers["X-Custom-Header"] = "processed"
        return response

# Create server with plugins and middleware
server = MockServer(
    config_path="config.yaml",
    middleware=[CustomMiddleware()],
    plugins=[FakerPlugin()]
)

# Add routes dynamically
server.add_route(
    Route(
        method="GET",
        path="/api/dynamic",
        response=Response(
            status_code=200,
            body={"message": "Dynamic route added!"}
        )
    )
)

server.start()
```

#### Testing with Python
```python
from api_mocker import MockServer
import requests

# Start server
server = MockServer(config_path="test-config.yaml")
server.start()

# Test endpoints
response = requests.get("http://127.0.0.1:8000/api/health")
assert response.status_code == 200
assert response.json()["status"] == "healthy"

# Stop server
server.stop()
```

### Template Variables

api-mocker supports dynamic template variables in responses:

```yaml
routes:
  - method: "GET"
    path: "/api/dynamic"
    response:
      status_code: 200
      body:
        # Request information
        method: "{{ request.method }}"
        path: "{{ request.path }}"
        headers: "{{ request.headers }}"
        query: "{{ request.query }}"
        
        # URL parameters
        user_id: "{{ params.user_id }}"
        
        # Random data
        random_id: "{{ random.randint(1, 1000) }}"
        random_name: "{{ fake.name() }}"
        random_email: "{{ fake.email() }}"
        
        # Date/time
        timestamp: "{{ datetime.now().isoformat() }}"
        date: "{{ datetime.now().strftime('%Y-%m-%d') }}"
        
        # Request body (for POST/PUT)
        received_data: "{{ request.body }}"
```

### Authentication Examples

#### Bearer Token
```yaml
middleware:
  - name: "auth"
    config:
      type: "bearer"
      tokens: ["secret-token-123", "another-token"]

routes:
  - method: "GET"
    path: "/api/protected"
    auth_required: true
    response:
      status_code: 200
      body:
        message: "Access granted"
```

#### API Key
```yaml
middleware:
  - name: "auth"
    config:
      type: "api_key"
      header: "X-API-Key"
      keys: ["api-key-123", "api-key-456"]
```

#### Basic Auth
```yaml
middleware:
  - name: "auth"
    config:
      type: "basic"
      users:
        admin: "password123"
        user: "password456"
```

### Database Integration

```yaml
database:
  type: "sqlite"
  path: "mock_data.db"
  tables:
    users:
      - id: 1
        name: "John Doe"
        email: "john@example.com"
        role: "admin"
      - id: 2
        name: "Jane Smith"
        email: "jane@example.com"
        role: "user"

routes:
  - method: "GET"
    path: "/api/users"
    response:
      status_code: 200
      body:
        users: "{{ db.query('SELECT * FROM users') }}"

  - method: "GET"
    path: "/api/users/{user_id}"
    response:
      status_code: 200
      body:
        user: "{{ db.query_one('SELECT * FROM users WHERE id = ?', params.user_id) }}"
```

### Docker Usage

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["api-mocker", "start", "--config", "config.yaml", "--host", "0.0.0.0"]
```

```yaml
# docker-compose.yml
version: '3.8'
services:
  api-mocker:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - ./config:/app/config
    environment:
      - DEBUG=true
```

### CI/CD Integration

```yaml
# .github/workflows/test.yml
name: Test API Mocks

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install api-mocker
          pip install pytest requests
      
      - name: Run tests
        run: |
          api-mocker test --config config.yaml --test-file tests.yaml
```

## 🔧 Development

### Setup Development Environment
```bash
git clone https://github.com/your-username/api-mocker.git
cd api-mocker
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -e ".[dev]"
```

### Run Tests
```bash
pytest tests/
```

### Build Package
```bash
python -m build
```

## 🤝 Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🆘 Support

- 📖 [Documentation](https://github.com/your-username/api-mocker#documentation)
- 🐛 [Issue Tracker](https://github.com/your-username/api-mocker/issues)
- 💬 [Discussions](https://github.com/your-username/api-mocker/discussions)

---

© 2025 sherin joseph roy 