import mysql.connector.pooling
import threading
from typing import Optional, Dict, Any, Tuple, Union, List


class MySQLConnectionPool:
    """
    A thread-safe MySQL connection pool manager.
    
    Provides a high-level interface for executing SQL queries with automatic:
    - Connection pooling
    - Resource cleanup (cursors and connections)
    - Transaction management
    - Automatic reconnection
    
    Class Attributes:
        _pool: MySQLConnectionPool - Shared connection pool
        _lock: threading.Lock - Lock for thread-safe pool initialization
        _dictionary: bool - Whether to return results as dictionaries
    
    Basic Usage:
        >>> from mysql_connection_pool import MySQLConnectionPool
        >>> db = MySQLConnectionPool(host='localhost', user='root', database='test')
        >>> results = db.fetchall("SELECT * FROM users")
    """
    
    _pool: mysql.connector.pooling.MySQLConnectionPool = None
    _lock: threading.Lock = threading.Lock()
    _dictionary: bool = True

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
                
                config = {
                    'pool_name': pool_name,
                    'pool_size': pool_size,
                    'host': host,
                    'port': port,
                    'user': user,
                    'password': password,
                    'database': database,
                    'autocommit': True,
                    'pool_reset_session': True,
                }
                
                # Add additional kwargs to config
                config.update(kwargs)
                
                MySQLConnectionPool._pool = mysql.connector.pooling.MySQLConnectionPool(**config)

    def _get_connection(self) -> mysql.connector.connection.MySQLConnection:
        """
        Get a connection from the pool.
        
        Returns:
            MySQLConnection: Active connection
            
        Raises:
            PoolError: If no connections available after timeout
        """
        return self._pool.get_connection()

    def execute(
        self, 
        query: str, 
        params: Optional[Union[Tuple, Dict]] = None
    ) -> Tuple[mysql.connector.cursor.MySQLCursor, mysql.connector.connection.MySQLConnection]:
        """
        Execute SQL query and return cursor and connection.
        
        Note: Caller MUST close the connection manually.
        
        Args:
            query: SQL query with optional parameters (%s or %(name)s)
            params: Query parameters
            
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
        cursor = conn.cursor(dictionary=self._dictionary)
        cursor.execute(query, params or ())
        return cursor, conn

    def execute_safe(
        self,
        query: str,
        params: Optional[Union[Tuple, Dict]] = None
    ) -> Tuple[mysql.connector.cursor.MySQLCursor, Optional[List[Dict]]]:
        """
        Execute query and automatically close resources.
        
        Args:
            query: SQL query
            params: Query parameters
            
        Returns:
            Tuple (cursor, results) - results is None for non-result queries
            
        Example:
            >>> _, results = db.execute_safe("SELECT * FROM products")
        """
        conn = self._get_connection()
        try:
            with conn.cursor(dictionary=self._dictionary) as cursor:
                cursor.execute(query, params or ())
                results = cursor.fetchall() if cursor.with_rows else None
                return cursor, results
        finally:
            conn.close()

    def fetchone(
        self,
        query: str,
        params: Optional[Union[Tuple, Dict]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Execute query and return a single row.
        
        Args:
            query: SQL query
            params: Query parameters
            
        Returns:
            Dict with row data or None if no results
            
        Example:
            >>> user = db.fetchone("SELECT * FROM users WHERE id = %s", (1,))
        """
        conn = self._get_connection()
        try:
            with conn.cursor(dictionary=self._dictionary) as cursor:
                cursor.execute(query, params or ())
                return cursor.fetchone()
        finally:
            conn.close()

    def fetchall(
        self,
        query: str,
        params: Optional[Union[Tuple, Dict]] = None
    ) -> List[Dict[str, Any]]:
        """
        Execute query and return all rows.
        
        Args:
            query: SQL query
            params: Query parameters
            
        Returns:
            List[Dict] with results
            
        Example:
            >>> products = db.fetchall("SELECT * FROM products")
        """
        conn = self._get_connection()
        try:
            with conn.cursor(dictionary=self._dictionary) as cursor:
                cursor.execute(query, params or ())
                return cursor.fetchall()
        finally:
            conn.close()

    def commit_execute(
        self,
        query: str,
        params: Optional[Union[Tuple, Dict]] = None
    ) -> Tuple[int, Optional[int]]:
        """
        Execute write query and commit.
        
        Args:
            query: SQL query (INSERT/UPDATE/DELETE)
            params: Query parameters
            
        Returns:
            Tuple (rowcount, lastrowid)
            
        Example:
            >>> count, last_id = db.commit_execute(
            ...     "INSERT INTO logs (message) VALUES (%s)",
            ...     ("Error 404",)
            ... )
        """
        conn = self._get_connection()
        try:
            with conn.cursor(dictionary=self._dictionary) as cursor:
                cursor.execute(query, params or ())
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