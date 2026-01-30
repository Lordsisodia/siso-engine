"""
Blackbox4 Brain v2.0 - Database Connection Module
Handles async PostgreSQL connections and operations.
"""

import os
from typing import Optional
from contextlib import asynccontextmanager
import asyncpg
from dotenv import load_dotenv

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(__file__), 'databases', '.env'))


class DatabaseConfig:
    """Database configuration from environment."""

    def __init__(self):
        self.host = os.getenv('POSTGRES_HOST', 'localhost')
        self.port = int(os.getenv('POSTGRES_PORT', 5432))
        self.database = os.getenv('POSTGRES_DB', 'blackbox4_brain')
        self.user = os.getenv('POSTGRES_USER', 'blackbox4')
        self.password = os.getenv('POSTGRES_PASSWORD', 'blackbox4_brain_pass')
        self.min_size = int(os.getenv('CONNECTION_POOL_SIZE', 10))
        self.max_size = self.min_size * 2

    @property
    def dsn(self) -> str:
        """Get data source name."""
        return f'postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}'


class Database:
    """Async PostgreSQL connection pool manager."""

    _pool: Optional[asyncpg.Pool] = None
    _config: Optional[DatabaseConfig] = None

    @classmethod
    async def initialize(cls, config: Optional[DatabaseConfig] = None):
        """Initialize connection pool."""
        if cls._pool is not None:
            return

        cls._config = config or DatabaseConfig()

        try:
            cls._pool = await asyncpg.create_pool(
                host=cls._config.host,
                port=cls._config.port,
                user=cls._config.user,
                password=cls._config.password,
                database=cls._config.database,
                min_size=cls._config.min_size,
                max_size=cls._config.max_size,
                command_timeout=60,
            )
            print(f"✓ Connected to PostgreSQL at {cls._config.host}:{cls._config.port}")
        except Exception as e:
            print(f"✗ Failed to connect to PostgreSQL: {e}")
            raise

    @classmethod
    async def close(cls):
        """Close connection pool."""
        if cls._pool:
            await cls._pool.close()
            cls._pool = None
            print("✓ PostgreSQL connection closed")

    @classmethod
    @asynccontextmanager
    async def connection(cls):
        """Get connection from pool."""
        if cls._pool is None:
            await cls.initialize()

        async with cls._pool.acquire() as conn:
            yield conn

    @classmethod
    async def execute(cls, query: str, *args, fetch: str = None):
        """Execute a query.

        Args:
            query: SQL query
            *args: Query parameters
            fetch: One of 'one', 'all', 'val', or None (for no return)

        Returns:
            Query result based on fetch parameter
        """
        async with cls.connection() as conn:
            if fetch == 'val':
                result = await conn.fetchval(query, *args)
            elif fetch == 'one':
                result = await conn.fetchrow(query, *args)
            elif fetch == 'all':
                result = await conn.fetch(query, *args)
            else:
                result = await conn.execute(query, *args)

            return result

    @classmethod
    async def executemany(cls, query: str, args_list: list):
        """Execute query multiple times.

        Args:
            query: SQL query
            args_list: List of parameter tuples
        """
        async with cls.connection() as conn:
            await conn.executemany(query, args_list)

    @classmethod
    async def transaction(cls):
        """Get transaction context."""
        if cls._pool is None:
            await cls.initialize()

        return cls._pool.transaction()


# Convenience functions
async def init_db(config: Optional[DatabaseConfig] = None):
    """Initialize database connection."""
    await Database.initialize(config)


async def close_db():
    """Close database connection."""
    await Database.close()


async def execute_query(query: str, *args, fetch: str = None):
    """Execute a query."""
    return await Database.execute(query, *args, fetch=fetch)


async def execute_many(query: str, args_list: list):
    """Execute query multiple times."""
    await Database.executemany(query, args_list)
