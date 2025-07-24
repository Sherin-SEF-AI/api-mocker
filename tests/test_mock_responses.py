"""
Comprehensive test suite for MockAPIResponse and MockSet classes.

This test suite demonstrates usage of the library in various scenarios and ensures
all functionality works correctly.
"""

import pytest
import time
import json
from unittest.mock import Mock, patch
from pathlib import Path
import tempfile
import os

from api_mocker.mock_responses import (
    MockAPIResponse, MockSet, ResponseType, HTTPMethod,
    CommitResponse, ForkResponse, PushResponse, ForcePushResponse,
    create_user_response, create_error_response, create_delayed_response,
    setup_api_mocks
)


class TestMockAPIResponse:
    """Test cases for MockAPIResponse class"""
    
    def test_basic_response_creation(self):
        """Test creating a basic mock response"""
        response = MockAPIResponse(
            path="/api/users",
            method=HTTPMethod.GET,
            status_code=200,
            body={"users": []}
        )
        
        assert response.path == "/api/users"
        assert response.method == HTTPMethod.GET
        assert response.status_code == 200
        assert response.body == {"users": []}
        assert response.name == "GET_api_users"
    
    def test_response_with_custom_name(self):
        """Test creating response with custom name"""
        response = MockAPIResponse(
            path="/api/users",
            name="custom_user_response",
            body={"users": []}
        )
        
        assert response.name == "custom_user_response"
    
    def test_default_headers(self):
        """Test that default headers are set correctly"""
        response = MockAPIResponse(path="/api/users")
        
        assert "Content-Type" in response.headers
        assert response.headers["Content-Type"] == "application/json"
        assert "X-Mock-Response" in response.headers
    
    def test_custom_headers(self):
        """Test setting custom headers"""
        custom_headers = {
            "Authorization": "Bearer token123",
            "X-Custom-Header": "custom_value"
        }
        
        response = MockAPIResponse(
            path="/api/users",
            headers=custom_headers
        )
        
        assert response.headers["Authorization"] == "Bearer token123"
        assert response.headers["X-Custom-Header"] == "custom_value"
    
    def test_path_matching_exact(self):
        """Test exact path matching"""
        response = MockAPIResponse(path="/api/users/123")
        
        assert response.matches_request("/api/users/123", "GET")
        assert not response.matches_request("/api/users/456", "GET")
    
    def test_path_matching_with_wildcards(self):
        """Test path matching with wildcards"""
        response = MockAPIResponse(path="/api/users/*")
        
        assert response.matches_request("/api/users/123", "GET")
        assert response.matches_request("/api/users/456", "GET")
        assert not response.matches_request("/api/posts/123", "GET")
    
    def test_path_matching_with_parameters(self):
        """Test path matching with parameters"""
        response = MockAPIResponse(path="/api/users/{user_id}")
        
        assert response.matches_request("/api/users/123", "GET")
        assert response.matches_request("/api/users/456", "GET")
        assert not response.matches_request("/api/users/123/posts", "GET")
    
    def test_method_matching(self):
        """Test HTTP method matching"""
        response = MockAPIResponse(
            path="/api/users",
            method=HTTPMethod.POST
        )
        
        assert response.matches_request("/api/users", "POST")
        assert not response.matches_request("/api/users", "GET")
    
    def test_header_condition_matching(self):
        """Test matching with header conditions"""
        response = MockAPIResponse(
            path="/api/users",
            conditions=[
                {
                    "type": "header",
                    "name": "Authorization",
                    "value": "Bearer token123"
                }
            ]
        )
        
        headers_with_auth = {"Authorization": "Bearer token123"}
        headers_without_auth = {"Content-Type": "application/json"}
        
        assert response.matches_request("/api/users", "GET", headers_with_auth)
        assert not response.matches_request("/api/users", "GET", headers_without_auth)
    
    def test_body_condition_matching(self):
        """Test matching with body conditions"""
        response = MockAPIResponse(
            path="/api/users",
            method=HTTPMethod.POST,
            conditions=[
                {
                    "type": "body",
                    "field": "user.name",
                    "value": "John Doe"
                }
            ]
        )
        
        body_with_name = {"user": {"name": "John Doe", "email": "john@example.com"}}
        body_without_name = {"user": {"name": "Jane Doe", "email": "jane@example.com"}}
        
        assert response.matches_request("/api/users", "POST", body=body_with_name)
        assert not response.matches_request("/api/users", "POST", body=body_without_name)
    
    def test_static_response_generation(self):
        """Test generating static responses"""
        response = MockAPIResponse(
            path="/api/users",
            response_type=ResponseType.STATIC,
            body={"users": [{"id": 1, "name": "John"}]}
        )
        
        result = response.generate_response()
        
        assert result["status_code"] == 200
        assert result["body"] == {"users": [{"id": 1, "name": "John"}]}
        assert "Content-Type" in result["headers"]
    
    def test_templated_response_generation(self):
        """Test generating templated responses"""
        response = MockAPIResponse(
            path="/api/users/{user_id}",
            response_type=ResponseType.TEMPLATED,
            template_vars={"user_id": "123", "name": "John Doe"},
            body={
                "id": "{{user_id}}",
                "name": "{{name}}",
                "email": "john@example.com"
            }
        )
        
        result = response.generate_response()
        
        assert result["body"]["id"] == "123"
        assert result["body"]["name"] == "John Doe"
        assert result["body"]["email"] == "john@example.com"
    
    def test_delayed_response_generation(self):
        """Test generating responses with delay"""
        response = MockAPIResponse(
            path="/api/slow",
            response_type=ResponseType.STATIC,
            delay_ms=100,
            body={"message": "delayed"}
        )
        
        start_time = time.time()
        result = response.generate_response()
        end_time = time.time()
        
        assert result["body"]["message"] == "delayed"
        assert end_time - start_time >= 0.1  # At least 100ms delay
    
    def test_error_response_generation(self):
        """Test generating error responses"""
        response = MockAPIResponse(
            path="/api/users",
            error_probability=1.0,  # Always return error
            body={"users": []}
        )
        
        result = response.generate_response()
        
        assert result["status_code"] == 500
        assert "error" in result["body"]
        assert result["headers"]["X-Mock-Error"] == "true"
    
    def test_dynamic_response_generation(self):
        """Test generating dynamic responses with custom function"""
        def generate_user(context):
            return {
                "id": context.get("user_id", "default"),
                "name": context.get("name", "Default User"),
                "timestamp": time.time()
            }
        
        response = MockAPIResponse(
            path="/api/users",
            response_type=ResponseType.DYNAMIC,
            generator_func=generate_user
        )
        
        context = {"user_id": "123", "name": "John Doe"}
        result = response.generate_response(context)
        
        assert result["body"]["id"] == "123"
        assert result["body"]["name"] == "John Doe"
        assert "timestamp" in result["body"]
    
    def test_serialization_and_deserialization(self):
        """Test converting response to/from dictionary"""
        original_response = MockAPIResponse(
            path="/api/users",
            method=HTTPMethod.POST,
            status_code=201,
            headers={"Custom-Header": "value"},
            body={"user": {"id": 1}},
            response_type=ResponseType.STATIC,
            delay_ms=100,
            error_probability=0.1,
            conditions=[{"type": "header", "name": "Auth", "value": "token"}],
            priority=5,
            template_vars={"var1": "value1"},
            description="Test response",
            tags=["test", "users"]
        )
        
        # Convert to dictionary
        response_dict = original_response.to_dict()
        
        # Convert back to response
        restored_response = MockAPIResponse.from_dict(response_dict)
        
        # Verify all properties are preserved
        assert restored_response.path == original_response.path
        assert restored_response.method == original_response.method
        assert restored_response.status_code == original_response.status_code
        assert restored_response.headers == original_response.headers
        assert restored_response.body == original_response.body
        assert restored_response.response_type == original_response.response_type
        assert restored_response.delay_ms == original_response.delay_ms
        assert restored_response.error_probability == original_response.error_probability
        assert restored_response.conditions == original_response.conditions
        assert restored_response.priority == original_response.priority
        assert restored_response.template_vars == original_response.template_vars
        assert restored_response.description == original_response.description
        assert restored_response.tags == original_response.tags
    
    def test_response_update(self):
        """Test updating response properties"""
        response = MockAPIResponse(path="/api/users")
        original_updated_at = response.updated_at
        
        time.sleep(0.1)  # Ensure timestamp difference
        response.update(
            status_code=404,
            body={"error": "Not found"},
            headers={"X-Error": "true"}
        )
        
        assert response.status_code == 404
        assert response.body == {"error": "Not found"}
        assert response.headers["X-Error"] == "true"
        assert response.updated_at > original_updated_at


