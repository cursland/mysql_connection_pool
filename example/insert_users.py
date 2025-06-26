from mysql_connection_pool import MySQLConnectionPool

def insert_users():
    db = MySQLConnectionPool.get_instance()
    db.commit_execute(
        "INSERT INTO users (name, age) VALUES (%s, %s)",
        ("John Doe", 30)
    )
