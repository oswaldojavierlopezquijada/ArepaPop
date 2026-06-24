# ArepaPop
oswaldo javier lopez quijada
# 🍔 Cantina Digital — Grupo 2

> **Projeto Final · Qualifica DF · Programador de Sistemas · 2026**

Sistema web para gerenciar produtos, pedidos e estoque de uma cantina escolar.
Desenvolvido com **Python + Flask + SQLite + HTML/CSS**.

---

## 🎯 Objetivo

Criar uma aplicação web funcional que permita:
- Cadastrar e listar produtos com preço e estoque
- Registrar pedidos descontando o estoque automaticamente
- Alertar quando o estoque de um produto estiver baixo
- Visualizar o total vendido por produto

---

## 🗂️ Estrutura de pastas

```
grupo2-cantina/
│
├── app.py                    ← arquivo principal Flask
├── banco.py                  ← funções do banco de dados
├── requirements.txt          ← dependências do projeto
│
├── templates/
│   ├── base.html             ← layout base (navbar, estilo)
│   ├── index.html            ← página inicial com resumo
│   ├── produtos.html         ← lista de produtos e estoque
│   ├── cadastrar_produto.html
│   ├── pedidos.html          ← histórico de pedidos
│   └── novo_pedido.html      ← formulário de pedido
│
└── static/
    └── style.css             ← estilos da aplicação
```

---

## 🗃️ Banco de Dados

### Tabelas

#### `produtos`
| Coluna    | Tipo    | Descrição                        |
|-----------|---------|----------------------------------|
| `id`      | INTEGER | Chave primária (auto incremento) |
| `nome`    | TEXT    | Nome do produto                  |
| `preco`   | REAL    | Preço unitário                   |
| `estoque` | INTEGER | Quantidade em estoque            |

#### `pedidos`
| Coluna       | Tipo    | Descrição                        |
|--------------|---------|----------------------------------|
| `id`         | INTEGER | Chave primária (auto incremento) |
| `produto_id` | INTEGER | Referência ao produto            |
| `quantidade` | INTEGER | Quantidade pedida                |
| `total`      | REAL    | Valor total do pedido            |
| `data_pedido`| TEXT    | Data e hora do pedido            |

### Código do banco (`banco.py`)

```python
import sqlite3

def conectar():
    return sqlite3.connect("cantina.db")

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
```

---

## 🚀 Rotas da aplicação

### Passo 1 — Página inicial

**Rota:** `GET /`

Exibe resumo: total de produtos, total de pedidos e receita total.

```python
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
```

**Template `index.html`:**
```html
{% extends "base.html" %}
{% block conteudo %}
  <h1>🍔 Cantina Digital</h1>
  <div class="cards">
    <div class="card">
      <h2>{{ total_produtos }}</h2>
      <p>Produtos cadastrados</p>
    </div>
    <div class="card">
      <h2>{{ total_pedidos }}</h2>
      <p>Pedidos realizados</p>
    </div>
    <div class="card">
      <h2>R$ {{ "%.2f"|format(receita) }}</h2>
      <p>Receita total</p>
    </div>
  </div>

  {% if alertas %}
    <div class="alerta">
      <strong>⚠️ Estoque baixo:</strong>
      {% for a in alertas %}
        {{ a[0] }} ({{ a[1] }} unidades){% if not loop.last %}, {% endif %}
      {% endfor %}
    </div>
  {% endif %}
{% endblock %}
```

---

### Passo 2 — Listar produtos

**Rota:** `GET /produtos`

Exibe todos os produtos com nome, preço e estoque atual.

```python
@app.route("/produtos")
def listar_produtos():
    con = conectar()
    cur = con.cursor()
    produtos = cur.execute(
        "SELECT * FROM produtos ORDER BY nome"
    ).fetchall()
    con.close()
    return render_template("produtos.html", produtos=produtos)
```

**Template `produtos.html`:**
```html
{% extends "base.html" %}
{% block conteudo %}
  <h1>🛒 Produtos</h1>
  <a href="/cadastrar-produto" class="btn">+ Cadastrar produto</a>

  <table>
    <thead>
      <tr><th>Produto</th><th>Preço</th><th>Estoque</th><th>Status</th></tr>
    </thead>
    <tbody>
      {% for p in produtos %}
      <tr>
        <td>{{ p[1] }}</td>
        <td>R$ {{ "%.2f"|format(p[2]) }}</td>
        <td>{{ p[3] }} un.</td>
        <td>
          {% if p[3] == 0 %}
            <span class="badge vermelho">Sem estoque</span>
          {% elif p[3] < 5 %}
            <span class="badge amarelo">Estoque baixo</span>
          {% else %}
            <span class="badge verde">OK</span>
          {% endif %}
        </td>
      </tr>
      {% endfor %}
    </tbody>
  </table>
{% endblock %}
```

---

### Passo 3 — Cadastrar produto

**Rotas:** `GET /cadastrar-produto` → formulário | `POST /cadastrar-produto` → salva

```python
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
        return redirect("/produtos")

    return render_template("cadastrar_produto.html")
```

