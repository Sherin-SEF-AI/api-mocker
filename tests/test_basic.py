import pytest
from fastapi.testclient import TestClient
from api_mocker import MockServer

def test_mockserver_get():
    config = {
        "routes": [
            {
                "path": "/mock/test-endpoint",
                "method": "GET",
                "response": {
                    "status_code": 200,
                    "body": {"message": "GET mock for test-endpoint"}
                }
            }
        ]
    }
    server = MockServer(config_data=config)
    client = TestClient(server.app)
    response = client.get("/mock/test-endpoint")
    assert response.status_code == 200
    assert response.json()["message"] == "GET mock for test-endpoint" 