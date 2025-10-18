"""
Database Integration System

This module provides comprehensive database integration capabilities including:
- SQLite, PostgreSQL, and MongoDB support
- Connection pooling and management
- Query builders and ORM-like functionality
- Database migrations and schema management
- Transaction support
- Caching and performance optimization
"""

import sqlite3
import asyncio
import json
from typing import Any, Dict, List, Optional, Union, Callable, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import threading
from contextlib import asynccontextmanager
import aiosqlite
import asyncpg
import motor.motor_asyncio
from pymongo import MongoClient
import redis
import pickle


class DatabaseType(Enum):
    """Database types"""
    SQLITE = "sqlite"
    POSTGRESQL = "postgresql"
    MONGODB = "mongodb"
    REDIS = "redis"


class QueryOperator(Enum):
    """Query operators"""
    EQ = "="
    NE = "!="
    GT = ">"
    GTE = ">="
    LT = "<"
    LTE = "<="
    LIKE = "LIKE"
    IN = "IN"
    NOT_IN = "NOT IN"
    IS_NULL = "IS NULL"
    IS_NOT_NULL = "IS NOT NULL"


@dataclass
class DatabaseConfig:
    """Database configuration"""
    db_type: DatabaseType
    host: str = "localhost"
    port: int = 5432
    database: str = "api_mocker"
    username: str = ""
    password: str = ""
    connection_pool_size: int = 10
    max_connections: int = 100
    timeout: int = 30
    ssl_mode: str = "prefer"
    additional_params: Dict[str, Any] = field(default_factory=dict)


@dataclass
class QueryCondition:
    """Query condition"""
    field: str
    operator: QueryOperator
    value: Any
    logical_operator: str = "AND"  # AND, OR


@dataclass
class QueryBuilder:
    """Query builder for database operations"""
    table: str
    conditions: List[QueryCondition] = field(default_factory=list)
    fields: List[str] = field(default_factory=list)
    order_by: List[str] = field(default_factory=list)
    limit: Optional[int] = None
    offset: Optional[int] = None
    joins: List[Dict[str, str]] = field(default_factory=list)
    group_by: List[str] = field(default_factory=list)
    having: List[QueryCondition] = field(default_factory=list)


