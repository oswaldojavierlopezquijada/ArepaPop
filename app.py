from flask import Flask, render_template, request, redirect, url_for
from banco import conectar, criar_tabelas
from datetime import datetime

app = Flask(__name__)

# Cria as tabelas no banco de dados ao iniciar a aplicação
criar_tabelas()

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

    # Produtos com estoque abaixo de 5 unidades
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
# PASSO 3 — Cadastrar Produto
# ---------------------------------------------------------
@app.route("/cadastrar-produto", methods=["GET", "POST"])
def cadastrar_produto():
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

        # Busca o produto para pegar preço e verificar estoque
        produto = cur.execute(
            "SELECT nome, preco, estoque FROM produtos WHERE id = ?",
            (produto_id,)
        ).fetchone()

        if not produto:
            con.close()
            return "Produto não encontrado", 404

        nome_prod, preco, estoque_atual = produto

        # Valida se tem estoque suficiente
        if quantidade > estoque_atual:
            produtos_disponiveis = cur.execute("SELECT id, nome, estoque FROM produtos WHERE estoque > 0").fetchall()
            con.close()
            return render_template("novo_pedido.html",
                erro=f"Estoque insuficiente! Disponível: {estoque_atual} unidades.",
                produtos=produtos_disponiveis
            )

        total = preco * quantidade
        agora = datetime.now().strftime("%d/%m/%Y %H:%M")

        # Registra o pedido
        cur.execute(
            "INSERT INTO pedidos (produto_id, quantidade, total, data_pedido) VALUES (?, ?, ?, ?)",
            (produto_id, quantidade, total, agora)
        )
        # Desconta do estoque
        cur.execute(
            "UPDATE produtos SET estoque = estoque - ? WHERE id = ?",
            (quantidade, produto_id)
        )
        con.commit()
        con.close()
        return redirect(url_for("listar_pedidos"))

    # GET: lista só produtos com estoque > 0
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
# Inicialização do Servidor Local
# ---------------------------------------------------------

if __name__ == "__main__":
    app.run(debug=True)