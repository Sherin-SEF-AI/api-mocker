"""
GraphQL Mock Support System

This module provides comprehensive GraphQL mocking capabilities including:
- Schema introspection and validation
- Query and mutation mocking
- Subscription support with real-time updates
- Advanced type system support
- Custom resolvers and middleware
"""

import json
import asyncio
from typing import Any, Dict, List, Optional, Union, Callable
from dataclasses import dataclass, field
from enum import Enum
import re
from datetime import datetime
import uuid


class GraphQLOperationType(Enum):
    """GraphQL operation types"""
    QUERY = "query"
    MUTATION = "mutation"
    SUBSCRIPTION = "subscription"


class GraphQLScalarType(Enum):
    """GraphQL scalar types"""
    STRING = "String"
    INT = "Int"
    FLOAT = "Float"
    BOOLEAN = "Boolean"
    ID = "ID"
    DATE = "Date"
    DATETIME = "DateTime"
    JSON = "JSON"


@dataclass
class GraphQLField:
    """Represents a GraphQL field definition"""
    name: str
    type: str
    description: Optional[str] = None
    args: List[Dict[str, Any]] = field(default_factory=list)
    is_required: bool = False
    is_list: bool = False
    is_nullable: bool = True


@dataclass
class GraphQLType:
    """Represents a GraphQL type definition"""
    name: str
    kind: str  # OBJECT, SCALAR, ENUM, INTERFACE, UNION, INPUT_OBJECT
    description: Optional[str] = None
    fields: List[GraphQLField] = field(default_factory=list)
    interfaces: List[str] = field(default_factory=list)
    possible_types: List[str] = field(default_factory=list)
    enum_values: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class GraphQLMockResolver:
    """Represents a custom resolver for GraphQL operations"""
    field_name: str
    type_name: str
    resolver_func: Callable
    description: Optional[str] = None
    args: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class GraphQLMockResponse:
    """Represents a mock response for GraphQL operations"""
    operation_name: str
    operation_type: GraphQLOperationType
    query: str
    variables: Dict[str, Any] = field(default_factory=dict)
    response_data: Dict[str, Any] = field(default_factory=dict)
    errors: List[Dict[str, Any]] = field(default_factory=list)
    extensions: Dict[str, Any] = field(default_factory=dict)
    delay_ms: int = 0
    error_probability: float = 0.0
    conditions: List[Dict[str, Any]] = field(default_factory=list)
    priority: int = 0


class GraphQLSchemaManager:
    """Manages GraphQL schema definitions and introspection"""
    
    def __init__(self):
        self.types: Dict[str, GraphQLType] = {}
        self.queries: Dict[str, GraphQLField] = {}
        self.mutations: Dict[str, GraphQLField] = {}
        self.subscriptions: Dict[str, GraphQLField] = {}
        self.resolvers: List[GraphQLMockResolver] = []
    
    def add_type(self, type_def: GraphQLType) -> None:
        """Add a type definition to the schema"""
        self.types[type_def.name] = type_def
    
    def add_query(self, field: GraphQLField) -> None:
        """Add a query field to the schema"""
        self.queries[field.name] = field
    
    def add_mutation(self, field: GraphQLField) -> None:
        """Add a mutation field to the schema"""
        self.mutations[field.name] = field
    
    def add_subscription(self, field: GraphQLField) -> None:
        """Add a subscription field to the schema"""
        self.subscriptions[field.name] = field
    
    def add_resolver(self, resolver: GraphQLMockResolver) -> None:
        """Add a custom resolver"""
        self.resolvers.append(resolver)
    
    def get_schema_introspection(self) -> Dict[str, Any]:
        """Generate GraphQL schema introspection data"""
        return {
            "__schema": {
                "queryType": {"name": "Query"},
                "mutationType": {"name": "Mutation"} if self.mutations else None,
                "subscriptionType": {"name": "Subscription"} if self.subscriptions else None,
                "types": [self._type_to_introspection(type_def) for type_def in self.types.values()],
                "directives": []
            }
        }
    
    def _type_to_introspection(self, type_def: GraphQLType) -> Dict[str, Any]:
        """Convert type definition to introspection format"""
        result = {
            "name": type_def.name,
            "kind": type_def.kind.upper(),
            "description": type_def.description
        }
        
        if type_def.fields:
            result["fields"] = [
                {
                    "name": field.name,
                    "type": self._field_type_to_introspection(field),
                    "description": field.description,
                    "args": [
                        {
                            "name": arg["name"],
                            "type": self._field_type_to_introspection(arg),
                            "description": arg.get("description")
                        }
                        for arg in field.args
                    ]
                }
                for field in type_def.fields
            ]
        
        if type_def.enum_values:
            result["enumValues"] = [
                {
                    "name": enum_val["name"],
                    "description": enum_val.get("description"),
                    "isDeprecated": enum_val.get("isDeprecated", False)
                }
                for enum_val in type_def.enum_values
            ]
        
        return result
    
    def _field_type_to_introspection(self, field: Union[GraphQLField, Dict[str, Any]]) -> Dict[str, Any]:
        """Convert field type to introspection format"""
        if isinstance(field, GraphQLField):
            type_name = field.type
            is_required = field.is_required
            is_list = field.is_list
        else:
            type_name = field["type"]
            is_required = field.get("isRequired", False)
            is_list = field.get("isList", False)
        
        result = {"name": type_name}
        
        if is_list:
            result = {
                "kind": "LIST",
                "ofType": result
            }
        
        if not is_required:
            result = {
                "kind": "NON_NULL",
                "ofType": result
            }
        
        return result