class SQLiteManager:
    """SQLite database manager"""
    
    def __init__(self, db_path: str = "api_mocker.db"):
        self.db_path = db_path
        self.connection_pool = []
        self.pool_lock = threading.Lock()
        self.max_connections = 10
    
    async def get_connection(self) -> aiosqlite.Connection:
        """Get a database connection from the pool"""
        with self.pool_lock:
            if self.connection_pool:
                return self.connection_pool.pop()
            else:
                return await aiosqlite.connect(self.db_path)
    
    async def return_connection(self, conn: aiosqlite.Connection) -> None:
        """Return a connection to the pool"""
        with self.pool_lock:
            if len(self.connection_pool) < self.max_connections:
                self.connection_pool.append(conn)
            else:
                await conn.close()
    
    async def execute_query(self, query: str, params: Tuple = ()) -> List[Dict[str, Any]]:
        """Execute a query and return results"""
        conn = await self.get_connection()
        try:
            cursor = await conn.execute(query, params)
            rows = await cursor.fetchall()
            columns = [description[0] for description in cursor.description] if cursor.description else []
            return [dict(zip(columns, row)) for row in rows]
        finally:
            await self.return_connection(conn)
    
    async def execute_update(self, query: str, params: Tuple = ()) -> int:
        """Execute an update query and return affected rows"""
        conn = await self.get_connection()
        try:
            cursor = await conn.execute(query, params)
            await conn.commit()
            return cursor.rowcount
        finally:
            await self.return_connection(conn)
    
    async def create_table(self, table_name: str, schema: Dict[str, str]) -> None:
        """Create a table with the given schema"""
        columns = [f"{name} {type_def}" for name, type_def in schema.items()]
        query = f"CREATE TABLE IF NOT EXISTS {table_name} ({', '.join(columns)})"
        await self.execute_update(query)
    
    async def insert_record(self, table_name: str, data: Dict[str, Any]) -> int:
        """Insert a record and return the ID"""
        fields = list(data.keys())
        placeholders = ["?" for _ in fields]
        query = f"INSERT INTO {table_name} ({', '.join(fields)}) VALUES ({', '.join(placeholders)})"
        params = tuple(data.values())
        
        conn = await self.get_connection()
        try:
            cursor = await conn.execute(query, params)
            await conn.commit()
            return cursor.lastrowid
        finally:
            await self.return_connection(conn)
    
    async def update_record(self, table_name: str, data: Dict[str, Any], 
                           conditions: List[QueryCondition]) -> int:
        """Update records based on conditions"""
        set_clause = ", ".join([f"{field} = ?" for field in data.keys()])
        where_clause, params = self._build_where_clause(conditions)
        
        query = f"UPDATE {table_name} SET {set_clause} WHERE {where_clause}"
        all_params = tuple(data.values()) + params
        
        return await self.execute_update(query, all_params)
    
    async def delete_record(self, table_name: str, conditions: List[QueryCondition]) -> int:
        """Delete records based on conditions"""
        where_clause, params = self._build_where_clause(conditions)
        query = f"DELETE FROM {table_name} WHERE {where_clause}"
        return await self.execute_update(query, params)
    
    def _build_where_clause(self, conditions: List[QueryCondition]) -> Tuple[str, Tuple]:
        """Build WHERE clause from conditions"""
        if not conditions:
            return "1=1", ()
        
        clauses = []
        params = []
        
        for i, condition in enumerate(conditions):
            if i > 0:
                clauses.append(condition.logical_operator)
            
            if condition.operator == QueryOperator.EQ:
                clauses.append(f"{condition.field} = ?")
                params.append(condition.value)
            elif condition.operator == QueryOperator.NE:
                clauses.append(f"{condition.field} != ?")
                params.append(condition.value)
            elif condition.operator == QueryOperator.LIKE:
                clauses.append(f"{condition.field} LIKE ?")
                params.append(condition.value)
            elif condition.operator == QueryOperator.IN:
                placeholders = ",".join(["?" for _ in condition.value])
                clauses.append(f"{condition.field} IN ({placeholders})")
                params.extend(condition.value)
            elif condition.operator == QueryOperator.IS_NULL:
                clauses.append(f"{condition.field} IS NULL")
            elif condition.operator == QueryOperator.IS_NOT_NULL:
                clauses.append(f"{condition.field} IS NOT NULL")
        
        return " ".join(clauses), tuple(params)


class PostgreSQLManager:
    """PostgreSQL database manager"""
    
    def __init__(self, config: DatabaseConfig):
        self.config = config
        self.pool = None
    
    async def initialize(self) -> None:
        """Initialize the connection pool"""
        self.pool = await asyncpg.create_pool(
            host=self.config.host,
            port=self.config.port,
            database=self.config.database,
            user=self.config.username,
            password=self.config.password,
            min_size=1,
            max_size=self.config.connection_pool_size,
            command_timeout=self.config.timeout
        )
    
    async def execute_query(self, query: str, *params) -> List[Dict[str, Any]]:
        """Execute a query and return results"""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query, *params)
            return [dict(row) for row in rows]
    
    async def execute_update(self, query: str, *params) -> int:
        """Execute an update query and return affected rows"""
        async with self.pool.acquire() as conn:
            result = await conn.execute(query, *params)
            return int(result.split()[-1])
    
    async def close(self) -> None:
        """Close the connection pool"""
        if self.pool:
            await self.pool.close()


class MongoDBManager:
    """MongoDB database manager"""
    
    def __init__(self, config: DatabaseConfig):
        self.config = config
        self.client = None
        self.database = None
    
    async def initialize(self) -> None:
        """Initialize MongoDB connection"""
        connection_string = f"mongodb://{self.config.username}:{self.config.password}@{self.config.host}:{self.config.port}/{self.config.database}"
        self.client = motor.motor_asyncio.AsyncIOMotorClient(connection_string)
        self.database = self.client[self.config.database]
    
    async def insert_document(self, collection: str, document: Dict[str, Any]) -> str:
        """Insert a document and return the ID"""
        result = await self.database[collection].insert_one(document)
        return str(result.inserted_id)
    
    async def find_documents(self, collection: str, filter_dict: Dict[str, Any] = None,
                            limit: int = None, skip: int = None) -> List[Dict[str, Any]]:
        """Find documents in a collection"""
        cursor = self.database[collection].find(filter_dict or {})
        
        if skip:
            cursor = cursor.skip(skip)
        if limit:
            cursor = cursor.limit(limit)
        
        documents = await cursor.to_list(length=limit or 1000)
        return documents
    
    async def update_document(self, collection: str, filter_dict: Dict[str, Any],
                             update_dict: Dict[str, Any]) -> int:
        """Update documents in a collection"""
        result = await self.database[collection].update_many(filter_dict, {"$set": update_dict})
        return result.modified_count
    
    async def delete_document(self, collection: str, filter_dict: Dict[str, Any]) -> int:
        """Delete documents from a collection"""
        result = await self.database[collection].delete_many(filter_dict)
        return result.deleted_count
    
    async def create_index(self, collection: str, index_spec: Dict[str, Any]) -> str:
        """Create an index on a collection"""
        result = await self.database[collection].create_index(list(index_spec.items()))
        return result
    
    async def close(self) -> None:
        """Close MongoDB connection"""
        if self.client:
            self.client.close()


