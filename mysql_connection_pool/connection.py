import mysql.connector.pooling
import threading
from typing import Optional, Dict, Any, Tuple, Union, List
import os
import sqlparse


class MySQLConnectionPool:
    """
    A thread-safe MySQL connection pool manager with database switching capability.
    
    Provides a high-level interface for executing SQL queries with automatic:
    - Connection pooling
    - Resource cleanup (cursors and connections)
    - Transaction management
    - Automatic reconnection
    - Database switching
    
    Class Attributes:
        _pool: MySQLConnectionPool - Shared connection pool
        _lock: threading.Lock - Lock for thread-safe pool initialization
        _dictionary: bool - Whether to return results as dictionaries
        _instance: MySQLConnectionPool - Singleton instance
    
    Basic Usage:
        >>> from mysql_connection_pool import MySQLConnectionPool
        >>> db = MySQLConnectionPool(host='localhost', user='root', database='test')
        >>> results = db.fetchall("SELECT * FROM users")
        >>> db.switch_database('new_database')  # Switch to a different database
    """
    
    _pool: mysql.connector.pooling.MySQLConnectionPool = None
    _lock: threading.Lock = threading.Lock()
    _dictionary: bool = True
    _instance = None
    _current_database: Optional[str] = None
    _connection_params: Dict[str, Any] = {}

    def __init__(
        self,
        host: str = "localhost",
        port: int = 3306,
        user: Optional[str] = None,
        password: Optional[str] = None,
        database: Optional[str] = None,
        dictionary: bool = True,
        pool_name: str = "mysql_pool",
        pool_size: int = 5,
        **kwargs
    ):
        """
        Initialize the connection pool (once per application).
        
        Args:
            host: MySQL server host
            port: MySQL port (default 3306)
            user: MySQL username
            password: MySQL password
            database: Database to use
            dictionary: If True, returns results as dicts
            pool_name: Pool identifier name
            pool_size: Maximum connections in pool
            **kwargs: Additional connection parameters
            
        Raises:
            mysql.connector.Error: If initial connection fails
        """
        with MySQLConnectionPool._lock:
            if MySQLConnectionPool._pool is None:
                MySQLConnectionPool._dictionary = dictionary
                MySQLConnectionPool._current_database = database
                MySQLConnectionPool._connection_params = {
                    'host': host,
                    'port': port,
                    'user': user,
                    'password': password,
                    'database': database,
                    'pool_name': pool_name,
                    'pool_size': pool_size,
                    'autocommit': True,
                    'pool_reset_session': True,
                }
                MySQLConnectionPool._connection_params.update(kwargs)
                
                MySQLConnectionPool._pool = mysql.connector.pooling.MySQLConnectionPool(
                    **MySQLConnectionPool._connection_params
                )
                MySQLConnectionPool._instance = self

    def switch_database(self, database: str) -> None:
        """
        Switch to a different database for all subsequent queries.
        
        Args:
            database: Name of the database to switch to
            
        Raises:
            mysql.connector.Error: If database doesn't exist or connection fails
            ValueError: If database name contains invalid characters
        """
        if not self._validate_db_name(database):
            raise ValueError("Invalid database name. Only alphanumeric characters and underscores are allowed.")
            
        conn = self._get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(f"USE `{database}`")
                MySQLConnectionPool._current_database = database
                # Update connection params for new connections
                MySQLConnectionPool._connection_params['database'] = database
        finally:
            conn.close()

    def _validate_db_name(self, name: str) -> bool:
        """Validate database name to prevent SQL injection"""
        return all(c.isalnum() or c == '_' for c in name)

    def get_current_database(self) -> Optional[str]:
        """
        Get the name of the currently active database.
        
        Returns:
            str: Current database name or None if not connected to any database
        """
        return self._current_database

    def _get_connection(self) -> mysql.connector.connection.MySQLConnection:
        """
        Get a connection from the pool and ensure it's using the correct database.
        
        Returns:
            MySQLConnection: Active connection
            
        Raises:
            PoolError: If no connections available after timeout
        """
        conn = self._pool.get_connection()
        if self._current_database:
            try:
                with conn.cursor() as cursor:
                    cursor.execute(f"USE `{self._current_database}`")
            except Exception:
                conn.close()
                raise
        return conn

    def _normalize_params(self, params):
        """Helper to normalize query parameters for cursor.execute."""
        if params is None:
            return None
        if isinstance(params, (tuple, list, dict)):
            return params
        # Single value, wrap in tuple
        return (params,)

    def execute(
        self, 
        query: str, 
        params: Optional[Union[Tuple, Dict]] = None,
        database: Optional[str] = None
    ) -> Tuple['mysql.connector.cursor.MySQLCursor', 'mysql.connector.connection.MySQLConnection']:
        """
        Execute SQL query and return cursor and connection.
        
        Note: Caller MUST close the connection manually.
        
        Args:
            query: SQL query with optional parameters (%s or %(name)s)
            params: Query parameters
            database: Optional database to use for this query
            
        Returns:
            Tuple (cursor, connection) - You must call connection.close() after
            
        Example:
            >>> cursor, conn = db.execute("SELECT * FROM users WHERE id = %s", (1,))
            >>> try:
            ...     results = cursor.fetchall()
            ... finally:
            ...     conn.close()
        """
        conn = self._get_connection()
        if database:
            with conn.cursor() as cursor:
                cursor.execute(f"USE `{database}`")
        cursor = conn.cursor(dictionary=self._dictionary)
        norm_params = self._normalize_params(params)
        if norm_params is not None:
            cursor.execute(query, norm_params)
        else:
            cursor.execute(query)
        return cursor, conn

    def execute_safe(
        self,
        query: str,
        params: Optional[Union[Tuple, Dict]] = None,
        database: Optional[str] = None
    ) -> Optional[List[Dict]]:
        """
        Execute query and automatically close resources.
        
        Args:
            query: SQL query
            params: Query parameters
            database: Optional database to use for this query
            
        Returns:
            Tuple (cursor, results) - results is None for non-result queries
            
        Example:
            >>> _, results = db.execute_safe("SELECT * FROM products", database='inventory')
        """
        conn = self._get_connection()
        try:
            if database:
                with conn.cursor() as cursor:
                    cursor.execute(f"USE `{database}`")
            with conn.cursor(dictionary=self._dictionary) as cursor:
                norm_params = self._normalize_params(params)
                if norm_params is not None:
                    cursor.execute(query, norm_params)
                else:
                    cursor.execute(query)
                results = cursor.fetchall() if cursor.with_rows else None
                return results
        finally:
            conn.close()

    def fetchone(
        self,
        query: str,
        params: Optional[Union[Tuple, Dict]] = None,
        database: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Execute query and return a single row.
        
        Args:
            query: SQL query
            params: Query parameters
            database: Optional database to use for this query
            
        Returns:
            Dict with row data or None if no results
            
        Example:
            >>> user = db.fetchone("SELECT * FROM users WHERE id = %s", (1,), database='auth_db')
        """
        conn = self._get_connection()
        try:
            if database:
                with conn.cursor() as cursor:
                    cursor.execute(f"USE `{database}`")
            with conn.cursor(dictionary=self._dictionary) as cursor:
                norm_params = self._normalize_params(params)
                if norm_params is not None:
                    cursor.execute(query, norm_params)
                else:
                    cursor.execute(query)
                return cursor.fetchone()
        finally:
            conn.close()

    def fetchall(
        self,
        query: str,
        params: Optional[Union[Tuple, Dict]] = None,
        database: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Execute query and return all rows.
        
        Args:
            query: SQL query
            params: Query parameters
            database: Optional database to use for this query
            
        Returns:
            List[Dict] with results
            
        Example:
            >>> products = db.fetchall("SELECT * FROM products", database='store_db')
        """
        conn = self._get_connection()
        try:
            if database:
                with conn.cursor() as cursor:
                    cursor.execute(f"USE `{database}`")
            with conn.cursor(dictionary=self._dictionary) as cursor:
                norm_params = self._normalize_params(params)
                if norm_params is not None:
                    cursor.execute(query, norm_params)
                else:
                    cursor.execute(query)
                return cursor.fetchall()
        finally:
            conn.close()

    def commit_execute(
        self,
        query: str,
        params: Optional[Union[Tuple, Dict]] = None,
        database: Optional[str] = None
    ) -> Tuple[int, Optional[int]]:
        """
        Execute write query and commit.
        
        Args:
            query: SQL query (INSERT/UPDATE/DELETE)
            params: Query parameters
            database: Optional database to use for this query
            
        Returns:
            Tuple (rowcount, lastrowid)
            
        Example:
            >>> count, last_id = db.commit_execute(
            ...     "INSERT INTO logs (message) VALUES (%s)",
            ...     ("Error 404",),
            ...     database='logging_db'
            ... )
        """
        conn = self._get_connection()
        try:
            if database:
                with conn.cursor() as cursor:
                    cursor.execute(f"USE `{database}`")
            with conn.cursor(dictionary=self._dictionary) as cursor:
                norm_params = self._normalize_params(params)
                if norm_params is not None:
                    cursor.execute(query, norm_params)
                else:
                    cursor.execute(query)
                conn.commit()
                return cursor.rowcount, cursor.lastrowid
        finally:
            conn.close()

    @staticmethod
    def lastrowid(cursor: mysql.connector.cursor.MySQLCursor) -> Optional[int]:
        """Return the ID of the last inserted row."""
        return cursor.lastrowid

    @staticmethod
    def rowcount(cursor: mysql.connector.cursor.MySQLCursor) -> int:
        """Return the number of affected rows."""
        return cursor.rowcount

    @classmethod
    def is_initialized(cls) -> bool:
        """Check if the pool has been initialized."""
        return cls._pool is not None

    @classmethod
    def get_instance(cls):
        """Get the singleton instance."""
        if not cls._pool or not cls._instance:
            raise RuntimeError("Pool not initialized. Call __init__ first.")
        return cls._instance
    
    @staticmethod
    def run_sql_file(file_path: str) -> None:
        """
        Execute SQL commands from a file.
        
        Args:
            file_path: Path to the SQL file
            
        Raises:
            FileNotFoundError: If the file does not exist
            mysql.connector.Error: If execution fails
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"SQL file not found: {file_path}")
        
        with open(file_path, 'r') as file:
            sql_script = file.read()

        statements = sqlparse.parse(sql_script)
        statements = [str(stmt).strip() for stmt in statements if str(stmt).strip()]
        
        if not statements:
            raise ValueError("No valid SQL statements found in the file.")

        db = MySQLConnectionPool.get_instance()
        for stmt in statements:
            db.execute_safe(stmt)

    @staticmethod
    def run_multiple_sql_files(file_paths: List[str]) -> None:
        """
        Execute multiple SQL files in order.
        
        Args:
            file_paths: List of paths to SQL files
        """
        
        db = MySQLConnectionPool.get_instance()
        for file_path in file_paths:
            db.run_sql_file(file_path)

    @staticmethod
    def run_multiple_sql_files_from_directory(base_dir: str, file_names: List[str]) -> None:
        """
        Execute multiple SQL files from a directory.
        
        Args:
            base_dir: Directory containing SQL files
            file_names: List of SQL file names to execute
        """
        file_paths = [os.path.join(base_dir, name).replace("\\", "/") for name in file_names]
        
        db = MySQLConnectionPool.get_instance()
        db.run_multiple_sql_files(file_paths)