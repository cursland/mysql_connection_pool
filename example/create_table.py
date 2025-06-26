from mysql_connection_pool import MySQLConnectionPool


def create_table():
    db = MySQLConnectionPool.get_instance()
    
    db.commit_execute(
        "CREATE TABLE IF NOT EXISTS users (id INT AUTO_INCREMENT PRIMARY KEY, name VARCHAR(100), age INT);",
        ()
    )
