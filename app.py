from flask import Flask, render_template, request, redirect, url_for, session
from banco import conectar, criar_tabelas
from datetime import datetime
import os

app = Flask(__name__)
# A secret_key é obrigatória para usar session em Flask
app.secret_key = "arepapop_secreto_123"

# ---------------------------------------------------------
# SISTEMA DE AUTENTICAÇÃO (SESSÃO ADM)
# ---------------------------------------------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    erro = None
    if request.method == "POST":
        usuario = request.form["usuario"]
        senha = request.form["senha"]
        
        if usuario == "admin" and senha == "arepa123":
            session["admin"] = True
            return redirect(url_for('index'))
        else:
            erro = "Usuário ou senha incorretos!"
            
    return render_template("login.html", erro=erro)

@app.route("/logout")
def logout():
    session.pop("admin", None)
    return redirect(url_for('index'))

# ---------------------------------------------------------
# PASSO 1 — Página Inicial (Dashboard)
# ---------------------------------------------------------
@app.route("/")
def index():
    con = conectar()
    cur = con.cursor()

    total_produtos = cur.execute("SELECT COUNT(*) FROM produtos").fetchone()[0]
    total_pedidos  = cur.execute("SELECT COUNT(*) FROM pedidos").fetchone()[0]
    receita = cur.execute("SELECT SUM(total) FROM pedidos").fetchone()[0] or 0

    alertas = cur.execute(
        "SELECT nome, estoque FROM produtos WHERE estoque < 5"
    ).fetchall()

    con.close()
    return render_template("index.html",
        total_produtos=total_produtos,
        total_pedidos=total_pedidos,
        receita=receita,
        alertas=alertas
    )

# ---------------------------------------------------------
# PASSO 2 — Listar Produtos
# ---------------------------------------------------------
@app.route("/produtos")
def listar_produtos():
    con = conectar()
    cur = con.cursor()
    produtos = cur.execute(
        "SELECT * FROM produtos ORDER BY nome"
    ).fetchall()
    con.close()
    return render_template("produtos.html", produtos=produtos)

# ---------------------------------------------------------
# PASSO 3 — Cadastrar Produto (PROTEGIDO)
# ---------------------------------------------------------
@app.route("/cadastrar-produto", methods=["GET", "POST"])
def cadastrar_produto():
    if not session.get("admin"):
        return redirect(url_for('login'))

    if request.method == "POST":
        nome    = request.form["nome"]
        preco   = float(request.form["preco"])
        estoque = int(request.form["estoque"])

        con = conectar()
        cur = con.cursor()
        cur.execute(
            "INSERT INTO produtos (nome, preco, estoque) VALUES (?, ?, ?)",
            (nome, preco, estoque)
        )
        con.commit()
        con.close()
        return redirect(url_for("listar_produtos"))

    return render_template("cadastrar_produto.html")

# ---------------------------------------------------------
# PASSO 4 — Registrar Pedido
# ---------------------------------------------------------
@app.route("/novo-pedido", methods=["GET", "POST"])
def novo_pedido():
    if request.method == "POST":
        produto_id = int(request.form["produto_id"])
        quantidade = int(request.form["quantidade"])

        con = conectar()
        cur = con.cursor()

        produto = cur.execute(
            "SELECT nome, preco, estoque FROM produtos WHERE id = ?",
            (produto_id,)
        ).fetchone()

        if not produto:
            con.close()
            return "Produto não encontrado", 404

        nome_prod, preco, estoque_atual = produto

        if quantidade > estoque_atual:
            produtos_disponiveis = cur.execute("SELECT id, nome, estoque FROM produtos WHERE estoque > 0").fetchall()
            con.close()
            return render_template("novo_pedido.html",
                erro=f"Estoque insuficiente! Disponível: {estoque_atual} unidades.",
                produtos=produtos_disponiveis
            )

        total = preco * quantidade
        agora = datetime.now().strftime("%d/%m/%Y %H:%M")

        cur.execute(
            "INSERT INTO pedidos (produto_id, quantidade, total, data_pedido) VALUES (?, ?, ?, ?)",
            (produto_id, quantidade, total, agora)
        )
        cur.execute(
            "UPDATE produtos SET estoque = estoque - ? WHERE id = ?",
            (quantidade, produto_id)
        )
        con.commit()
        con.close()
        return redirect(url_for("listar_pedidos"))

    con = conectar()
    cur = con.cursor()
    produtos = cur.execute(
        "SELECT id, nome, estoque FROM produtos WHERE estoque > 0"
    ).fetchall()
    con.close()
    return render_template("novo_pedido.html", produtos=produtos, erro=None)

