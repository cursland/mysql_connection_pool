# 🎯 MySQLConnectionPool

## 🔌 Conexión Básica
```python
from mysql_connection_pool import MySQLConnectionPool

# Configuración mínima
db = MySQLConnectionPool(
    host="localhost",
    user="admin",
    password="segura123",
    database="ecommerce",
    pool_size=5
)
```

## ⚡ Características Principales
- Pool de conexiones MySQL thread-safe
- Cambio dinámico de base de datos (`switch_database`)
- Métodos de consulta: `fetchall`, `fetchone`, `execute_safe`, `commit_execute`
- Ejecución segura y limpieza automática de recursos
- Métodos utilitarios: `get_current_database`, `is_initialized`, `get_instance`
- Soporte para transacciones manuales
- Validación de nombres de base de datos

## 📋 Ejemplos por Método

### 1. `fetchall()` - Consultas de lectura
```python
# Obtener todos los productos
productos = db.fetchall("SELECT id, nombre, precio FROM productos")
print(f"📦 Productos: {len(productos)} encontrados")

# Consulta con parámetros
productos_activos = db.fetchall(
    "SELECT * FROM productos WHERE activo = %s AND precio > %s",
    (True, 50.0)
)
```

### 2. `fetchone()` - Un solo registro
```python
usuario = db.fetchone(
    "SELECT * FROM usuarios WHERE email = %s",
    ("maria@example.com",)
)
if usuario:
    print(f"👤 Usuario encontrado: {usuario['nombre']}")

total = db.fetchone("SELECT COUNT(*) AS total FROM pedidos")["total"]
print(f"🛒 Total pedidos: {total}")
```

### 3. `commit_execute()` - Escritura de datos
```python
_, nuevo_id = db.commit_execute(
    "INSERT INTO productos (nombre, precio) VALUES (%s, %s)",
    ("Teclado Mecánico", 89.99)
)
print(f"🆕 ID del nuevo producto: {nuevo_id}")

filas_afectadas, _ = db.commit_execute(
    "UPDATE productos SET precio = precio * 0.9 WHERE categoria = %s",
    ("Electrónicos",)
)
print(f"♻️ {filas_afectadas} productos actualizados")
```

### 4. `execute_safe()` y `execute()` - Uso genérico
```python
# Consulta con procesamiento segurocursor, resultados = db.execute_safe("""
    SELECT p.nombre, COUNT(*) as ventas
    FROM productos p
    JOIN pedidos_detalle pd ON p.id = pd.producto_id
    GROUP BY p.id
""")
if resultados:
    for prod in resultados:
        print(f"📊 {prod['nombre']}: {prod['ventas']} ventas")

# Llamada a procedimiento almacenado
cursor, _ = db.execute_safe("CALL limpiar_registros_antiguos(%s)", (30,))

# Uso avanzado de execute (requiere cerrar conexión manualmente)
cursor, conn = db.execute("SELECT * FROM usuarios WHERE id = %s", (1,))
try:
    user = cursor.fetchone()
finally:
    conn.close()
```

### 5. Cambio de Base de Datos
```python
# Cambiar la base de datos activa
db.switch_database("nueva_base")
print("Base de datos actual:", db.get_current_database())
```

## 🏗️ Escenarios Avanzados

### 1. Transacciones Complejas
```python
conn = db._get_connection()
try:
    conn.start_transaction()
    cursor = conn.cursor(dictionary=True)
    # ... operaciones ...
    conn.commit()
finally:
    conn.close()
```

### 2. Paginación de Resultados
```python
def obtener_productos_paginados(pagina: int, por_pagina: int = 10):
    offset = (pagina - 1) * por_pagina
    return db.fetchall(
        "SELECT * FROM productos LIMIT %s OFFSET %s",
        (por_pagina, offset)
    )

pagina_2 = obtener_productos_paginados(2)
print(f"📄 Página 2: {len(pagina_2)} productos")
```

### 3. Carga Masiva Eficiente
```python
# Generar 1000 productos de prueba
datos_productos = [
    (f"Producto {i}", f"categoria-{i%5}", 10 + i*0.5) 
    for i in range(1, 1001)
]

# Para operaciones batch, usar un ciclo o executemany manualmente
for datos in datos_productos:
    db.commit_execute(
        "INSERT INTO productos (nombre, categoria, precio) VALUES (%s, %s, %s)",
        datos
    )
print("⚡ Carga masiva completada")
```

## 🛠️ Patrones Útiles

### 1. Conexión con Context Manager (Python 3.8+)
```python
from contextlib import contextmanager

@contextmanager
def get_db_connection():
    conn = db._get_connection()
    try:
        yield conn
    finally:
        conn.close()

with get_db_connection() as connection:
    cursor = connection.cursor(dictionary=True)
    cursor.execute("SELECT NOW() AS hora_actual")
    print(f"⏰ Hora del servidor: {cursor.fetchone()['hora_actual']}")
```

### 2. Resultados en Formato JSON
```python
import json

def exportar_a_json(tabla: str, archivo: str):
    datos = db.fetchall(f"SELECT * FROM {tabla}")
    with open(archivo, 'w') as f:
        json.dump(datos, f, indent=2)

exportar_a_json("productos", "backup_productos.json")
print("📤 Datos exportados a JSON")
```

## 🔄 Métodos Utilitarios
- `switch_database(nombre)`: Cambia la base de datos activa (valida el nombre)
- `get_current_database()`: Devuelve el nombre de la base de datos actual
- `is_initialized()`: Indica si el pool fue inicializado
- `get_instance()`: Devuelve la instancia singleton del pool

## 📝 Notas Importantes
1. Siempre usa parámetros para prevenir SQL injection:
   ```python
   # ❌ Mal
   db.fetchall(f"SELECT * FROM usuarios WHERE id = {user_input}")
   # ✅ Bien
   db.fetchall("SELECT * FROM usuarios WHERE id = %s", (user_input,))
   ```
2. El método `switch_database` valida el nombre de la base de datos (solo letras, números y guiones bajos).
3. Las conexiones obtenidas con `_get_connection()` DEBEN cerrarse manualmente.
4. Para operaciones batch, usa un ciclo o `executemany` manualmente.
5. Si usas `execute`, recuerda cerrar la conexión devuelta.