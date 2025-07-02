import pytest
from fastapi.testclient import TestClient
from api_mocker import MockServer

def test_mockserver_get():
    server = MockServer()
    client = TestClient(server.app)
    response = client.get("/mock/test-endpoint")
    assert response.status_code == 200
    assert response.json()["message"] == "GET mock for test-endpoint" 