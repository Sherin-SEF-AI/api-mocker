import pytest
import asyncio
import os
from api_mocker.database_integration import (
    SQLiteManager, DatabaseConfig, DatabaseType, 
    QueryCondition, QueryOperator
)

DB_PATH = "test_api_mocker.db"

@pytest.fixture
async def sqlite_manager():
    """Fixture for SQLiteManager"""
    manager = SQLiteManager(db_path=DB_PATH)
    yield manager
    # Cleanup
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)

@pytest.mark.asyncio
async def test_sqlite_lifecycle(sqlite_manager):
    """Test full lifecycle: Create Table, Insert, Select, Update, Delete"""
    
    # 1. Create Table
    schema = {
        "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
        "name": "TEXT",
        "age": "INTEGER"
    }
    await sqlite_manager.create_table("users", schema)
    
    # 2. Insert
    user_id = await sqlite_manager.insert_record("users", {"name": "Test User", "age": 30})
    assert user_id == 1
    
    # 3. Select (Execute Query)
    users = await sqlite_manager.execute_query("SELECT * FROM users WHERE id = ?", (user_id,))
    assert len(users) == 1
    assert users[0]["name"] == "Test User"
    assert users[0]["age"] == 30
    
    # 4. Update
    conditions = [QueryCondition("id", QueryOperator.EQ, user_id)]
    updated_rows = await sqlite_manager.update_record("users", {"age": 31}, conditions)
    assert updated_rows == 1
    
    # Verify Update
    users = await sqlite_manager.execute_query("SELECT * FROM users WHERE id = ?", (user_id,))
    assert users[0]["age"] == 31
    
    # 5. Delete
    deleted_rows = await sqlite_manager.delete_record("users", conditions)
    assert deleted_rows == 1
    
    # Verify Delete
    users = await sqlite_manager.execute_query("SELECT * FROM users WHERE id = ?", (user_id,))
    assert len(users) == 0

@pytest.mark.asyncio
async def test_sql_injection_protection(sqlite_manager):
    """Test that SQL injection attempts in conditions are neutralized"""
    
    # Setup
    await sqlite_manager.create_table("items", {"id": "INTEGER PRIMARY KEY", "name": "TEXT"})
    await sqlite_manager.insert_record("items", {"name": "Safe Item"})
    
    # Attempt Injection via Value
    # This should look for name = "' OR '1'='1" literallly, not execute it
    injection_attempt = "' OR '1'='1"
    conditions = [QueryCondition("name", QueryOperator.EQ, injection_attempt)]
    
    rows = await sqlite_manager.execute_query(
        f"SELECT * FROM items WHERE name = ?", (injection_attempt,)
    )
    # Should find nothing because "Safe Item" != "' OR '1'='1"
    assert len(rows) == 0
    
    # More importantly, let's check update_record which builds the query
    # We want to ensure update_record behaves safely.
    # update_record uses _build_where_clause which uses parameters.
    
    # Try to verify that _build_where_clause produces parameterized query
    where_clause, params = sqlite_manager._build_where_clause(conditions)
    assert "?" in where_clause
    assert injection_attempt in params
    assert "'" not in where_clause # The injection string should NOT be in the SQL string

@pytest.mark.asyncio
async def test_complex_conditions(sqlite_manager):
    """Test complex query conditions (AND, IN, LIKE)"""
    # Setup
    await sqlite_manager.create_table("products", {"id": "INTEGER PRIMARY KEY", "category": "TEXT", "price": "INTEGER"})
    await sqlite_manager.insert_record("products", {"category": "electronics", "price": 100})
    await sqlite_manager.insert_record("products", {"category": "electronics", "price": 200})
    await sqlite_manager.insert_record("products", {"category": "books", "price": 50})
    
    # Test IN operator
    conditions = [
        QueryCondition("category", QueryOperator.IN, ["electronics", "books"]),
        QueryCondition("price", QueryOperator.GT, 150) # Should match only the 200 one
    ]
    
    # We don't have a generic "select" method in SQLiteManager exposed nicely for arbitrary conditions
    # except via manual query. BUT update_record and delete_record uses it.
    # Let's test _build_where_clause directly mostly, or use delete with complex conditions
    
    where_clause, params = sqlite_manager._build_where_clause(conditions)
    
    query = f"SELECT * FROM products WHERE {where_clause}"
    results = await sqlite_manager.execute_query(query, params)
    
    assert len(results) == 1
    assert results[0]["price"] == 200

@pytest.mark.asyncio
async def test_postgres_manager_mock():
    """Test PostgresManager using mocks"""
    from unittest.mock import MagicMock, AsyncMock, patch
    from api_mocker.database_integration import PostgreSQLManager, DatabaseConfig, DatabaseType
    
    config = DatabaseConfig(DatabaseType.POSTGRESQL, "localhost", 5432, "test", "user", "pass")
    manager = PostgreSQLManager(config)
    
    # Mock pool should be MagicMock because acquire() is not awaited itself, 
    # the result of acquire() is used in 'async with'
    mock_pool = MagicMock()
    mock_conn = AsyncMock()
    
    # Setup connection context manager mock
    # async with pool.acquire() as conn
    # pool.acquire() returns object with __aenter__
    mock_context_manager = AsyncMock()
    mock_context_manager.__aenter__.return_value = mock_conn
    mock_pool.acquire.return_value = mock_context_manager
    
    # Setup execute return value (asyncpg returns "UPDATE N" string)
    mock_conn.execute.return_value = "UPDATE 1"

    # Patch asyncpg.create_pool
    # create_pool IS awaited, so it returns the pool via AsyncMock
    with patch("asyncpg.create_pool", new=AsyncMock(return_value=mock_pool)) as mock_create:
        await manager.initialize()
        mock_create.assert_called_once()
        
        # Test generic execute
        rows_affected = await manager.execute_update("UPDATE table SET x=1")
        mock_conn.execute.assert_called_with("UPDATE table SET x=1")
        assert rows_affected == 1