class GraphQLMockServer:
    """Main GraphQL mock server implementation"""
    
    def __init__(self):
        self.schema_manager = GraphQLSchemaManager()
        self.mock_responses: List[GraphQLMockResponse] = []
        self.subscription_connections: Dict[str, asyncio.Queue] = {}
        self._setup_default_schema()
    
    def _setup_default_schema(self) -> None:
        """Setup default GraphQL schema with common types"""
        # User type
        user_type = GraphQLType(
            name="User",
            kind="OBJECT",
            description="A user in the system",
            fields=[
                GraphQLField("id", "ID!", is_required=True),
                GraphQLField("name", "String!", is_required=True),
                GraphQLField("email", "String!", is_required=True),
                GraphQLField("createdAt", "DateTime!"),
                GraphQLField("posts", "[Post!]")
            ]
        )
        
        # Post type
        post_type = GraphQLType(
            name="Post",
            kind="OBJECT",
            description="A blog post",
            fields=[
                GraphQLField("id", "ID!", is_required=True),
                GraphQLField("title", "String!", is_required=True),
                GraphQLField("content", "String!"),
                GraphQLField("author", "User!"),
                GraphQLField("publishedAt", "DateTime")
            ]
        )
        
        # Query type
        query_type = GraphQLType(
            name="Query",
            kind="OBJECT",
            fields=[
                GraphQLField("user", "User", args=[
                    {"name": "id", "type": "ID!", "isRequired": True}
                ]),
                GraphQLField("users", "[User!]"),
                GraphQLField("post", "Post", args=[
                    {"name": "id", "type": "ID!", "isRequired": True}
                ]),
                GraphQLField("posts", "[Post!]")
            ]
        )
        
        # Mutation type
        mutation_type = GraphQLType(
            name="Mutation",
            kind="OBJECT",
            fields=[
                GraphQLField("createUser", "User!", args=[
                    {"name": "input", "type": "CreateUserInput!", "isRequired": True}
                ]),
                GraphQLField("updateUser", "User!", args=[
                    {"name": "id", "type": "ID!", "isRequired": True},
                    {"name": "input", "type": "UpdateUserInput!", "isRequired": True}
                ]),
                GraphQLField("deleteUser", "Boolean!", args=[
                    {"name": "id", "type": "ID!", "isRequired": True}
                ])
            ]
        )
        
        # Input types
        create_user_input = GraphQLType(
            name="CreateUserInput",
            kind="INPUT_OBJECT",
            fields=[
                GraphQLField("name", "String!", is_required=True),
                GraphQLField("email", "String!", is_required=True)
            ]
        )
        
        update_user_input = GraphQLType(
            name="UpdateUserInput",
            kind="INPUT_OBJECT",
            fields=[
                GraphQLField("name", "String"),
                GraphQLField("email", "String")
            ]
        )
        
        # Add types to schema
        self.schema_manager.add_type(user_type)
        self.schema_manager.add_type(post_type)
        self.schema_manager.add_type(query_type)
        self.schema_manager.add_type(mutation_type)
        self.schema_manager.add_type(create_user_input)
        self.schema_manager.add_type(update_user_input)
        
        # Add query fields
        for field in query_type.fields:
            self.schema_manager.add_query(field)
        
        # Add mutation fields
        for field in mutation_type.fields:
            self.schema_manager.add_mutation(field)
    
    def add_mock_response(self, response: GraphQLMockResponse) -> None:
        """Add a mock response for GraphQL operations"""
        self.mock_responses.append(response)
        # Sort by priority (higher priority first)
        self.mock_responses.sort(key=lambda x: x.priority, reverse=True)
    
    def create_mock_response(self, operation_name: str, operation_type: GraphQLOperationType,
                           query: str, response_data: Dict[str, Any],
                           variables: Dict[str, Any] = None,
                           delay_ms: int = 0, error_probability: float = 0.0,
                           conditions: List[Dict[str, Any]] = None,
                           priority: int = 0) -> GraphQLMockResponse:
        """Create a mock response for GraphQL operations"""
        return GraphQLMockResponse(
            operation_name=operation_name,
            operation_type=operation_type,
            query=query,
            variables=variables or {},
            response_data=response_data,
            delay_ms=delay_ms,
            error_probability=error_probability,
            conditions=conditions or [],
            priority=priority
        )
    
    def find_matching_response(self, query: str, variables: Dict[str, Any] = None,
                             operation_name: str = None) -> Optional[GraphQLMockResponse]:
        """Find the best matching response for a GraphQL query"""
        variables = variables or {}
        
        for response in self.mock_responses:
            if self._matches_query(response, query, variables, operation_name):
                return response
        
        return None
    
    def _matches_query(self, response: GraphQLMockResponse, query: str,
                      variables: Dict[str, Any], operation_name: str = None) -> bool:
        """Check if a response matches the given query"""
        # Check operation name
        if operation_name and response.operation_name != operation_name:
            return False
        
        # Check query matching (exact or pattern)
        if response.query != query and not self._query_pattern_match(response.query, query):
            return False
        
        # Check variables
        if response.variables:
            for key, value in response.variables.items():
                if variables.get(key) != value:
                    return False
        
        # Check conditions
        if response.conditions:
            return self._check_conditions(response.conditions, variables)
        
        return True
    
    def _query_pattern_match(self, pattern: str, query: str) -> bool:
        """Check if query matches a pattern"""
        # Simple pattern matching - can be enhanced
        if '*' in pattern:
            regex_pattern = pattern.replace('*', '.*')
            return bool(re.match(regex_pattern, query))
        return False
    
    def _check_conditions(self, conditions: List[Dict[str, Any]], variables: Dict[str, Any]) -> bool:
        """Check if conditions are met"""
        for condition in conditions:
            if not self._evaluate_condition(condition, variables):
                return False
        return True
    
    def _evaluate_condition(self, condition: Dict[str, Any], variables: Dict[str, Any]) -> bool:
        """Evaluate a single condition"""
        condition_type = condition.get('type', 'variable')
        
        if condition_type == 'variable':
            field_path = condition.get('field')
            expected_value = condition.get('value')
            actual_value = self._get_nested_value(variables, field_path)
            return actual_value == expected_value
        
        elif condition_type == 'custom':
            func = condition.get('function')
            return func(variables) if callable(func) else False
        
        return False
    
    def _get_nested_value(self, obj: Any, path: str) -> Any:
        """Get nested value from object using dot notation"""
        if not path:
            return obj
        
        keys = path.split('.')
        current = obj
        
        for key in keys:
            if isinstance(current, dict):
                current = current.get(key)
            elif isinstance(current, list) and key.isdigit():
                current = current[int(key)]
            else:
                return None
        
        return current
    
    async def execute_query(self, query: str, variables: Dict[str, Any] = None,
                          operation_name: str = None) -> Dict[str, Any]:
        """Execute a GraphQL query and return mock response"""
        variables = variables or {}
        
        # Find matching response
        response = self.find_matching_response(query, variables, operation_name)
        
        if not response:
            return {
                "data": None,
                "errors": [{"message": "No mock response found for query"}]
            }
        
        # Check for errors
        if response.error_probability > 0 and self._should_return_error(response.error_probability):
            return {
                "data": None,
                "errors": [{"message": "Mock error response", "extensions": {"code": "MOCK_ERROR"}}]
            }
        
        # Apply delay
        if response.delay_ms > 0:
            await asyncio.sleep(response.delay_ms / 1000.0)
        
        # Generate response data
        data = self._generate_response_data(response, variables)
        
        result = {
            "data": data,
            "errors": response.errors,
            "extensions": response.extensions
        }
        
        return result
    
    def _should_return_error(self, error_probability: float) -> bool:
        """Determine if an error should be returned"""
        import random
        return random.random() < error_probability
    
    def _generate_response_data(self, response: GraphQLMockResponse, variables: Dict[str, Any]) -> Dict[str, Any]:
        """Generate response data with variable substitution"""
        data = response.response_data.copy()
        
        # Substitute variables in response data
        data = self._substitute_variables(data, variables)
        
        return data
    
    def _substitute_variables(self, data: Any, variables: Dict[str, Any]) -> Any:
        """Recursively substitute variables in data"""
        if isinstance(data, dict):
            return {key: self._substitute_variables(value, variables) for key, value in data.items()}
        elif isinstance(data, list):
            return [self._substitute_variables(item, variables) for item in data]
        elif isinstance(data, str) and data.startswith('{{') and data.endswith('}}'):
            var_name = data[2:-2]
            return variables.get(var_name, data)
        else:
            return data
    
    async def handle_subscription(self, query: str, variables: Dict[str, Any] = None,
                                operation_name: str = None) -> asyncio.Queue:
        """Handle GraphQL subscription with real-time updates"""
        connection_id = str(uuid.uuid4())
        queue = asyncio.Queue()
        self.subscription_connections[connection_id] = queue
        
        # Start subscription task
        asyncio.create_task(self._subscription_worker(connection_id, query, variables, operation_name))
        
        return queue
    
    async def _subscription_worker(self, connection_id: str, query: str,
                                  variables: Dict[str, Any], operation_name: str) -> None:
        """Worker for handling subscription updates"""
        try:
            while connection_id in self.subscription_connections:
                # Generate subscription data
                data = await self._generate_subscription_data(query, variables, operation_name)
                
                if connection_id in self.subscription_connections:
                    await self.subscription_connections[connection_id].put(data)
                
                # Wait before next update
                await asyncio.sleep(1.0)  # 1 second interval
        except Exception as e:
            print(f"Subscription error: {e}")
        finally:
            if connection_id in self.subscription_connections:
                del self.subscription_connections[connection_id]
    
    async def _generate_subscription_data(self, query: str, variables: Dict[str, Any],
                                       operation_name: str) -> Dict[str, Any]:
        """Generate subscription data"""
        # This would typically generate real-time data
        # For now, return mock data
        return {
            "data": {
                "subscriptionUpdate": {
                    "id": str(uuid.uuid4()),
                    "timestamp": datetime.now().isoformat(),
                    "message": "Real-time update"
                }
            }
        }
    
    def get_schema(self) -> Dict[str, Any]:
        """Get the GraphQL schema"""
        return self.schema_manager.get_schema_introspection()
    
    def add_custom_resolver(self, field_name: str, type_name: str, resolver_func: Callable) -> None:
        """Add a custom resolver for a field"""
        resolver = GraphQLMockResolver(
            field_name=field_name,
            type_name=type_name,
            resolver_func=resolver_func
        )
        self.schema_manager.add_resolver(resolver)


