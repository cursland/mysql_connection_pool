import mysql.connector.pooling
import threading
from typing import Optional, Dict, Any, Tuple, Union, List
import os
import sqlglot
import re
import logging
import sys
from datetime import datetime


class MySQLConnectionPoolLogger:
    """
    Custom logger for MySQLConnectionPool with emoji support and logs formatting.
    Logs are saved based on the provided path or current working directory.
    """
    
    _logger = None
    _log_file_path = None
    _language = "es"
    
    # Multilingual messages
    MESSAGES = {
        "es": {
            "processing_file": "Procesando archivo SQL",
            "executing_statements": "Ejecutando sentencias SQL",
            "executing_statement": "Ejecutando sentencia",
            "statement_success": "Sentencia ejecutada correctamente",
            "statement_error": "Error en sentencia",
            "files_to_execute": "Archivos a ejecutar",
            "no_statements": "No se encontraron sentencias SQL válidas",
            "file_error": "Error procesando archivo",
            "problematic_statement": "Sentencia problemática",
            "query": "Consulta",
            "response": "Respuesta",
            "success": "ÉXITO",
            "error": "ERROR",
            "info": "INFO",
            "debug": "DEBUG"
        },
        "en": {
            "processing_file": "Processing SQL file",
            "executing_statements": "Executing SQL statements",
            "executing_statement": "Executing statement",
            "statement_success": "Statement executed successfully",
            "statement_error": "Error in statement",
            "files_to_execute": "Files to execute",
            "no_statements": "No valid SQL statements found",
            "file_error": "Error processing file",
            "problematic_statement": "Problematic statement",
            "query": "Query",
            "response": "Response",
            "success": "SUCCESS",
            "error": "ERROR",
            "info": "INFO",
            "debug": "DEBUG"
        }
    }
    
    @classmethod
    def setup_logger(cls, log_file_path: str = None, language: str = "es", clear_logs: bool = False):
        """
        Setup logger with file and console handlers.
        
        Args:
            log_file_path: Path for log file. Can be:
                          - None: No logging
                          - "logs/myfile.log": Relative path from execution directory
                          - "/full/path/myfile.log": Absolute path
            language: Language for log messages ("es" or "en")
            clear_logs: If True, clears the log file content at startup
        """
        cls._language = language
        
        # If no log file path provided, don't set up logging
        if not log_file_path:
            return None
            
        if cls._logger is not None:
            return cls._logger
            
        # Handle path
        if os.path.isabs(log_file_path):
            # Absolute path
            cls._log_file_path = log_file_path
        else:
            # Relative path from current working directory
            cls._log_file_path = os.path.join(os.getcwd(), log_file_path)
          # Ensure log directory exists
        log_dir = os.path.dirname(cls._log_file_path)
        os.makedirs(log_dir, exist_ok=True)
        
        # Clear log file if requested
        if clear_logs and os.path.exists(cls._log_file_path):
            open(cls._log_file_path, 'w').close()
            
        # Create logger
        cls._logger = logging.getLogger('mysql_connection_pool')
        cls._logger.setLevel(logging.DEBUG)
        
        # Remove existing handlers to avoid duplicates
        cls._logger.handlers.clear()
        
        # Create formatter (only for file)
        file_formatter = logging.Formatter(
            '%(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # File handler only (no console output)
        file_handler = logging.FileHandler(cls._log_file_path, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(file_formatter)
        cls._logger.addHandler(file_handler)
        
        return cls._logger
    
    @classmethod
    def get_logger(cls):
        """Get the logger instance."""
        return cls._logger
    
    @classmethod
    def _get_message(cls, key: str) -> str:
        """Get message in the configured language."""
        return cls.MESSAGES.get(cls._language, cls.MESSAGES["es"]).get(key, key)
    
    @classmethod
    def _format_log(cls, level: str, title: str, message: str = "", query: str = "", response: str = "", emoji: str = "", execution_context: str = ""):
        """Format a log entry with centered title and execution context."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Create separator with centered execution context
        separator_length = 80
        separator_char = "═"
        
        # Create centered execution context line
        context_text = f"[{timestamp}] {execution_context.upper()}" if execution_context else f"[{timestamp}] SISTEMA"
        context_length = len(context_text)
        
        # Calculate padding for centering
        if context_length < separator_length:
            padding = (separator_length - context_length) // 2
            context_line = separator_char * padding + context_text + separator_char * (separator_length - padding - context_length)
        else:
            context_line = context_text
        
        log_entry = f"""
{context_line}

Action: {title}"""
        
        if message:
            log_entry += f"\n\n{message}"
        
        if query:
            # Don't limit query display for better readability
            log_entry += f"\n\n🔍 Query:\n\n{query}"
        
        if response:
            log_entry += f"\n\n✅ {response}"
        
        log_entry += f"\n\n{separator_char * separator_length}\n"
        
        return log_entry
    
    @classmethod
    def log_statement_execution(cls, statement_num: int, total_statements: int, query: str, success: bool = True, error_msg: str = "", rows_affected: int = 0, execution_context: str = "run_sql_file"):
        """Log SQL statement execution with SQL response details."""
        logger = cls.get_logger()
        if not logger:
            return
            
        if success:
            title = f"{cls._get_message('executing_statement')} {statement_num}/{total_statements}"
            response = f"{cls._get_message('statement_success')}:\n\n{rows_affected} row(s) affected"
        else:
            title = f"{cls._get_message('statement_error')} {statement_num}/{total_statements}"
            response = f"ERROR:\n\n{error_msg}"
        
        log_entry = cls._format_log(
            level="INFO" if success else "ERROR",
            title=title,
            query=query,
            response=response,
            execution_context=execution_context
        )
        
        if success:
            logger.info(log_entry)
        else:
            logger.error(log_entry)
    
    @classmethod
    def log_file_processing(cls, file_path: str, statement_count: int, execution_context: str = "run_sql_file"):
        """Log file processing start."""
        logger = cls.get_logger()
        if not logger:
            return
            
        title = f"{cls._get_message('processing_file')}: {os.path.basename(file_path)}"
        message = f"{cls._get_message('executing_statements')}: {statement_count}"
        
        log_entry = cls._format_log(
            level="INFO",
            title=title,
            message=message,
            execution_context=execution_context
        )
        
        logger.info(log_entry)
    
    @classmethod
    def log_files_list(cls, file_paths: List[str], execution_context: str = "run_multiple_sql_files_from_directory"):
        """Log list of files to execute."""
        logger = cls.get_logger()
        if not logger:
            return
            
        title = cls._get_message('files_to_execute')
        message = "\n".join([f"  • {path}" for path in file_paths])
        
        log_entry = cls._format_log(
            level="INFO",
            title=title,
            message=message,
            execution_context=execution_context
        )
        
        logger.info(log_entry)
    
    @classmethod
    def log_error(cls, title: str, error_msg: str, problematic_content: str = "", execution_context: str = "sistema"):
        """Log error."""
        logger = cls.get_logger()
        if not logger:
            return
            
        log_entry = cls._format_log(
            level="ERROR",
            title=title,
            message=error_msg,
            query=problematic_content if problematic_content else "",
            execution_context=execution_context
        )
        
        logger.error(log_entry)
    
    @classmethod
    def log_warning(cls, title: str, message: str = "", execution_context: str = "sistema"):
        """Log warning."""
        logger = cls.get_logger()
        if not logger:
            return
            
        log_entry = cls._format_log(
            level="WARNING",
            title=title,
            message=message,
            execution_context=execution_context
        )
        
        logger.warning(log_entry)
    
    @classmethod
    def get_log_file_path(cls) -> str:
        """Get the current log file path."""
        return cls._log_file_path


class MySQLConnectionPool:
    """
    A thread-safe MySQL connection pool manager with database switching capability.
    
    Provides a high-level interface for executing SQL queries with automatic:
    - Connection pooling
    - Resource cleanup (cursors and connections)
    - Transaction management
    - Automatic reconnection
    - Database switching
    - Beautiful logging with multilingual support
    
    Class Attributes:
        _pool: MySQLConnectionPool - Shared connection pool
        _lock: threading.Lock - Lock for thread-safe pool initialization
        _dictionary: bool - Whether to return results as dictionaries
        _instance: MySQLConnectionPool - Singleton instance      Basic Usage:
        >>> from mysql_connection_pool import MySQLConnectionPool
        >>> db = MySQLConnectionPool(host='localhost', user='root', database='test', 
        ...                         logs='logs/mysql.log', log_language='es', clear_logs=True)
        >>> results = db.fetchall("SELECT * FROM users")
        >>> db.switch_database('new_database')  # Switch to a different database
    """
    
    _pool: mysql.connector.pooling.MySQLConnectionPool = None
    _lock: threading.Lock = threading.Lock()
    _dictionary: bool = True
    _instance = None
    _current_database: Optional[str] = None
    _connection_params: Dict[str, Any] = {}
    _log_language: str = "es"
    _log_file_path: Optional[str] = None
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
        logs: Optional[str] = None,
        log_language: str = "es",
        clear_logs: bool = False,
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
            logs: Log file path (None=no logging, "logs/file.log"=relative, "/path/file.log"=absolute)
            log_language: Language for log messages "es" or "en" (default "es")
            clear_logs: If True, clears the log file content at startup (default False)
            **kwargs: Additional connection parameters
            
        Raises:
            mysql.connector.Error: If initial connection fails
        """
        with MySQLConnectionPool._lock:
            if MySQLConnectionPool._pool is None:
                MySQLConnectionPool._dictionary = dictionary
                MySQLConnectionPool._current_database = database
                MySQLConnectionPool._log_language = log_language
                MySQLConnectionPool._log_file_path = logs
                  # Setup logger with new parameters
                MySQLConnectionPoolLogger.setup_logger(
                    log_file_path=logs,
                    language=log_language,
                    clear_logs=clear_logs
                )
                
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
            MySQLConnectionPool.safe_close_connection(conn)

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
        database: Optional[str] = None,
        enable_logging: bool = True
    ) -> Tuple['mysql.connector.cursor.MySQLCursor', 'mysql.connector.connection.MySQLConnection']:
        """
        Execute SQL query and return cursor and connection.
        
        Note: Caller MUST close the connection manually.
        
        Args:
            query: SQL query with optional parameters (%s or %(name)s)
            params: Query parameters
            database: Optional database to use for this query
            enable_logging: Whether to log this execution
            
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
        
        try:
            if norm_params is not None:
                cursor.execute(query, norm_params)
            else:
                cursor.execute(query)
            
            # Log if enabled
            if enable_logging:
                MySQLConnectionPoolLogger.log_statement_execution(
                    statement_num=1,
                    total_statements=1,
                    query=query,
                    success=True,
                    rows_affected=cursor.rowcount,
                    execution_context="execute"
                )
        except Exception as e:
            if enable_logging:
                MySQLConnectionPoolLogger.log_statement_execution(
                    statement_num=1,
                    total_statements=1,
                    query=query,
                    success=False,
                    error_msg=str(e),
                    execution_context="execute"
                )
            MySQLConnectionPool.safe_close_connection(conn)
            raise e
            
        return cursor, conn

    def execute_safe(
        self,
        query: str,
        params: Optional[Union[Tuple, Dict]] = None,
        database: Optional[str] = None,
        enable_logging: bool = True
    ) -> Optional[List[Dict]]:
        """
        Execute query and automatically close resources.
        
        Args:
            query: SQL query
            params: Query parameters
            database: Optional database to use for this query
            enable_logging: Whether to log this execution
            
        Returns:
            Results list or None for non-result queries
            
        Example:
            >>> results = db.execute_safe("SELECT * FROM products", database='inventory')
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
                rows_affected = cursor.rowcount
                
                # Log if enabled
                if enable_logging:
                    MySQLConnectionPoolLogger.log_statement_execution(
                        statement_num=1,
                        total_statements=1,
                        query=query,
                        success=True,
                        rows_affected=rows_affected,
                        execution_context="execute_safe"
                    )
                
                return results
        except Exception as e:
            if enable_logging:
                MySQLConnectionPoolLogger.log_statement_execution(
                    statement_num=1,
                    total_statements=1,
                    query=query,
                    success=False,
                    error_msg=str(e),
                    execution_context="execute_safe"
                )
            raise e
        finally:
            MySQLConnectionPool.safe_close_connection(conn)

    def fetchone(
        self,
        query: str,
        params: Optional[Union[Tuple, Dict]] = None,
        database: Optional[str] = None,
        enable_logging: bool = True
    ) -> Optional[Dict[str, Any]]:
        """
        Execute query and return a single row.
        
        Args:
            query: SQL query
            params: Query parameters
            database: Optional database to use for this query
            enable_logging: Whether to log this execution
            
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
                result = cursor.fetchone()
                rows_affected = cursor.rowcount
                
                # Log if enabled
                if enable_logging:
                    MySQLConnectionPoolLogger.log_statement_execution(
                        statement_num=1,
                        total_statements=1,
                        query=query,
                        success=True,
                        rows_affected=rows_affected,
                        execution_context="fetchone"
                    )
                
                return result
        except Exception as e:
            if enable_logging:
                MySQLConnectionPoolLogger.log_statement_execution(
                    statement_num=1,
                    total_statements=1,
                    query=query,
                    success=False,
                    error_msg=str(e),
                    execution_context="fetchone"
                )
            raise e
        finally:
            MySQLConnectionPool.safe_close_connection(conn)

    def fetchall(
        self,
        query: str,
        params: Optional[Union[Tuple, Dict]] = None,
        database: Optional[str] = None,
        enable_logging: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Execute query and return all rows.
        
        Args:
            query: SQL query
            params: Query parameters
            database: Optional database to use for this query
            enable_logging: Whether to log this execution
            
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
                results = cursor.fetchall()
                rows_affected = cursor.rowcount
                
                # Log if enabled
                if enable_logging:
                    MySQLConnectionPoolLogger.log_statement_execution(
                        statement_num=1,
                        total_statements=1,
                        query=query,
                        success=True,
                        rows_affected=rows_affected,
                        execution_context="fetchall"
                    )
                
                return results
        except Exception as e:
            if enable_logging:
                MySQLConnectionPoolLogger.log_statement_execution(
                    statement_num=1,
                    total_statements=1,
                    query=query,
                    success=False,
                    error_msg=str(e),
                    execution_context="fetchall"
                )
            raise e
        finally:
            MySQLConnectionPool.safe_close_connection(conn)

    def commit_execute(
        self,
        query: str,
        params: Optional[Union[Tuple, Dict]] = None,
        database: Optional[str] = None,
        enable_logging: bool = True
    ) -> Tuple[int, Optional[int]]:
        """
        Execute write query and commit.
        
        Args:
            query: SQL query (INSERT/UPDATE/DELETE)
            params: Query parameters
            database: Optional database to use for this query
            enable_logging: Whether to log this execution
            
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
                rows_affected = cursor.rowcount
                last_id = cursor.lastrowid
                
                # Log if enabled
                if enable_logging:
                    MySQLConnectionPoolLogger.log_statement_execution(
                        statement_num=1,
                        total_statements=1,
                        query=query,
                        success=True,
                        rows_affected=rows_affected,
                        execution_context="commit_execute"
                    )
                
                return rows_affected, last_id
        except Exception as e:
            if enable_logging:
                MySQLConnectionPoolLogger.log_statement_execution(
                    statement_num=1,
                    total_statements=1,
                    query=query,
                    success=False,
                    error_msg=str(e),
                    execution_context="commit_execute"
                )
            raise e
        finally:
            MySQLConnectionPool.safe_close_connection(conn)

    @staticmethod
    def lastrowid(cursor: mysql.connector.cursor.MySQLCursor) -> Optional[int]:
        """Return the ID of the last inserted row."""
        return cursor.lastrowid

    @staticmethod
    def rowcount(cursor: mysql.connector.cursor.MySQLCursor) -> int:
        """Return the number of affected rows."""
        return cursor.rowcount

    def execute_with_logging(self, query: str, params: Optional[Union[Tuple, Dict]] = None, database: Optional[str] = None) -> Tuple[Optional[List[Dict]], int]:
        """
        Execute query and return results along with row count for logging.
        
        Args:
            query: SQL query
            params: Query parameters
            database: Optional database to use for this query
            
        Returns:
            Tuple (results, rowcount)
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
                row_count = cursor.rowcount
                return results, row_count
        finally:
            MySQLConnectionPool.safe_close_connection(conn)

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
    def _remove_sql_comments(sql_content: str) -> str:
        """Remove SQL comments while preserving string literals."""
        # Remove single line comments (-- comment)
        sql_content = re.sub(r'--.*$', '', sql_content, flags=re.MULTILINE)
        
        # Remove multi-line comments (/* comment */)
        sql_content = re.sub(r'/\*.*?\*/', '', sql_content, flags=re.DOTALL)
        
        return sql_content

    @staticmethod
    def _handle_delimiter_statements(content: str) -> List[str]:
        """
        Handle DELIMITER statements in SQL content.
        
        This function processes content with custom delimiters like:
        DELIMITER //
        CREATE TRIGGER ...
        END //
        DELIMITER ;
        """
        
        statements = []
        current_delimiter = ';'
        current_statement = ''
        
        lines = content.split('\n')
        
        for line in lines:
            line = line.strip()
            
            # Skip empty lines
            if not line:
                continue
                
            # Check for DELIMITER change
            delimiter_match = re.match(r'^\s*DELIMITER\s+(.+)\s*$', line, re.IGNORECASE)
            if delimiter_match:
                # Save current statement if exists
                if current_statement.strip():
                    statements.append(current_statement.strip())
                    current_statement = ''
                
                # Change delimiter
                new_delimiter = delimiter_match.group(1).strip()
                current_delimiter = new_delimiter
                continue
            
            # Add line to current statement
            if current_statement:
                current_statement += '\n' + line
            else:
                current_statement = line
            
            # Check if statement ends with current delimiter
            if line.endswith(current_delimiter):
                # Remove the delimiter from the end
                final_statement = current_statement[:-len(current_delimiter)].strip()
                if final_statement:
                    statements.append(final_statement)
                current_statement = ''
        
        # Add any remaining statement
        if current_statement.strip():
            statements.append(current_statement.strip())
        
        return statements

    @staticmethod
    def _parse_sql_with_sqlglot(sql_content: str) -> List[str]:
        """
        Parse SQL content using SQLGlot, handling DELIMITER statements and complex triggers.
        
        Args:
            sql_content: Raw SQL content from file
            
        Returns:
            List of SQL statements ready to execute
        """
        
        # Remove comments but keep structure
        content = MySQLConnectionPool._remove_sql_comments(sql_content)
        
        # Handle DELIMITER statements
        statements = MySQLConnectionPool._handle_delimiter_statements(content)
        
        # Clean and validate each statement
        clean_statements = []
        for stmt in statements:
            stmt = stmt.strip()
            if stmt and not stmt.startswith('--') and stmt.upper() != 'DELIMITER':
                # Skip standalone DELIMITER statements
                if not re.match(r'^\s*DELIMITER\s+', stmt, re.IGNORECASE):
                    clean_statements.append(stmt)
        
        return clean_statements
    
    @staticmethod
    def run_sql_file(file_path: str) -> None:
        """
        Execute SQL commands from a file using SQLGlot for advanced parsing.
        
        Supports:
        - DELIMITER statements for triggers and stored procedures
        - Complex multi-line statements
        - Comments removal
        - Proper statement separation
        - Beautiful multilingual logging
        
        Args:
            file_path: Path to the SQL file
            
        Raises:
            FileNotFoundError: If the file does not exist
            mysql.connector.Error: If execution fails
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"SQL file not found: {file_path}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                sql_content = file.read()

            # Parse SQL content using SQLGlot with DELIMITER support
            statements = MySQLConnectionPool._parse_sql_with_sqlglot(sql_content)
            
            if not statements:
                MySQLConnectionPoolLogger.log_warning("No se encontraron sentencias SQL válidas en el archivo.")
                return

            db = MySQLConnectionPool.get_instance()
              # Log file processing start
            MySQLConnectionPoolLogger.log_file_processing(file_path, len(statements), "run_sql_file")
            
            for i, stmt in enumerate(statements, 1):
                try:
                    # Execute statement and get rows affected
                    results, rows_affected = db.execute_with_logging(stmt)
                    
                    # Log successful execution
                    MySQLConnectionPoolLogger.log_statement_execution(
                        statement_num=i,
                        total_statements=len(statements),
                        query=stmt,
                        success=True,
                        rows_affected=rows_affected,
                        execution_context="run_sql_file"
                    )
                except Exception as stmt_error:
                    # Log error execution
                    MySQLConnectionPoolLogger.log_statement_execution(
                        statement_num=i,
                        total_statements=len(statements),
                        query=stmt,
                        success=False,
                        error_msg=str(stmt_error),
                        execution_context="run_sql_file"
                    )
                    raise stmt_error
                    
        except Exception as e:
            MySQLConnectionPoolLogger.log_error(
                title="Error procesando archivo",
                error_msg=str(e),
                problematic_content=file_path,
                execution_context="run_sql_file"
            )
            raise e

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
        Execute multiple SQL files from a directory with beautiful logging.
        
        Args:
            base_dir: Directory containing SQL files
            file_names: List of SQL file names to execute
        """
        file_paths = [os.path.join(base_dir, name).replace("\\", "/") for name in file_names]
          # Log files list
        MySQLConnectionPoolLogger.log_files_list(file_paths, "run_multiple_sql_files_from_directory")
        
        db = MySQLConnectionPool.get_instance()
        db.run_multiple_sql_files(file_paths)
    
    # Convenience methods with logging enabled by default
    def execute_logged(self, query: str, params: Optional[Union[Tuple, Dict]] = None, database: Optional[str] = None) -> Tuple['mysql.connector.cursor.MySQLCursor', 'mysql.connector.connection.MySQLConnection']:
        """Execute SQL query with logging enabled."""
        return self.execute(query, params, database, enable_logging=True)
    
    def execute_safe_logged(self, query: str, params: Optional[Union[Tuple, Dict]] = None, database: Optional[str] = None) -> Optional[List[Dict]]:
        """Execute query safely with logging enabled."""
        return self.execute_safe(query, params, database, enable_logging=True)
    
    def fetchone_logged(self, query: str, params: Optional[Union[Tuple, Dict]] = None, database: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Fetch one row with logging enabled."""
        return self.fetchone(query, params, database, enable_logging=True)
    
    def fetchall_logged(self, query: str, params: Optional[Union[Tuple, Dict]] = None, database: Optional[str] = None) -> List[Dict[str, Any]]:
        """Fetch all rows with logging enabled."""
        return self.fetchall(query, params, database, enable_logging=True)
    
    def commit_execute_logged(self, query: str, params: Optional[Union[Tuple, Dict]] = None, database: Optional[str] = None) -> Tuple[int, Optional[int]]:
        """Execute write query with commit and logging enabled."""
        return self.commit_execute(query, params, database, enable_logging=True)
    
    @staticmethod
    def safe_close_connection(connection):
        """
        Safely close a MySQL connection, ignoring errors if already closed or unavailable.
        Use this instead of connection.close() directly.
        """
        try:
            if connection and hasattr(connection, "is_connected") and connection.is_connected():
                connection.close()
        except Exception:
            pass  # Connection already closed or unavailable