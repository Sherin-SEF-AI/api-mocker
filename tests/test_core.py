import pytest
from api_mocker.core import (
    CoreEngine, AdvancedRouter, RouteConfig, 
    DynamicResponseGenerator, SchemaValidator, StateManager
)

class TestCoreEngine:
    def test_engine_initialization(self):
        """Test that the core engine initializes correctly."""
        engine = CoreEngine()
        assert engine.router is not None
        assert engine.schema_validator is not None
        assert engine.state_manager is not None
        assert engine.response_generator is not None

    def test_add_route(self):
        """Test adding routes to the engine."""
        engine = CoreEngine()
        route = RouteConfig(
            path="/api/test",
            method="GET",
            response={"message": "test"}
        )
        engine.router.add_route(route)
        assert len(engine.router.routes) == 1

    def test_process_request_simple(self):
        """Test processing a simple request."""
        engine = CoreEngine()
        route = RouteConfig(
            path="/api/test",
            method="GET",
            response={"message": "test response"}
        )
        engine.router.add_route(route)
        
        response = engine.process_request("/api/test", "GET", {})
        assert response["status_code"] == 200
        assert response["body"]["message"] == "test response"

    def test_process_request_not_found(self):
        """Test processing a request for a non-existent route."""
        engine = CoreEngine()
        response = engine.process_request("/api/notfound", "GET", {})
        assert response["status_code"] == 404
        assert "error" in response["body"]

class TestAdvancedRouter:
    def test_router_initialization(self):
        """Test router initialization."""
        router = AdvancedRouter()
        assert router.routes == []
        assert router.path_params == {}

    def test_add_route(self):
        """Test adding routes to the router."""
        router = AdvancedRouter()
        route = RouteConfig(
            path="/api/users/{user_id}",
            method="GET",
            response={"id": "{{user_id}}"}
        )
        router.add_route(route)
        assert len(router.routes) == 1

    def test_find_route_exact_match(self):
        """Test finding a route with exact path match."""
        router = AdvancedRouter()
        route = RouteConfig(
            path="/api/users",
            method="GET",
            response={"users": []}
        )
        router.add_route(route)
        
        found_route = router.find_route("/api/users", "GET")
        assert found_route is not None
        assert found_route.path == "/api/users"

    def test_find_route_with_parameters(self):
        """Test finding a route with path parameters."""
        router = AdvancedRouter()
        route = RouteConfig(
            path="/api/users/{user_id}",
            method="GET",
            response={"id": "{{user_id}}"}
        )
        router.add_route(route)
        
        found_route = router.find_route("/api/users/123", "GET")
        assert found_route is not None
        assert router.path_params["user_id"] == "123"

    def test_find_route_method_mismatch(self):
        """Test that route matching considers HTTP method."""
        router = AdvancedRouter()
        route = RouteConfig(
            path="/api/users",
            method="GET",
            response={"users": []}
        )
        router.add_route(route)
        
        found_route = router.find_route("/api/users", "POST")
        assert found_route is None

    def test_path_to_regex_conversion(self):
        """Test conversion of path parameters to regex patterns."""
        router = AdvancedRouter()
        pattern = router._path_to_regex("/api/users/{user_id}/posts/{post_id}")
        assert pattern == "^/api/users/(?P<user_id>[^/]+)/posts/(?P<post_id>[^/]+)$"

class TestDynamicResponseGenerator:
    def test_generate_user(self):
        """Test user generation."""
        user = DynamicResponseGenerator.generate_user()
        assert "id" in user
        assert "name" in user
        assert "email" in user
        assert "created_at" in user
        assert "@" in user["email"]

    def test_generate_product(self):
        """Test product generation."""
        product = DynamicResponseGenerator.generate_product()
        assert "id" in product
        assert "name" in product
        assert "price" in product
        assert "category" in product
        assert isinstance(product["price"], float)

    def test_generate_list(self):
        """Test list generation."""
        users = DynamicResponseGenerator.generate_list("user", 5)
        assert len(users) == 5
        assert all("id" in user for user in users)

class TestSchemaValidator:
    def test_validator_initialization(self):
        """Test schema validator initialization."""
        validator = SchemaValidator()
        assert validator.schemas == {}

    def test_add_schema(self):
        """Test adding schemas to the validator."""
        validator = SchemaValidator()
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "integer"}
            }
        }
        validator.add_schema("User", schema)
        assert "User" in validator.schemas

    def test_generate_from_schema_object(self):
        """Test generating data from object schema."""
        validator = SchemaValidator()
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "integer"}
            }
        }
        validator.add_schema("User", schema)
        
        data = validator.generate_from_schema("User")
        assert isinstance(data, dict)
        assert "name" in data
        assert "age" in data

    def test_generate_from_schema_array(self):
        """Test generating data from array schema."""
        validator = SchemaValidator()
        schema = {
            "type": "array",
            "items": {"type": "string"},
            "minItems": 3
        }
        validator.add_schema("StringArray", schema)
        
        data = validator.generate_from_schema("StringArray")
        assert isinstance(data, list)
        assert len(data) >= 3

class TestStateManager:
    def test_state_manager_initialization(self):
        """Test state manager initialization."""
        state = StateManager()
        assert state.data == {}
        assert state.counters == {}

    def test_set_and_get_data(self):
        """Test setting and getting data."""
        state = StateManager()
        state.set_data("users", [{"id": 1, "name": "John"}])
        
        data = state.get_data("users")
        assert data == [{"id": 1, "name": "John"}]

    def test_delete_data(self):
        """Test deleting data."""
        state = StateManager()
        state.set_data("temp", "value")
        assert state.get_data("temp") == "value"
        
        success = state.delete_data("temp")
        assert success is True
        assert state.get_data("temp") is None

    def test_get_next_id(self):
        """Test ID generation."""
        state = StateManager()
        id1 = state.get_next_id("users")
        id2 = state.get_next_id("users")
        id3 = state.get_next_id("posts")
        
        assert id1 == 1
        assert id2 == 2
        assert id3 == 1  # Different resource

    def test_reset(self):
        """Test resetting state."""
        state = StateManager()
        state.set_data("test", "value")
        state.get_next_id("users")
        
        state.reset()
        assert state.data == {}
        assert state.counters == {} 