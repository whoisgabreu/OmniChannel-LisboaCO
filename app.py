from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import schedule
import threading
import time
import json
import modules.ETL as ETL # Responsável por baixar os cards
import asyncio

from werkzeug.security import generate_password_hash, check_password_hash

# Database
from database import Base, SessionLocal, engine
from models import Usuario


app = Flask(__name__)
app.secret_key = '4815162342'  # Necessário para usar sessão

# Dependency
def get_db():
    db = SessionLocal()
    try: 
        yield db
    finally:
        db.close()

cards = asyncio.run(ETL.main())

# Função que será executada a cada 10 minutos
def tarefa_periodica():
    cards = asyncio.run(ETL.main())
    print("Tarefa executada!")

# Loop de agendamento (roda em thread separada)
def agendador():
    schedule.every(20).minutes.do(tarefa_periodica)
    while True:
        schedule.run_pending()
        time.sleep(1)

# Rota para criar novo usuário
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":

        email = request.form["email"]
        senha = generate_password_hash(request.form["senha"])
        nome = request.form["nome"]
        cargo = request.form["cargo"]
        squad = request.form["squad"]      # <-- continua igual
        unidade = request.form["unidade"]  # <-- continua igual
        admin = "admin" in request.form
        ativo = "ativo" in request.form

        db = SessionLocal()
        if db.query(Usuario).filter_by(email=email).first():
            db.close()
            return render_template("register.html", erro="Email já cadastrado.")

        novo_usuario = Usuario(
            email=email,
            senha=senha,
            nome=nome,
            cargo=cargo,
            squad=squad,
            unidade=unidade,
            admin=admin,
            ativo=ativo,
            first_login=True
        )
        db.add(novo_usuario)
        db.commit()
        db.close()

        return redirect(url_for("login"))

    return render_template("register.html")

# Rota para resetar senha
import secrets
import string

def gerar_senha_aleatoria(tamanho=10):
    caracteres = string.ascii_letters + string.digits
    return ''.join(secrets.choice(caracteres) for _ in range(tamanho))

@app.route("/resetar-senha/<int:usuario_id>", methods=["POST"])
def resetar_senha(usuario_id):

    if not session["admin"]:
        return redirect(url_for("home"))

    db = SessionLocal()
    usuario = db.query(Usuario).filter_by(id=usuario_id).first()

    if not usuario:
        db.close()
        return "Usuário não encontrado", 404

    user = usuario.nome
    nova_senha = gerar_senha_aleatoria()
    usuario.senha = generate_password_hash(nova_senha)
    db.commit()
    db.close()
    # Aqui você poderia enviar por e-mail ou exibir no painel do admin
    return render_template("gerenciar_usuarios.html", usuario = user ,nova_senha = nova_senha)

# Rota para listar todos os usuários
@app.route("/usuarios", methods=["GET"])
def listar_usuarios():
    db = next(get_db())
    usuarios = db.query(Usuario).all()
    return jsonify([u.to_dict() for u in usuarios])

# Rota para atualizar um usuário
@app.route("/atualizar_usuario/<int:id>", methods=["POST"])
def atualizar_usuario(id):
    if "usuario" not in session:
        return redirect(url_for("login"))

    if not session["admin"]:
        return redirect(url_for("home"))

    db = SessionLocal()

    # Obtenha os dados do formulário
    nome = request.form.get("nome")
    email = request.form.get("email")
    cargo = request.form.get("cargo")
    squad = request.form.get("squad")
    unidade = request.form.get("unidade")
    admin = 'admin' in request.form  # Checkbox
    ativo = 'ativo' in request.form  # Checkbox

    # Recupere o usuário do banco
    usuario = db.get(Usuario, id)
    if not usuario:
        db.close()
        return "Usuário não encontrado", 404

    # Atualize os dados
    usuario.nome = nome
    usuario.email = email
    usuario.cargo = cargo
    usuario.squad = squad
    usuario.unidade = unidade
    usuario.admin = admin
    usuario.ativo = ativo

    db.commit()

    return redirect(url_for("gerenciar_usuarios"))

# # Rota para deletar um usuário
# @app.route("/usuarios/<int:id>", methods=["DELETE"])
# def deletar_usuario(id):
#     db = next(get_db())
#     usuario = db.query(Usuario).get(id)
#     if not usuario:
#         return jsonify({"erro": "Usuário não encontrado"}), 404
#     db.delete(usuario)
#     db.commit()
#     return jsonify({"mensagem": "Usuário deletado com sucesso."})

# -----------------------------------------------------------------

@app.route("/")
def index():
    return redirect(url_for("login"))

@app.route("/login", methods = ["GET", "POST"])
def login():
    if request.method == "POST":
        usuario = request.form["username"]
        senha = request.form["password"]

        print(generate_password_hash(senha))

        db = SessionLocal()
        user = db.query(Usuario).filter_by(email=usuario).first()
        db.close()

        if not user:
            return render_template("login.html", erro = "Usuário não encontrado.")

        if user.ativo == False:
            return render_template("login.html", erro = "Usuário desativado.")

        if user and check_password_hash(user.senha, senha):
            session["usuario"] = user.email
            session["nome"] = user.nome
            session["admin"] = user.admin
            session["id"] = user.id
            
            return redirect(url_for("home"))
        else:
            return render_template("login.html", erro = "Usuário ou senha inválidos.")
        
    return render_template("login.html")

@app.route("/home")
def home():
    if "usuario" not in session:
        return redirect(url_for("login"))
    return render_template("index.html")

@app.route("/gerenciar_usuarios")
def gerenciar_usuarios():
    if "usuario" not in session:
        return redirect(url_for("login"))
    
    if not session["admin"]:
        return redirect(url_for('home'))

    return render_template("gerenciar_usuarios.html")

@app.route("/dashboards")
def dashboards():
    if "usuario" not in session:
        return redirect(url_for("login"))

    return render_template("dashboards.html")

@app.route("/logout")
def logout():
    session.pop("usuario", None)
    return redirect(url_for("login"))


# Literalmente usada pra carregar os cards nem JS
@app.route('/get_cards')
def get_cards():
    return jsonify(cards["data"])

thread = threading.Thread(target = agendador)
thread.daemon = True
thread.start()

print("Totalmente iniciado")

# if __name__ == "__main__":
#     app.run(host="0.0.0.0", port=5005, debug = True)