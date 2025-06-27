# 🐬✨ MySQL Connection Pool - Gestor de conexiones para MySQL ✨🐬

Este módulo proporciona una clase `MySQLConnectionPool` que gestiona un pool de conexiones a MySQL de forma segura para hilos, con capacidades avanzadas de logging y manejo de transacciones.

## 🚀 Características principales

- ✅ **Pool de conexiones thread-safe**  
- 🔄 **Reconexión automática**  
- 📝 **Logging detallado con soporte multilingüe (español/inglés)**  
- 🔄 **Cambio de base de datos dinámico**  
- 📂 **Ejecución de archivos SQL con parsing avanzado**  
- 🔒 **Manejo seguro de recursos (cierre automático de conexiones)**  
- 📊 **Múltiples métodos de ejecución según necesidades**  

## 📦 Instalación

```bash
pip install mysql-connection-pool
```

## 🛠️ Uso básico

### ⚙️ Inicialización

```python
from mysql_connection_pool import MySQLConnectionPool

# Configuración inicial
db = MySQLConnectionPool(
    host='localhost',
    user='tu_usuario',
    password='tu_contraseña',
    database='base_inicial',
    pool_size=5,
    logs='logs/mysql.log',  # Ruta relativa o absoluta
    log_language='es',      # 'es' o 'en'
    clear_logs=True         # Limpiar archivo de log al iniciar
)
```

### 🔍 Ejecución de consultas

```python
# 👥 Consulta SELECT simple
usuarios = db.fetchall("SELECT * FROM usuarios")

# 🔎 Consulta con parámetros
usuario = db.fetchone("SELECT * FROM usuarios WHERE id = %s", (1,))

# 📝 Inserción con commit automático
filas_afectadas, ultimo_id = db.commit_execute(
    "INSERT INTO productos (nombre, precio) VALUES (%s, %s)",
    ("Laptop", 999.99)
)

# 🔄 Cambiar de base de datos
db.switch_database('otra_base_datos')
```

## 🧩 Métodos principales

### 1️⃣ `execute(query, params=None, database=None, enable_logging=False)`
Ejecuta una consulta y devuelve cursor y conexión (debes cerrarla manualmente).

```python
cursor, conn = db.execute("SELECT * FROM tabla")
try:
    resultados = cursor.fetchall()
finally:
    conn.close()  # ¡Importante cerrar la conexión! 🔒
```

### 2️⃣ `execute_safe(query, params=None, database=None, enable_logging=False)`
Ejecuta una consulta y cierra los recursos automáticamente.

```python
resultados = db.execute_safe("SELECT * FROM productos WHERE precio > %s", (100,))
```

### 3️⃣ `fetchone(query, params=None, database=None, enable_logging=False)`
Obtiene una sola fila.

```python
usuario = db.fetchone("SELECT * FROM usuarios WHERE email = %s", ("user@example.com",))
```

### 4️⃣ `fetchall(query, params=None, database=None, enable_logging=False)`
Obtiene todas las filas.

```python
productos = db.fetchall("SELECT * FROM productos")
```

### 5️⃣ `commit_execute(query, params=None, database=None, enable_logging=False)`
Ejecuta una consulta de escritura (INSERT/UPDATE/DELETE) con commit automático.

```python
filas, id_insertado = db.commit_execute(
    "INSERT INTO ventas (producto_id, cantidad) VALUES (%s, %s)",
    (5, 2)
)
```

### 6️⃣ `switch_database(database)`
Cambia a otra base de datos.

```python
db.switch_database('base_de_datos_nueva')
```

### 7️⃣ Métodos con logging automático
Versiones con `_logged` que activan logging por defecto:

```python
db.execute_logged(...)
db.fetchone_logged(...)
# etc...
```

## 📂 Ejecución de archivos SQL

### 📄 Ejecutar un archivo SQL

```python
MySQLConnectionPool.run_sql_file('ruta/archivo.sql')
```

### 📚 Ejecutar múltiples archivos

```python
MySQLConnectionPool.run_multiple_sql_files([
    'ruta/archivo1.sql',
    'ruta/archivo2.sql'
])
```

### 🗂️ Ejecutar archivos desde un directorio

```python
MySQLConnectionPool.run_multiple_sql_files_from_directory(
    'ruta/directorio',
    ['script1.sql', 'script2.sql']
)
```

## 🏆 Ejemplo completo

```python
from mysql_connection_pool import MySQLConnectionPool
import os

# Configuración inicial
db = MySQLConnectionPool(
    host='localhost',
    user='root',
    password='password123',
    database='mi_negocio',
    pool_size=5,
    logs=os.path.join('logs', 'mysql.log'),
    log_language='es',
    clear_logs=True
)

try:
    # 1️⃣ Crear tabla si no existe
    db.commit_execute_logged("""
        CREATE TABLE IF NOT EXISTS clientes (
            id INT AUTO_INCREMENT PRIMARY KEY,
            nombre VARCHAR(100) NOT NULL,
            email VARCHAR(100) UNIQUE NOT NULL,
            fecha_registro DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # 2️⃣ Insertar datos
    filas_afectadas, ultimo_id = db.commit_execute_logged(
        "INSERT INTO clientes (nombre, email) VALUES (%s, %s)",
        ("Juan Pérez", "juan@example.com")
    )
    print(f"ID insertado: {ultimo_id} 🎉")
    
    # 3️⃣ Consultar datos
    clientes = db.fetchall_logged("SELECT * FROM clientes")
    print("Clientes:", clientes)
    
    # 4️⃣ Cambiar de base de datos y ejecutar script SQL
    db.switch_database('otra_base')
    MySQLConnectionPool.run_sql_file('scripts/migracion.sql')
    
except Exception as e:
    print("❌ Error:", e)
```

## 📝 Sistema de Logging

El sistema de logging registra:
- ✅ Ejecución exitosa de consultas
- ❌ Errores con detalles completos
- 📝 Cambios de base de datos
- 📂 Ejecución de archivos SQL

Ejemplo de entrada de log:
```
══════════════════════════════[2023-07-20 14:30:45] RUN_SQL_FILE══════════════════════════════

Action: Procesando archivo SQL: migracion.sql

Ejecutando sentencias SQL: 3

══════════════════════════════════════════════════════════════════════════════════════════════
```

## 🧠 Manejo avanzado de SQL

El parser soporta:
- 🔄 Sentencias con DELIMITER para procedimientos almacenados
- 📝 Comentarios (-- y /* */)
- 📜 Multiples sentencias en un archivo

Ejemplo de archivo SQL complejo:

```sql
DELIMITER //
CREATE PROCEDURE calcular_total(IN cliente_id INT)
BEGIN
    SELECT SUM(monto) AS total 
    FROM pedidos 
    WHERE cliente_id = cliente_id;
END //
DELIMITER ;

-- Insertar datos iniciales
INSERT INTO config (parametro, valor) VALUES ('version', '1.0');
```