---

### Passo 4 — Registrar pedido

**Rotas:** `GET /novo-pedido` → formulário | `POST /novo-pedido` → salva e desconta estoque

```python
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
            con.close()
            return render_template("novo_pedido.html",
                erro=f"Estoque insuficiente! Disponível: {estoque_atual} unidades.",
                produtos=cur.execute("SELECT id, nome, estoque FROM produtos WHERE estoque > 0").fetchall()
            )

        total = preco * quantidade
        from datetime import datetime
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
        return redirect("/pedidos")

    # GET: lista só produtos com estoque > 0
    con = conectar()
    cur = con.cursor()
    produtos = cur.execute(
        "SELECT id, nome, estoque FROM produtos WHERE estoque > 0"
    ).fetchall()
    con.close()
    return render_template("novo_pedido.html", produtos=produtos, erro=None)
```

---

### Passo 5 — Histórico de pedidos

**Rota:** `GET /pedidos`

Lista todos os pedidos com JOIN para mostrar o nome do produto.

```python
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
```

---

### Passo 6 — Ranking de vendas

**Rota:** `GET /ranking`

Mostra o total vendido agrupado por produto usando `GROUP BY`.

```python
@app.route("/ranking")
def ranking():
    con = conectar()
    cur = con.cursor()
    ranking = cur.execute("""
        SELECT pr.nome,
               SUM(p.quantidade) AS total_qtd,
               SUM(p.total)      AS total_valor
        FROM pedidos p
        JOIN produtos pr ON p.produto_id = pr.id
        GROUP BY pr.id
        ORDER BY total_valor DESC
    """).fetchall()
    con.close()
    return render_template("ranking.html", ranking=ranking)
```

---

## 📄 Arquivo principal (`app.py`)

```python
from flask import Flask, render_template, request, redirect
from banco import conectar, criar_tabelas

app = Flask(__name__)
criar_tabelas()

# Cole aqui todas as rotas dos passos acima

if __name__ == "__main__":
    app.run(debug=True)
```

---

## 📦 Dependências (`requirements.txt`)

```
flask
gunicorn
```

---

## 🎨 Estilo base (`static/style.css`)

```css
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: Arial, sans-serif; background: #f5f5f5; color: #333; }
nav { background: #2d6a2d; padding: 1rem 2rem; }
nav a { color: white; text-decoration: none; margin-right: 1.5rem; font-weight: bold; }
.container { max-width: 900px; margin: 2rem auto; padding: 0 1rem; }
h1 { margin-bottom: 1.5rem; color: #2d6a2d; }
table { width: 100%; border-collapse: collapse; background: white; border-radius: 8px; overflow: hidden; }
th { background: #2d6a2d; color: white; padding: 0.75rem 1rem; text-align: left; }
td { padding: 0.75rem 1rem; border-bottom: 1px solid #eee; }
.btn { display: inline-block; padding: 0.5rem 1rem; background: #2d6a2d; color: white;
       text-decoration: none; border-radius: 6px; border: none; cursor: pointer; margin-bottom: 1rem; }
.badge { padding: 0.25rem 0.75rem; border-radius: 20px; font-size: 0.85rem; font-weight: bold; }
.badge.verde   { background: #d4edda; color: #155724; }
.badge.amarelo { background: #fff3cd; color: #856404; }
.badge.vermelho{ background: #f8d7da; color: #721c24; }
.alerta { background: #fff3cd; border-left: 4px solid #ffc107; padding: 1rem; border-radius: 4px; margin: 1rem 0; }
.cards { display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem; margin-bottom: 1.5rem; }
.card { background: white; padding: 2rem; border-radius: 8px; text-align: center; border-left: 4px solid #2d6a2d; }
.card h2 { font-size: 2rem; color: #2d6a2d; }
form label { display: block; margin: 1rem 0 0.25rem; font-weight: bold; }
form input, form select { width: 100%; padding: 0.5rem; border: 1px solid #ccc; border-radius: 4px; }
form button { margin-top: 1.5rem; }
.erro { background: #f8d7da; color: #721c24; padding: 0.75rem 1rem; border-radius: 4px; margin-bottom: 1rem; }
```

---

## ☁️ Deploy no Render

1. Suba o projeto no GitHub (faça fork deste repo e implemente nele)
2. Acesse [render.com](https://render.com) e crie uma conta gratuita
3. Clique em **New > Web Service** e conecte seu repositório
4. Configure:
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app:app`
5. Clique em **Deploy**!

---

## ✅ Checklist de entrega

- [ ] Cadastro de produtos funcionando
- [ ] Pedido desconta o estoque automaticamente
- [ ] Validação de estoque insuficiente implementada
- [ ] Alerta de estoque baixo na página inicial
- [ ] Histórico de pedidos com JOIN funcionando
- [ ] Ranking de vendas com GROUP BY
- [ ] Aplicação rodando no Render com URL pública
- [ ] README atualizado com a URL do deploy

---

*Qualifica DF · 2026 · Programador de Sistemas*