class RedisManager:
    """Redis database manager"""
    
    def __init__(self, config: DatabaseConfig):
        self.config = config
        self.redis_client = None
    
    async def initialize(self) -> None:
        """Initialize Redis connection"""
        self.redis_client = redis.Redis(
            host=self.config.host,
            port=self.config.port,
            db=0,
            decode_responses=True
        )
    
    async def set(self, key: str, value: Any, expire: int = None) -> bool:
        """Set a key-value pair"""
        if isinstance(value, (dict, list)):
            value = json.dumps(value)
        return self.redis_client.set(key, value, ex=expire)
    
    async def get(self, key: str) -> Any:
        """Get a value by key"""
        value = self.redis_client.get(key)
        if value is None:
            return None
        
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value
    
    async def delete(self, key: str) -> bool:
        """Delete a key"""
        return bool(self.redis_client.delete(key))
    
    async def exists(self, key: str) -> bool:
        """Check if a key exists"""
        return bool(self.redis_client.exists(key))
    
    async def expire(self, key: str, seconds: int) -> bool:
        """Set expiration for a key"""
        return bool(self.redis_client.expire(key, seconds))
    
    async def close(self) -> None:
        """Close Redis connection"""
        if self.redis_client:
            self.redis_client.close()


class DatabaseManager:
    """Main database manager that handles multiple database types"""
    
    def __init__(self):
        self.managers: Dict[DatabaseType, Any] = {}
        self.configs: Dict[DatabaseType, DatabaseConfig] = {}
    
    def add_database(self, db_type: DatabaseType, config: DatabaseConfig) -> None:
        """Add a database configuration"""
        self.configs[db_type] = config
        
        if db_type == DatabaseType.SQLITE:
            self.managers[db_type] = SQLiteManager(config.database)
        elif db_type == DatabaseType.POSTGRESQL:
            self.managers[db_type] = PostgreSQLManager(config)
        elif db_type == DatabaseType.MONGODB:
            self.managers[db_type] = MongoDBManager(config)
        elif db_type == DatabaseType.REDIS:
            self.managers[db_type] = RedisManager(config)
    
    async def initialize_all(self) -> None:
        """Initialize all configured databases"""
        for db_type, manager in self.managers.items():
            if hasattr(manager, 'initialize'):
                await manager.initialize()
    
    async def close_all(self) -> None:
        """Close all database connections"""
        for manager in self.managers.values():
            if hasattr(manager, 'close'):
                await manager.close()
    
    def get_manager(self, db_type: DatabaseType):
        """Get a database manager by type"""
        return self.managers.get(db_type)
    
    async def execute_sqlite_query(self, query: str, params: Tuple = ()) -> List[Dict[str, Any]]:
        """Execute a SQLite query"""
        manager = self.get_manager(DatabaseType.SQLITE)
        if manager:
            return await manager.execute_query(query, params)
        return []
    
    async def execute_postgresql_query(self, query: str, *params) -> List[Dict[str, Any]]:
        """Execute a PostgreSQL query"""
        manager = self.get_manager(DatabaseType.POSTGRESQL)
        if manager:
            return await manager.execute_query(query, *params)
        return []
    
    async def insert_mongodb_document(self, collection: str, document: Dict[str, Any]) -> str:
        """Insert a MongoDB document"""
        manager = self.get_manager(DatabaseType.MONGODB)
        if manager:
            return await manager.insert_document(collection, document)
        return ""
    
    async def set_redis_value(self, key: str, value: Any, expire: int = None) -> bool:
        """Set a Redis value"""
        manager = self.get_manager(DatabaseType.REDIS)
        if manager:
            return await manager.set(key, value, expire)
        return False
    
    async def get_redis_value(self, key: str) -> Any:
        """Get a Redis value"""
        manager = self.get_manager(DatabaseType.REDIS)
        if manager:
            return await manager.get(key)
        return None