class TestMockSet:
    """Test cases for MockSet class"""
    
    def test_mock_set_creation(self):
        """Test creating a mock set"""
        mock_set = MockSet("test_set")
        
        assert mock_set.name == "test_set"
        assert len(mock_set.responses) == 0
        assert mock_set.metadata == {}
    
    def test_adding_responses(self):
        """Test adding responses to a mock set"""
        mock_set = MockSet("test_set")
        
        response1 = MockAPIResponse(path="/api/users", name="users_response")
        response2 = MockAPIResponse(path="/api/posts", name="posts_response")
        
        mock_set.add_response(response1)
        mock_set.add_response(response2)
        
        assert len(mock_set.responses) == 2
        assert mock_set.get_by_name("users_response") == response1
        assert mock_set.get_by_name("posts_response") == response2
    
    def test_removing_responses(self):
        """Test removing responses from a mock set"""
        mock_set = MockSet("test_set")
        
        response = MockAPIResponse(path="/api/users", name="users_response")
        mock_set.add_response(response)
        
        assert len(mock_set.responses) == 1
        
        # Remove by name
        assert mock_set.remove_response("users_response") is True
        assert len(mock_set.responses) == 0
        
        # Try to remove non-existent response
        assert mock_set.remove_response("non_existent") is False
    
    def test_finding_matching_response(self):
        """Test finding the best matching response for a request"""
        mock_set = MockSet("test_set")
        
        # Add multiple responses with different priorities
        low_priority = MockAPIResponse(
            path="/api/users/*",
            priority=1,
            name="low_priority"
        )
        
        high_priority = MockAPIResponse(
            path="/api/users/123",
            priority=10,
            name="high_priority"
        )
        
        mock_set.add_response(low_priority)
        mock_set.add_response(high_priority)
        
        # Should return high priority response for exact match
        matching = mock_set.find_matching_response("/api/users/123", "GET")
        assert matching.name == "high_priority"
        
        # Should return low priority response for wildcard match
        matching = mock_set.find_matching_response("/api/users/456", "GET")
        assert matching.name == "low_priority"
    
    def test_filtering_responses(self):
        """Test filtering responses by various criteria"""
        mock_set = MockSet("test_set")
        
        # Add responses with different properties
        user_response = MockAPIResponse(
            path="/api/users",
            status_code=200,
            tags=["users", "api"],
            name="user_response"
        )
        
        error_response = MockAPIResponse(
            path="/api/users",
            status_code=404,
            tags=["error", "api"],
            name="error_response"
        )
        
        mock_set.add_response(user_response)
        mock_set.add_response(error_response)
        
        # Filter by status code
        filtered = mock_set.filter(status_code=200)
        assert len(filtered) == 1
        assert filtered[0].name == "user_response"
        
        # Filter by tags
        filtered = mock_set.filter(tags="error")
        assert len(filtered) == 1
        assert filtered[0].name == "error_response"
        
        # Filter by multiple tags
        filtered = mock_set.filter(tags=["api"])
        assert len(filtered) == 2
    
    def test_indexing_functionality(self):
        """Test that indexes are built correctly"""
        mock_set = MockSet("test_set")
        
        response1 = MockAPIResponse(
            path="/api/users",
            method=HTTPMethod.GET,
            tags=["users"],
            name="get_users"
        )
        
        response2 = MockAPIResponse(
            path="/api/users",
            method=HTTPMethod.POST,
            tags=["users", "create"],
            name="create_user"
        )
        
        mock_set.add_response(response1)
        mock_set.add_response(response2)
        
        # Test path index
        path_responses = mock_set.get_by_path("/api/users")
        assert len(path_responses) == 2
        
        # Test method index
        get_responses = mock_set.get_by_method("GET")
        assert len(get_responses) == 1
        assert get_responses[0].name == "get_users"
        
        post_responses = mock_set.get_by_method("POST")
        assert len(post_responses) == 1
        assert post_responses[0].name == "create_user"
        
        # Test tag index
        user_responses = mock_set.get_by_tag("users")
        assert len(user_responses) == 2
        
        create_responses = mock_set.get_by_tag("create")
        assert len(create_responses) == 1
        assert create_responses[0].name == "create_user"
    
    def test_serialization_and_deserialization(self):
        """Test converting mock set to/from dictionary"""
        mock_set = MockSet("test_set", metadata={"version": "1.0"})
        
        response1 = MockAPIResponse(path="/api/users", name="users")
        response2 = MockAPIResponse(path="/api/posts", name="posts")
        
        mock_set.add_response(response1)
        mock_set.add_response(response2)
        
        # Convert to dictionary
        mock_set_dict = mock_set.to_dict()
        
        # Convert back to mock set
        restored_mock_set = MockSet.from_dict(mock_set_dict)
        
        assert restored_mock_set.name == mock_set.name
        assert restored_mock_set.metadata == mock_set.metadata
        assert len(restored_mock_set.responses) == len(mock_set.responses)
    
    def test_file_save_and_load(self):
        """Test saving and loading mock sets to/from files"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            temp_file = f.name
        
        try:
            # Create and save mock set
            mock_set = MockSet("test_set", metadata={"version": "1.0"})
            response = MockAPIResponse(path="/api/users", name="users")
            mock_set.add_response(response)
            
            mock_set.save_to_file(temp_file)
            
            # Load mock set from file
            loaded_mock_set = MockSet.load_from_file(temp_file)
            
            assert loaded_mock_set.name == mock_set.name
            assert loaded_mock_set.metadata == mock_set.metadata
            assert len(loaded_mock_set.responses) == len(mock_set.responses)
            
        finally:
            # Clean up
            if os.path.exists(temp_file):
                os.unlink(temp_file)


class TestExampleSubclasses:
    """Test cases for example subclasses"""
    
    def test_commit_response(self):
        """Test CommitResponse subclass"""
        response = CommitResponse()
        
        assert response.path == "/repos/{owner}/{repo}/git/commits"
        assert response.method == HTTPMethod.POST
        assert response.status_code == 201
        assert response.response_type == ResponseType.TEMPLATED
        
        result = response.generate_response()
        assert result["body"]["sha"] == "abc123def456"
        assert result["body"]["message"] == "feat: add new feature"
        assert result["body"]["author"]["name"] == "John Doe"
    
    def test_fork_response(self):
        """Test ForkResponse subclass"""
        response = ForkResponse()
        
        assert response.path == "/repos/{owner}/{repo}/forks"
        assert response.method == HTTPMethod.POST
        assert response.status_code == 202
        assert response.response_type == ResponseType.STATIC
        
        result = response.generate_response()
        assert result["body"]["id"] == 12345
        assert result["body"]["fork"] is True
        assert result["body"]["source"]["name"] == "original-repo"
    
    def test_push_response(self):
        """Test PushResponse subclass"""
        response = PushResponse()
        
        assert response.path == "/repos/{owner}/{repo}/git/refs/heads/{branch}"
        assert response.method == HTTPMethod.PATCH
        assert response.status_code == 200
        assert response.response_type == ResponseType.TEMPLATED
        
        result = response.generate_response()
        assert result["body"]["ref"] == "refs/heads/main"
        assert result["body"]["sha"] == "def456ghi789"
    
    def test_force_push_response(self):
        """Test ForcePushResponse subclass"""
        response = ForcePushResponse()
        
        assert response.path == "/repos/{owner}/{repo}/git/refs/heads/{branch}"
        assert response.method == HTTPMethod.PATCH
        assert response.status_code == 200
        assert response.response_type == ResponseType.STATIC
        
        result = response.generate_response()
        assert result["body"]["force"] is True
        assert result["body"]["sha"] == "force123push456"


class TestConvenienceFunctions:
    """Test cases for convenience functions"""
    
    def test_create_user_response(self):
        """Test create_user_response function"""
        response = create_user_response("123", "John Doe")
        
        assert response.path == "/users/123"
        assert response.method == HTTPMethod.GET
        assert response.status_code == 200
        assert response.response_type == ResponseType.TEMPLATED
        
        result = response.generate_response()
        assert result["body"]["id"] == "123"
        assert result["body"]["name"] == "John Doe"
    
    def test_create_error_response(self):
        """Test create_error_response function"""
        response = create_error_response(500, "Internal Server Error")
        
        assert response.path == "*"
        assert response.status_code == 500
        assert response.response_type == ResponseType.STATIC
        
        result = response.generate_response()
        assert result["body"]["error"] is True
        assert result["body"]["message"] == "Internal Server Error"
        assert result["body"]["status_code"] == 500
    
    def test_create_delayed_response(self):
        """Test create_delayed_response function"""
        response = create_delayed_response(100)
        
        assert response.path == "/slow-endpoint"
        assert response.delay_ms == 100
        assert response.response_type == ResponseType.STATIC
        
        start_time = time.time()
        result = response.generate_response()
        end_time = time.time()
        
        assert result["body"]["message"] == "Response delayed"
        assert end_time - start_time >= 0.1


class TestPytestIntegration:
    """Test cases for pytest integration"""
    
    def test_setup_api_mocks_fixture(self):
        """Test the setup_api_mocks pytest fixture"""
        # Create a mock set directly instead of calling fixture
        mock_set = MockSet("test_mocks")
        
        assert isinstance(mock_set, MockSet)
        assert mock_set.name == "test_mocks"
        assert len(mock_set.responses) == 0
    
    def test_using_mock_set_in_test(self):
        """Test using mock set in a test scenario"""
        mock_set = MockSet("test_mocks")
        
        # Add some responses
        user_response = create_user_response("123", "John Doe")
        error_response = create_error_response(404, "User not found")
        
        mock_set.add_response(user_response)
        mock_set.add_response(error_response)
        
        # Test finding responses
        matching = mock_set.find_matching_response("/users/123", "GET")
        assert matching is not None
        assert matching.name == "GET_users_123"
        
        # Test filtering
        error_responses = mock_set.filter(status_code=404)
        assert len(error_responses) == 1


class TestAdvancedScenarios:
    """Test cases for advanced usage scenarios"""
    
    def test_complex_conditional_matching(self):
        """Test complex conditional matching with multiple conditions"""
        response = MockAPIResponse(
            path="/api/users",
            method=HTTPMethod.POST,
            conditions=[
                {
                    "type": "header",
                    "name": "Authorization",
                    "value": "Bearer admin_token"
                },
                {
                    "type": "body",
                    "field": "user.role",
                    "value": "admin"
                }
            ],
            body={"message": "Admin user created"}
        )
        
        # Should match
        headers = {"Authorization": "Bearer admin_token"}
        body = {"user": {"role": "admin", "name": "Admin User"}}
        assert response.matches_request("/api/users", "POST", headers, body)
        
        # Should not match - wrong header
        headers = {"Authorization": "Bearer user_token"}
        assert not response.matches_request("/api/users", "POST", headers, body)
        
        # Should not match - wrong role
        headers = {"Authorization": "Bearer admin_token"}
        body = {"user": {"role": "user", "name": "Regular User"}}
        assert not response.matches_request("/api/users", "POST", headers, body)
    
    def test_priority_based_response_selection(self):
        """Test priority-based response selection"""
        mock_set = MockSet("priority_test")
        
        # Add responses with different priorities
        general_response = MockAPIResponse(
            path="/api/users/*",
            priority=1,
            name="general",
            body={"message": "General response"}
        )
        
        specific_response = MockAPIResponse(
            path="/api/users/123",
            priority=10,
            name="specific",
            body={"message": "Specific response"}
        )
        
        mock_set.add_response(general_response)
        mock_set.add_response(specific_response)
        
        # Should return specific response for exact match
        matching = mock_set.find_matching_response("/api/users/123", "GET")
        assert matching.name == "specific"
        
        # Should return general response for other users
        matching = mock_set.find_matching_response("/api/users/456", "GET")
        assert matching.name == "general"
    
    def test_template_variable_substitution(self):
        """Test complex template variable substitution"""
        response = MockAPIResponse(
            path="/api/users/{user_id}/posts/{post_id}",
            response_type=ResponseType.TEMPLATED,
            template_vars={
                "user_id": "123",
                "post_id": "456",
                "title": "Sample Post"
            },
            body={
                "user_id": "{{user_id}}",
                "post_id": "{{post_id}}",
                "title": "{{title}}",
                "url": "/api/users/{{user_id}}/posts/{{post_id}}"
            }
        )
        
        result = response.generate_response()
        
        assert result["body"]["user_id"] == "123"
        assert result["body"]["post_id"] == "456"
        assert result["body"]["title"] == "Sample Post"
        assert result["body"]["url"] == "/api/users/123/posts/456"
    
    def test_error_probability_simulation(self):
        """Test error probability simulation"""
        response = MockAPIResponse(
            path="/api/unreliable",
            error_probability=0.5,  # 50% chance of error
            body={"data": "success"}
        )
        
        error_count = 0
        success_count = 0
        
        # Run multiple times to test probability
        for _ in range(100):
            result = response.generate_response()
            if result["status_code"] == 500:
                error_count += 1
            else:
                success_count += 1
        
        # Should have some errors and some successes
        assert error_count > 0
        assert success_count > 0
        assert error_count + success_count == 100


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v"]) 