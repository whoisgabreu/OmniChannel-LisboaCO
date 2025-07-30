from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import schedule
import threading
import time
import json
import modules.ETL as ETL
import asyncio
import os
import secrets
import string

from werkzeug.security import generate_password_hash, check_password_hash
from authlib.integrations.flask_client import OAuth

from dotenv import load_dotenv
import os

load_dotenv()

client_id = os.getenv("CLIENT_ID")
client_secret = os.getenv("CLIENT_SECRET")

# Database
from database import Base, SessionLocal, engine
from models import Usuario

app = Flask(__name__)
app.secret_key = '4815162342'

# ================= OAuth com Google =================
oauth = OAuth(app)
google = oauth.register(
    name='google',
    client_id=client_id,
    client_secret=client_secret,
    access_token_url='https://oauth2.googleapis.com/token',
    access_token_params=None,
    authorize_url='https://accounts.google.com/o/oauth2/auth',
    authorize_params={'access_type': 'offline'},
    api_base_url='https://www.googleapis.com/oauth2/v1/',
    client_kwargs={'scope': 'openid email profile'}
)
# ===================================================

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

cards = asyncio.run(ETL.main())

# Função periódica
def tarefa_periodica():
    cards = asyncio.run(ETL.main())
    print("Tarefa executada!")

def agendador():
    schedule.every(20).minutes.do(tarefa_periodica)
    while True:
        schedule.run_pending()
        time.sleep(1)

# ========== LOGIN COM GOOGLE ==========
@app.route("/login/google")
def login_google():
    redirect_uri = url_for("authorize_google", _external=True)
    return google.authorize_redirect(redirect_uri)

@app.route("/login/google/authorized")
def authorize_google():
    token = google.authorize_access_token()
    resp = google.get("userinfo")
    user_info = resp.json()

    email = user_info["email"]
    nome = user_info.get("name", "")

    db = SessionLocal()
    user = db.query(Usuario).filter_by(email=email).first()

    if not user:
        novo_usuario = Usuario(
            email=email,
            senha="",
            nome=nome,
            cargo="",
            squad="",
            unidade="",
            admin=False,
            ativo=True,
            first_login=True
        )
        db.add(novo_usuario)
        db.commit()
        user = novo_usuario

    if not user.ativo:
        db.close()
        return render_template("login.html", erro="Usuário desativado.")

    session["usuario"] = user.email
    session["nome"] = user.nome
    session["admin"] = user.admin
    session["id"] = user.id
    db.close()

    return redirect(url_for("home"))
# =======================================

@app.route("/")
def index():
    return redirect(url_for("login"))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        usuario = request.form["username"]
        senha = request.form["password"]

        db = SessionLocal()
        user = db.query(Usuario).filter_by(email=usuario).first()
        db.close()

        if not user:
            return render_template("login.html", erro="Usuário não encontrado.")
        if not user.ativo:
            return render_template("login.html", erro="Usuário desativado.")
        if user and check_password_hash(user.senha, senha):
            session["usuario"] = user.email
            session["nome"] = user.nome
            session["admin"] = user.admin
            session["id"] = user.id
            return redirect(url_for("home"))
        else:
            return render_template("login.html", erro="Usuário ou senha inválidos.")

    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email = request.form["email"]
        senha = generate_password_hash(request.form["senha"])
        nome = request.form["nome"]
        cargo = request.form["cargo"]
        squad = request.form["squad"]
        unidade = request.form["unidade"]
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

@app.route("/resetar-senha/<int:usuario_id>", methods=["POST"])
def resetar_senha(usuario_id):
    if not session.get("admin"):
        return redirect(url_for("home"))

    db = SessionLocal()
    usuario = db.query(Usuario).filter_by(id=usuario_id).first()
    if not usuario:
        db.close()
        return "Usuário não encontrado", 404

    user = usuario.nome
    nova_senha = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(10))
    usuario.senha = generate_password_hash(nova_senha)
    db.commit()
    db.close()
    return render_template("gerenciar_usuarios.html", usuario=user, nova_senha=nova_senha)

@app.route("/usuarios", methods=["GET"])
def listar_usuarios():
    db = next(get_db())
    usuarios = db.query(Usuario).all()
    return jsonify([u.to_dict() for u in usuarios])

@app.route("/atualizar_usuario/<int:id>", methods=["POST"])
def atualizar_usuario(id):
    if "usuario" not in session:
        return redirect(url_for("login"))
    if not session["admin"]:
        return redirect(url_for("home"))

    db = SessionLocal()
    usuario = db.get(Usuario, id)
    if not usuario:
        db.close()
        return "Usuário não encontrado", 404

    usuario.nome = request.form.get("nome")
    usuario.email = request.form.get("email")
    usuario.cargo = request.form.get("cargo")
    usuario.squad = request.form.get("squad")
    usuario.unidade = request.form.get("unidade")
    usuario.admin = 'admin' in request.form
    usuario.ativo = 'ativo' in request.form

    db.commit()
    return redirect(url_for("gerenciar_usuarios"))

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

@app.route('/get_cards')
def get_cards():
    return jsonify(cards["data"])

thread = threading.Thread(target=agendador)
thread.daemon = True
thread.start()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5005, debug=True)