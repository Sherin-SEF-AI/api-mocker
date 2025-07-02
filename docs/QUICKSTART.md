# api-mocker Quickstart Guide

This guide will help you get started with api-mocker in minutes. You'll learn how to create mock APIs, test them, and integrate them into your development workflow.

## 🚀 Installation

### Prerequisites
- Python 3.8 or higher
- pip (Python package installer)

### Install api-mocker
```bash
pip install api-mocker
```

Verify installation:
```bash
api-mocker --version
```

## 📝 Your First Mock API

### Step 1: Create a Basic Configuration

Create a file called `my-first-api.yaml`:

```yaml
server:
  host: "127.0.0.1"
  port: 8000
  debug: true

routes:
  - method: "GET"
    path: "/"
    response:
      status_code: 200
      body:
        message: "Welcome to my first mock API!"
        timestamp: "{{ datetime.now().isoformat() }}"

  - method: "GET"
    path: "/api/health"
    response:
      status_code: 200
      body:
        status: "healthy"
        uptime: "{{ random.randint(1, 1000) }} seconds"

  - method: "GET"
    path: "/api/users"
    response:
      status_code: 200
      body:
        users:
          - id: 1
            name: "Alice Johnson"
            email: "alice@example.com"
          - id: 2
            name: "Bob Smith"
            email: "bob@example.com"
        total: 2
```

### Step 2: Start the Mock Server

```bash
api-mocker start --config my-first-api.yaml
```

You should see output like:
```
✓ Mock server starting on http://127.0.0.1:8000
📁 Using config: my-first-api.yaml
Starting api-mocker server on http://127.0.0.1:8000
Loaded 3 routes
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
```

### Step 3: Test Your API

Open a new terminal and test your endpoints:

```bash
# Test the root endpoint
curl http://127.0.0.1:8000/

# Test the health endpoint
curl http://127.0.0.1:8000/api/health

# Test the users endpoint
curl http://127.0.0.1:8000/api/users
```

Expected responses:
```json
// GET /
{
  "message": "Welcome to my first mock API!",
  "timestamp": "2025-01-15T10:30:45.123456"
}

// GET /api/health
{
  "status": "healthy",
  "uptime": "742 seconds"
}

// GET /api/users
{
  "users": [
    {
      "id": 1,
      "name": "Alice Johnson",
      "email": "alice@example.com"
    },
    {
      "id": 2,
      "name": "Bob Smith",
      "email": "bob@example.com"
    }
  ],
  "total": 2
}
```

## 🔧 Advanced Examples

### Example 1: RESTful API with CRUD Operations

Create `rest-api.yaml`:

```yaml
server:
  host: "127.0.0.1"
  port: 8000
  debug: true

database:
  type: "sqlite"
  path: "mock_data.db"
  tables:
    products:
      - id: 1
        name: "Laptop"
        price: 999.99
        category: "Electronics"
      - id: 2
        name: "Coffee Mug"
        price: 12.99
        category: "Kitchen"

routes:
  # GET all products
  - method: "GET"
    path: "/api/products"
    response:
      status_code: 200
      body:
        products: "{{ db.query('SELECT * FROM products') }}"
        total: "{{ len(db.query('SELECT * FROM products')) }}"

  # GET single product
  - method: "GET"
    path: "/api/products/{product_id}"
    response:
      status_code: 200
      body:
        product: "{{ db.query_one('SELECT * FROM products WHERE id = ?', params.product_id) }}"

  # POST new product
  - method: "POST"
    path: "/api/products"
    validation:
      schema:
        type: "object"
        required: ["name", "price"]
        properties:
          name:
            type: "string"
            minLength: 1
          price:
            type: "number"
            minimum: 0
          category:
            type: "string"
    response:
      status_code: 201
      body:
        id: "{{ random.randint(1000, 9999) }}"
        name: "{{ request.body.name }}"
        price: "{{ request.body.price }}"
        category: "{{ request.body.category or 'General' }}"
        created_at: "{{ datetime.now().isoformat() }}"

  # PUT update product
  - method: "PUT"
    path: "/api/products/{product_id}"
    response:
      status_code: 200
      body:
        id: "{{ params.product_id }}"
        name: "{{ request.body.name }}"
        price: "{{ request.body.price }}"
        updated_at: "{{ datetime.now().isoformat() }}"

  # DELETE product
  - method: "DELETE"
    path: "/api/products/{product_id}"
    response:
      status_code: 204
      body: null
```