class DatabaseMigration:
    """Database migration system"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.migrations: List[Dict[str, Any]] = []
    
    def add_migration(self, version: str, description: str, 
                     up_sql: str, down_sql: str = None) -> None:
        """Add a migration"""
        migration = {
            "version": version,
            "description": description,
            "up_sql": up_sql,
            "down_sql": down_sql,
            "applied": False
        }
        self.migrations.append(migration)
    
    async def run_migrations(self) -> None:
        """Run all pending migrations"""
        # Create migrations table if it doesn't exist
        await self._create_migrations_table()
        
        # Get applied migrations
        applied_migrations = await self._get_applied_migrations()
        
        # Run pending migrations
        for migration in self.migrations:
            if migration["version"] not in applied_migrations:
                await self._apply_migration(migration)
    
    async def _create_migrations_table(self) -> None:
        """Create migrations tracking table"""
        sql = """
        CREATE TABLE IF NOT EXISTS migrations (
            version TEXT PRIMARY KEY,
            description TEXT,
            applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        await self.db_manager.execute_sqlite_query(sql)
    
    async def _get_applied_migrations(self) -> List[str]:
        """Get list of applied migrations"""
        result = await self.db_manager.execute_sqlite_query(
            "SELECT version FROM migrations ORDER BY applied_at"
        )
        return [row["version"] for row in result]
    
    async def _apply_migration(self, migration: Dict[str, Any]) -> None:
        """Apply a migration"""
        try:
            # Execute up SQL
            await self.db_manager.execute_sqlite_query(migration["up_sql"])
            
            # Record migration
            await self.db_manager.execute_sqlite_query(
                "INSERT INTO migrations (version, description) VALUES (?, ?)",
                (migration["version"], migration["description"])
            )
            
            print(f"Applied migration: {migration['version']} - {migration['description']}")
        except Exception as e:
            print(f"Error applying migration {migration['version']}: {e}")
            raise


# Global database manager instance
db_manager = DatabaseManager()


# Convenience functions
async def setup_sqlite_database(db_path: str = "api_mocker.db") -> None:
    """Setup SQLite database with default tables"""
    config = DatabaseConfig(
        db_type=DatabaseType.SQLITE,
        database=db_path
    )
    db_manager.add_database(DatabaseType.SQLITE, config)
    await db_manager.initialize_all()
    
    # Create default tables
    sqlite_manager = db_manager.get_manager(DatabaseType.SQLITE)
    if sqlite_manager:
        await sqlite_manager.create_table("users", {
            "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
            "username": "TEXT UNIQUE NOT NULL",
            "email": "TEXT UNIQUE NOT NULL",
            "created_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
        })
        
        await sqlite_manager.create_table("api_requests", {
            "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
            "method": "TEXT NOT NULL",
            "path": "TEXT NOT NULL",
            "headers": "TEXT",
            "body": "TEXT",
            "response_status": "INTEGER",
            "response_body": "TEXT",
            "created_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
        })


async def setup_postgresql_database(host: str, port: int, database: str, 
                                  username: str, password: str) -> None:
    """Setup PostgreSQL database"""
    config = DatabaseConfig(
        db_type=DatabaseType.POSTGRESQL,
        host=host,
        port=port,
        database=database,
        username=username,
        password=password
    )
    db_manager.add_database(DatabaseType.POSTGRESQL, config)
    await db_manager.initialize_all()


async def setup_mongodb_database(host: str, port: int, database: str,
                                username: str = "", password: str = "") -> None:
    """Setup MongoDB database"""
    config = DatabaseConfig(
        db_type=DatabaseType.MONGODB,
        host=host,
        port=port,
        database=database,
        username=username,
        password=password
    )
    db_manager.add_database(DatabaseType.MONGODB, config)
    await db_manager.initialize_all()


async def setup_redis_database(host: str = "localhost", port: int = 6379) -> None:
    """Setup Redis database"""
    config = DatabaseConfig(
        db_type=DatabaseType.REDIS,
        host=host,
        port=port
    )
    db_manager.add_database(DatabaseType.REDIS, config)
    await db_manager.initialize_all()