# ---------------------------------------------------------
# PASSO 5 — Histórico de Pedidos
# ---------------------------------------------------------
@app.route("/pedidos")
def listar_pedidos():
    con = conectar()
    cur = con.cursor()
    pedidos = cur.execute("""
        SELECT p.id, pr.nome, p.quantidade, p.total, p.data_pedido
        FROM pedidos p
        JOIN produtos pr ON p.produto_id = pr.id
        ORDER BY p.id DESC
    """).fetchall()
    con.close()
    return render_template("pedidos.html", pedidos=pedidos)

# ---------------------------------------------------------
# PASSO 6 — Ranking de Vendas
# ---------------------------------------------------------
@app.route("/ranking")
def ranking():
    con = conectar()
    cur = con.cursor()
    ranking_vendas = cur.execute("""
        SELECT pr.nome,
               SUM(p.quantidade) AS total_qtd,
               SUM(p.total)      AS total_valor
        FROM pedidos p
        JOIN produtos pr ON p.produto_id = pr.id
        GROUP BY pr.id
        ORDER BY total_valor DESC
    """).fetchall()
    con.close()
    return render_template("ranking.html", ranking=ranking_vendas)

# ---------------------------------------------------------
# PASSO 7 — Contato e Comentários
# ---------------------------------------------------------
@app.route("/contato", methods=["GET", "POST"])
def contato():
    con = conectar()
    cur = con.cursor()

    if request.method == "POST":
        nome = request.form["nome"]
        email = request.form["email"]
        mensagem = request.form["mensagem"]
        agora = datetime.now().strftime("%d/%m/%Y %H:%M")

        cur.execute(
            "INSERT INTO comentarios (nome, email, mensagem, data_envio) VALUES (?, ?, ?, ?)",
            (nome, email, mensagem, agora)
        )
        con.commit()
        con.close()
        return redirect(url_for("contato"))

    comentarios = cur.execute(
        "SELECT nome, mensagem, data_envio FROM comentarios ORDER BY id DESC"
    ).fetchall()
    con.close()
    
    return render_template("contacto.html", comentarios=comentarios)

# ---------------------------------------------------------
# PASSO 8 — Editar Produto (PROTEGIDO)
# ---------------------------------------------------------
@app.route("/editar-produto/<int:id>", methods=["GET", "POST"])
def editar_produto(id):
    if not session.get("admin"):
        return redirect(url_for('login'))

    con = conectar()
    cur = con.cursor()

    if request.method == "POST":
        nome = request.form["nome"]
        preco = float(request.form["preco"])
        estoque = int(request.form["estoque"])

        cur.execute(
            "UPDATE produtos SET nome = ?, preco = ?, estoque = ? WHERE id = ?",
            (nome, preco, estoque, id)
        )
        con.commit()
        con.close()
        return redirect(url_for("listar_produtos"))

    produto = cur.execute("SELECT * FROM produtos WHERE id = ?", (id,)).fetchone()
    con.close()

    if not produto:
        return "Produto não encontrado", 404

    return render_template("editar_produto.html", produto=produto)

# ---------------------------------------------------------
# PASSO 9 — Apagar Produto (PROTEGIDO)
# ---------------------------------------------------------
@app.route("/apagar-produto/<int:id>", methods=["POST"])
def apagar_produto(id):
    if not session.get("admin"):
        return redirect(url_for('login'))

    con = conectar()
    cur = con.cursor()
    
    cur.execute("DELETE FROM produtos WHERE id = ?", (id,))
    con.commit()
    con.close()
    
    return redirect(url_for("listar_produtos"))

# ---------------------------------------------------------
# Inicialização do Servidor (ÚNICO BLOCO)
# ---------------------------------------------------------
if __name__ == "__main__":
    # Garante que as tabelas sejam criadas ao iniciar
    criar_tabelas()
    
    porta = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=porta, debug=True)