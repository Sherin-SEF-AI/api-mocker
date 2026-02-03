
import pytest
import asyncio
from api_mocker.graphql_mock import (
    GraphQLMockServer, GraphQLOperationType, GraphQLMockResponse
)

@pytest.fixture
def graphql_server():
    return GraphQLMockServer()

@pytest.mark.asyncio
async def test_introspection(graphql_server):
    schema = graphql_server.get_schema()
    assert "__schema" in schema
    assert "queryType" in schema["__schema"]
    types = schema["__schema"]["types"]
    assert any(t["name"] == "User" for t in types)

@pytest.mark.asyncio
async def test_basic_query(graphql_server):
    # Setup mock response
    query = "query { user(id: \"1\") { name } }"
    response = GraphQLMockResponse(
        operation_name="GetUser",
        operation_type=GraphQLOperationType.QUERY,
        query=query,
        response_data={"user": {"name": "Test User"}}
    )
    graphql_server.add_mock_response(response)
    
    # Execute
    result = await graphql_server.execute_query(query)
    assert result["data"]["user"]["name"] == "Test User"
    assert not result["errors"]

@pytest.mark.asyncio
async def test_variable_substitution(graphql_server):
    query = "query GetUser($id: ID!) { user(id: $id) { name } }"
    response = GraphQLMockResponse(
        operation_name="GetUser",
        operation_type=GraphQLOperationType.QUERY,
        query=query,
        variables={"id": "1"}, # Matches when var id=1
        response_data={"user": {"name": "User {{id}}"}}
    )
    graphql_server.add_mock_response(response)
    
    # Execute
    result = await graphql_server.execute_query(query, variables={"id": "1"})
    assert result["data"]["user"]["name"] == "User 1"