Test the REST API:

```bash
# Start the server
api-mocker start --config rest-api.yaml

# In another terminal, test the endpoints:
curl http://127.0.0.1:8000/api/products

curl http://127.0.0.1:8000/api/products/1

curl -X POST http://127.0.0.1:8000/api/products \
  -H "Content-Type: application/json" \
  -d '{"name": "New Product", "price": 29.99, "category": "Test"}'

curl -X PUT http://127.0.0.1:8000/api/products/1 \
  -H "Content-Type: application/json" \
  -d '{"name": "Updated Laptop", "price": 1099.99}'

curl -X DELETE http://127.0.0.1:8000/api/products/1
```

### Example 2: Authentication and Protected Routes

Create `auth-api.yaml`:

```yaml
server:
  host: "127.0.0.1"
  port: 8000
  debug: true

middleware:
  - name: "auth"
    config:
      type: "bearer"
      tokens: ["secret-token-123", "admin-token-456"]

routes:
  # Public endpoint
  - method: "GET"
    path: "/api/public"
    response:
      status_code: 200
      body:
        message: "This is a public endpoint"
        timestamp: "{{ datetime.now().isoformat() }}"

  # Protected endpoint
  - method: "GET"
    path: "/api/protected"
    auth_required: true
    response:
      status_code: 200
      body:
        message: "Access granted to protected resource"
        user_id: "{{ random.randint(1, 100) }}"
        permissions: ["read", "write"]

  # Admin endpoint
  - method: "GET"
    path: "/api/admin"
    auth_required: true
    response:
      status_code: 200
      body:
        message: "Admin access granted"
        admin_data: "{{ fake.text() }}"
        system_status: "operational"
```

Test authentication:

```bash
# Start server
api-mocker start --config auth-api.yaml

# Test public endpoint (no auth needed)
curl http://127.0.0.1:8000/api/public

# Test protected endpoint (auth required)
curl http://127.0.0.1:8000/api/protected
# This will return 401 Unauthorized

# Test with valid token
curl -H "Authorization: Bearer secret-token-123" \
  http://127.0.0.1:8000/api/protected

# Test admin endpoint
curl -H "Authorization: Bearer admin-token-456" \
  http://127.0.0.1:8000/api/admin
```

### Example 3: Dynamic Responses with Templates

Create `dynamic-api.yaml`:

```yaml
server:
  host: "127.0.0.1"
  port: 8000
  debug: true

plugins:
  - name: "faker"
    config:
      locale: "en_US"

routes:
  # Dynamic user generation
  - method: "GET"
    path: "/api/users/random"
    response:
      status_code: 200
      body:
        id: "{{ random.randint(1, 10000) }}"
        name: "{{ fake.name() }}"
        email: "{{ fake.email() }}"
        phone: "{{ fake.phone_number() }}"
        address:
          street: "{{ fake.street_address() }}"
          city: "{{ fake.city() }}"
          state: "{{ fake.state() }}"
          zipcode: "{{ fake.zipcode() }}"
        created_at: "{{ datetime.now().isoformat() }}"

  # Search with query parameters
  - method: "GET"
    path: "/api/search"
    response:
      status_code: 200
      body:
        query: "{{ request.query.q or 'default' }}"
        page: "{{ request.query.page or 1 }}"
        limit: "{{ request.query.limit or 10 }}"
        results:
          - title: "{{ fake.sentence() }}"
            description: "{{ fake.text() }}"
            url: "{{ fake.url() }}"
          - title: "{{ fake.sentence() }}"
            description: "{{ fake.text() }}"
            url: "{{ fake.url() }}"
        total_results: "{{ random.randint(100, 1000) }}"

  # Echo request data
  - method: "POST"
    path: "/api/echo"
    response:
      status_code: 200
      body:
        method: "{{ request.method }}"
        path: "{{ request.path }}"
        headers: "{{ request.headers }}"
        query_params: "{{ request.query }}"
        body: "{{ request.body }}"
        timestamp: "{{ datetime.now().isoformat() }}"
```

Test dynamic responses:

