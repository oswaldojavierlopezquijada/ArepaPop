import sqlite3

def conectar():
    return sqlite3.connect("cantina.db")

def criar_tabelas():
    con = conectar()
    cur = con.cursor()
    
    # Tus tablas anteriores (produtos, pedidos) siguen aquí...
    cur.execute("""
    CREATE TABLE IF NOT EXISTS produtos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        preco REAL NOT NULL,
        estoque INTEGER NOT NULL
    )
    """)
    
    cur.execute("""
    CREATE TABLE IF NOT EXISTS pedidos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        produto_id INTEGER NOT NULL,
        quantidade INTEGER NOT NULL,
        total REAL NOT NULL,
        data_pedido TEXT NOT NULL,
        FOREIGN KEY (produto_id) REFERENCES produtos(id)
    )
    """)

    # NUEVA TABLA: Comentarios y Contacto
    cur.execute("""
    CREATE TABLE IF NOT EXISTS comentarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        email TEXT NOT NULL,
        mensagem TEXT NOT NULL,
        data_envio TEXT NOT NULL
    )
    """)
    
    con.commit()
    con.close()