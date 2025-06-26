from mysql_connection_pool import MySQLConnectionPool
from create_table import *
from insert_users import *

# Initialize the connection pool
db = MySQLConnectionPool(
    host="localhost",
    user="root",
    password="v62svHpgAPK2dAUyIjp9fu1RCFz",
    port=3028,
    pool_name="my_pool",
    pool_size=5,
    dictionary=True,
)
# Insert data and get the last inserted ID
rowcount, last_id = db.commit_execute(
    "CREATE DATABASE test_db; "
)
print(f"Database created with rowcount: {rowcount}, last_id: {last_id}")

# Switch to the new database created
print(f"Current database: {db.get_current_database()}")
db.switch_database('test_db')
print(f"Current database: {db.get_current_database()}")

create_table()
insert_users()

read = db.execute_safe(
    "SELECT * FROM users;"
)
print("Read data from users table:")
print(read)
