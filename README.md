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

## 📋 Ejemplos por Método

### 1. `fetchall()` - Consultas de lectura
```python
# Ejemplo 1: Obtener todos los productos
productos = db.fetchall("SELECT id, nombre, precio FROM productos")
print(f"📦 Productos: {len(productos)} encontrados")

# Ejemplo 2: Consulta con parámetros
productos_activos = db.fetchall(
    "SELECT * FROM productos WHERE activo = %s AND precio > %s",
    (True, 50.0)
)
```

### 2. `fetchone()` - Un solo registro
```python
# Ejemplo 1: Buscar usuario por email
usuario = db.fetchone(
    "SELECT * FROM usuarios WHERE email = %s",
    ("maria@example.com",)
)
if usuario:
    print(f"👤 Usuario encontrado: {usuario['nombre']}")

# Ejemplo 2: Contar registros
total = db.fetchone("SELECT COUNT(*) AS total FROM pedidos")["total"]
print(f"🛒 Total pedidos: {total}")
```

### 3. `commit_execute()` - Escritura de datos
```python
# Ejemplo 1: Insert simple
_, nuevo_id = db.commit_execute(
    "INSERT INTO productos (nombre, precio) VALUES (%s, %s)",
    ("Teclado Mecánico", 89.99)
)
print(f"🆕 ID del nuevo producto: {nuevo_id}")

# Ejemplo 2: Actualización masiva
filas_afectadas, _ = db.commit_execute(
    "UPDATE productos SET precio = precio * 0.9 WHERE categoria = %s",
    ("Electrónicos",)
)
print(f"♻️ {filas_afectadas} productos actualizados")
```

### 4. `execute_safe()` - Uso genérico
```python
# Ejemplo 1: Consulta con procesamiento
cursor, resultados = db.execute_safe("""
    SELECT p.nombre, COUNT(*) as ventas
    FROM productos p
    JOIN pedidos_detalle pd ON p.id = pd.producto_id
    GROUP BY p.id
""")

if resultados:
    for prod in resultados:
        print(f"📊 {prod['nombre']}: {prod['ventas']} ventas")

# Ejemplo 2: Llamada a procedimiento
cursor, _ = db.execute_safe("CALL limpiar_registros_antiguos(%s)", (30,))
```

## 🏗️ Escenarios Avanzados

### 1. Transacciones Complejas
```python
conn = db._get_connection()
try:
    conn.start_transaction()
    
    cursor = conn.cursor(dictionary=True)
    
    # Paso 1: Reservar inventario
    cursor.execute(
        "UPDATE inventario SET cantidad = cantidad - %s WHERE producto_id = %s",
        (2, 101)
    )
    
    # Paso 2: Crear pedido
    cursor.execute(
        "INSERT INTO pedidos (usuario_id, total) VALUES (%s, %s)",
        (15, 199.98)
    )
    pedido_id = cursor.lastrowid
    
    # Paso 3: Detalles del pedido
    cursor.executemany(
        "INSERT INTO pedidos_detalle (pedido_id, producto_id, cantidad) VALUES (%s, %s, %s)",
        [(pedido_id, 101, 2)]
    )
    
    conn.commit()
    print(f"✅ Pedido {pedido_id} creado correctamente")
except Exception as e:
    conn.rollback()
    print(f"❌ Error en transacción: {e}")
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

# Uso:
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

db.commit_execute(
    "INSERT INTO productos (nombre, categoria, precio) VALUES (%s, %s, %s)",
    datos_productos,
    many=True
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

# Uso:
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

## 📝 Notas Importantes
1. Siempre usa parámetros para prevenir SQL injection:
   ```python
   # ❌ Mal
   db.fetchall(f"SELECT * FROM usuarios WHERE id = {user_input}")
   
   # ✅ Bien
   db.fetchall("SELECT * FROM usuarios WHERE id = %s", (user_input,))
   ```

2. Para operaciones batch, usa `many=True` en `commit_execute()`.

3. Las conexiones obtenidas con `_get_connection()` DEBEN cerrarse manualmente.