# Global GraphQL mock server instance
graphql_mock_server = GraphQLMockServer()


# Convenience functions
def create_user_query_mock(user_id: str = "123", name: str = "John Doe") -> GraphQLMockResponse:
    """Create a mock response for user query"""
    return GraphQLMockResponse(
        operation_name="GetUser",
        operation_type=GraphQLOperationType.QUERY,
        query="query GetUser($id: ID!) { user(id: $id) { id name email createdAt } }",
        variables={"id": user_id},
        response_data={
            "user": {
                "id": "{{id}}",
                "name": name,
                "email": "john@example.com",
                "createdAt": "2023-01-01T00:00:00Z"
            }
        }
    )


def create_post_mutation_mock(title: str = "Sample Post", content: str = "Post content") -> GraphQLMockResponse:
    """Create a mock response for post creation mutation"""
    return GraphQLMockResponse(
        operation_name="CreatePost",
        operation_type=GraphQLOperationType.MUTATION,
        query="mutation CreatePost($input: CreatePostInput!) { createPost(input: $input) { id title content author { id name } } }",
        response_data={
            "createPost": {
                "id": "{{post_id}}",
                "title": title,
                "content": content,
                "author": {
                    "id": "{{author_id}}",
                    "name": "{{author_name}}"
                }
            }
        }
    )


def create_subscription_mock(topic: str = "updates") -> GraphQLMockResponse:
    """Create a mock response for subscription"""
    return GraphQLMockResponse(
        operation_name="SubscribeToUpdates",
        operation_type=GraphQLOperationType.SUBSCRIPTION,
        query="subscription SubscribeToUpdates { subscriptionUpdate { id timestamp message } }",
        response_data={
            "subscriptionUpdate": {
                "id": "{{update_id}}",
                "timestamp": "{{timestamp}}",
                "message": f"Update for {topic}"
            }
        }
    )
