import pytest
from fastapi.testclient import TestClient
from api_mocker.server import MockServer
from api_mocker.auth_system import auth_system

def test_auth_integration():
    """Test that auth_required enforced in server"""
    config = {
        "routes": [
            {
                "path": "/protected",
                "method": "GET",
                "response": {"body": {"secret": "data"}},
                "auth": True 
            },
            {
                "path": "/public",
                "method": "GET",
                "response": {"body": {"public": "data"}},
                "auth": False
            }
        ]
    }
    
    server = MockServer(config_data=config)
    client = TestClient(server.app)
    
    # 1. Public Route
    resp = client.get("/public")
    assert resp.status_code == 200
    
    # 2. Protected Route - No Token
    resp = client.get("/protected")
    assert resp.status_code == 401
    assert "Missing or invalid token" in resp.json()["error"]
    
    # 3. Protected Route - Invalid Token
    resp = client.get("/protected", headers={"Authorization": "Bearer invalid"})
    assert resp.status_code == 401
    
    # 4. Protected Route - Valid Token
    # Register user to get token
    reg = auth_system.register_user("intuser", "int@test.com", "Pass123!Safe")
    # Login
    auth = auth_system.authenticate_user("int@test.com", "Pass123!Safe")
    token = auth["access_token"]
    
    resp = client.get("/protected", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["secret"] == "data"
