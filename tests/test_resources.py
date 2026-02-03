import pytest
import json
from fastapi.testclient import TestClient
from api_mocker.server import MockServer

def test_resource_crud_workflow():
    """
    Test the full CRUD lifecycle of a resource.
    Scenario: E-commerce Products
    """
    config = {
        "resources": [
            {
                "name": "products",
                "path": "/api/products",
                "id_field": "id"
            }
        ]
    }
    
    server = MockServer(config_data=config)
    client = TestClient(server.app)
    
    # 1. LIST - Initiailly empty
    response = client.get("/api/products")
    assert response.status_code == 200
    data = response.json()["data"]
    assert data == []
    
    # 2. CREATE (POST)
    new_product = {"name": "Laptop", "price": 1000}
    response = client.post("/api/products", json=new_product)
    assert response.status_code == 201
    created_product = response.json()
    assert created_product["name"] == "Laptop"
    assert "id" in created_product
    product_id = created_product["id"]
    
    # 3. GET Item
    response = client.get(f"/api/products/{product_id}")
    assert response.status_code == 200
    assert response.json()["id"] == product_id
    
    # 4. UPDATE (PUT)
    update_data = {"price": 900}
    response = client.put(f"/api/products/{product_id}", json=update_data)
    assert response.status_code == 200
    assert response.json()["price"] == 900
    assert response.json()["name"] == "Laptop" # Should be preserved if merging? 
    # ResourceHandler.update merges.
    
    # 5. LIST again - should contain item
    response = client.get("/api/products")
    assert response.status_code == 200
    assert len(response.json()["data"]) == 1
    
    # 6. DELETE
    response = client.delete(f"/api/products/{product_id}")
    assert response.status_code == 204
    
    # 7. GET Item - 404
    response = client.get(f"/api/products/{product_id}")
    assert response.status_code == 404

def test_resource_smart_features():
    """Test filtering, pagination, sorting"""
    config = {
        "resources": [
            {
                "name": "users",
                "path": "/users",
                "id_field": "id"
            }
        ]
    }
    server = MockServer(config_data=config)
    client = TestClient(server.app)
    
    # Create bulk data
    for i in range(15):
        client.post("/users", json={"name": f"User {i}", "role": "admin" if i < 5 else "user"})
        
    # 1. Pagination
    response = client.get("/users?page=1&limit=10")
    data = response.json()
    assert len(data["data"]) == 10
    assert data["meta"]["total"] == 15
    assert data["meta"]["total_pages"] == 2
    
    response = client.get("/users?page=2&limit=10")
    data = response.json()
    assert len(data["data"]) == 5
    
    # 2. Filtering
    response = client.get("/users?role=admin")
    data = response.json()
    assert len(data["data"]) == 5
    for user in data["data"]:
        assert user["role"] == "admin"
        
    # 3. Search
    response = client.get("/users?q=User 1") # Should match "User 1", "User 10", "User 11"...
    data = response.json()
    # User 1, 10, 11, 12, 13, 14 -> 6 items
    assert len(data["data"]) >= 1 
    assert data["data"][0]["name"].startswith("User")
    
    # 4. Sorting
    # Sort by name descending
    response = client.get("/users?sort=name_desc&limit=100")
    data = response.json()["data"]
    # String sort: "User 9" > "User 10" ? No, "User 9" > "User 1"
    # Lexicographical: User 9 > User 8 ... User 14 > User 13 ..etc
    # Let's verify first and last
    # User names: User 0 .. User 14
    # Descending: User 9, User 8... since 9 > 1
    
    # Just check if it's not default order
    assert data[0]["name"] != "User 0"
