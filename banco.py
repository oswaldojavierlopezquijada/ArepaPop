import sqlite3

def conectar():
    con = sqlite3.connect("cantina.db")
    con.row_factory = sqlite3.Row
    return con

def criar_tabelas():
    con = conectar()
    cur = con.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS produtos (
            id      INTEGER PRIMARY KEY AUTOINCREMENT,
            nome    TEXT NOT NULL,
            preco   REAL NOT NULL,
            estoque INTEGER NOT NULL DEFAULT 0
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS pedidos (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            produto_id  INTEGER NOT NULL,
            quantidade  INTEGER NOT NULL,
            total       REAL    NOT NULL,
            data_pedido TEXT    NOT NULL,
            FOREIGN KEY (produto_id) REFERENCES produtos(id)
        )
    """)

    con.commit()
    con.close()