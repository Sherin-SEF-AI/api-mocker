# API-Mocker Agent Context

> **SYSTEM PROMPT:** This document is optimized for AI Agents to understand how to operate `api-mocker`.

## 1. Tool Identity
- **Name**: `api-mocker`
- **Purpose**: Autonomous creation of mock APIs, data generation, and traffic analysis.
- **Interface**: CLI (Command Line Interface) and YAML Configuration.

## 2. Operation Manual

### BASH Command Map
| Intent | Command Template |
| :--- | :--- |
| **Initialize Project** | `api-mocker init --name {project_name}` |
| **Start Server** | `api-mocker start --config {config_path} --port {port}` |
| **Import API Spec** | `api-mocker import-spec {spec_file} --output {output_yaml}` |
| **List Configured Routes** | `api-mocker list-routes --config {config_path}` |
| **Generate Data** | `api-mocker ai generate --prompt "{description}" --count {n}` |
| **Check Health** | `curl http://localhost:{port}/health` |

### Configuration Schema (YAML)

Agents should generate configuration files following this structure:

```yaml
server:
  host: "127.0.0.1"
  port: 8000

routes:
  - path: "/api/example"
    method: "GET"
    response:
      status_code: 200
      body:
        message: "Hello World"
        timestamp: "{{timestamp}}"
    delay: 0 # milliseconds

ml:
  enabled: true # Enable predictive analytics
```

## 3. Self-Verification Strategy
To verify the tool is working, an Agent should:
1. Run `api-mocker --version`
2. Run `api-mocker init --name verify_test`
3. Run `api-mocker list-routes --config verify_test/config/api-mock.yaml`
4. Assert that output contains `/api/health`.

## 4. Advanced Capabilities
- **GraphQL**: `api-mocker graphql start`
- **WebSocket**: `api-mocker websocket start`
- **Analytics**: `api-mocker dashboard` (starts on port 8080)