```bash
# Start server
api-mocker start --config dynamic-api.yaml

# Generate random user
curl http://127.0.0.1:8000/api/users/random

# Search with parameters
curl "http://127.0.0.1:8000/api/search?q=python&page=2&limit=5"

# Echo request data
curl -X POST http://127.0.0.1:8000/api/echo \
  -H "Content-Type: application/json" \
  -H "X-Custom-Header: test-value" \
  -d '{"message": "Hello World", "number": 42}'
```

## 🧪 Testing Your Mock API

### Create Test Configuration

Create `test-config.yaml`:

```yaml
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
        Content-Type: "application/json"
      body:
        name: "Test User"
        email: "test@example.com"
    expected:
      status_code: 201
      body:
        name: "Test User"
        email: "test@example.com"

  - name: "Protected Route Without Auth"
    request:
      method: "GET"
      url: "/api/protected"
    expected:
      status_code: 401

  - name: "Protected Route With Auth"
    request:
      method: "GET"
      url: "/api/protected"
      headers:
        Authorization: "Bearer secret-token-123"
    expected:
      status_code: 200
      body:
        message: "Access granted to protected resource"
```

Run tests:

```bash
# Run all tests
api-mocker test --config your-api.yaml --test-file test-config.yaml

# Run specific test
api-mocker test --config your-api.yaml --test-name "Health Check"

# Run tests with verbose output
api-mocker test --config your-api.yaml --test-file test-config.yaml --verbose
```

## 📊 Monitoring and Analytics

### Start Monitoring Dashboard

```bash
# Start monitoring on port 8080
api-mocker monitor --config your-api.yaml --port 8080

# Export metrics to file
api-mocker monitor --config your-api.yaml --export metrics.json
```

Visit `http://127.0.0.1:8080` to see:
- Request/response statistics
- Endpoint performance
- Error rates
- Real-time request logs

## 🔄 Import from Existing APIs

### Import OpenAPI/Swagger Specification

```bash
# Import from OpenAPI spec
api-mocker import openapi --file swagger.json --output mock-config.yaml

# Import with custom base URL
api-mocker import openapi --file api-spec.yaml --base-url https://api.example.com
```

### Import Postman Collection

```bash
# Import Postman collection
api-mocker import postman --file collection.json --output mock-config.yaml
```

### Record Real API Calls

```bash
# Record API calls to a real service
api-mocker record --target https://jsonplaceholder.typicode.com --output recorded.yaml

# Replay recorded requests
api-mocker replay --file recorded.yaml --config mock-config.yaml
```

## 🐳 Docker Integration

### Create Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install api-mocker

COPY config/ ./config/
EXPOSE 8000

CMD ["api-mocker", "start", "--config", "config/api.yaml", "--host", "0.0.0.0"]
```

### Create docker-compose.yml

```yaml
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

### Run with Docker

```bash
# Build and run
docker-compose up --build

# Or run directly
docker run -p 8000:8000 -v $(pwd)/config:/app/config api-mocker
```

## 🔌 Plugin System

### List Available Plugins

```bash
api-mocker plugins list
```

### Install and Enable Plugins

```bash
# Install a plugin
api-mocker plugins install auth-plugin

# Enable plugin
api-mocker plugins enable auth-plugin

# Configure plugin
api-mocker plugins configure auth-plugin --setting value
```

## 📈 Performance and Scaling

### Load Testing

```bash
# Test with multiple concurrent requests
for i in {1..100}; do
  curl http://127.0.0.1:8000/api/health &
done
wait
```

### Rate Limiting

Add to your config:

```yaml
server:
  rate_limit:
    enabled: true
    requests_per_minute: 100
    burst_size: 20
```

## 🚀 Next Steps

1. **Explore Templates**: Use `api-mocker init --template rest-api` to create pre-configured projects
2. **Integrate with CI/CD**: Add api-mocker to your testing pipeline
3. **Create Custom Plugins**: Extend functionality with your own plugins
4. **Join the Community**: Contribute to the project and share your use cases

## 🆘 Getting Help

- 📖 [Full Documentation](https://github.com/your-username/api-mocker#documentation)
- 🐛 [Report Issues](https://github.com/your-username/api-mocker/issues)
- 💬 [Ask Questions](https://github.com/your-username/api-mocker/discussions)
- 📧 [Email Support](mailto:support@api-mocker.com)

---

Happy mocking! 🎭 