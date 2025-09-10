from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import schedule
import threading
import time
import json
import requests as req
import os
import modules.ETL as ETL # Responsável por baixar os cards
import asyncio

from collections import Counter
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv

# Database
from database import Base, SessionLocal, engine
from models import Usuario

load_dotenv()
API_KEY = os.getenv("API_KEY")

app = Flask(__name__)
app.secret_key = os.urandom(10).hex()  # Necessário para usar sessão

def require_api_key(func):
    def wrapper(*args, **kwargs):
        key = request.headers.get("X-API-KEY")
        if key != API_KEY:
            return jsonify({"error": "Unauthorized"}), 401
        return func(*args, **kwargs)
    wrapper.__name__ = func.__name__
    return wrapper

# Dependency
def get_db():
    db = SessionLocal()
    try: 
        yield db
    finally:
        db.close()

cards = asyncio.run(ETL.main())
# cards = []

# Função que será executada a cada 10 minutos
def tarefa_periodica():
    global cards
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

# Rota para atualizar um usuário
@app.route("/atualizar_senha", methods=["GET", "POST"])
def atualizar_senha():

    if "usuario" not in session:
        return redirect(url_for("login"))


    if request.method == "POST":

        db = SessionLocal()

        atual_senha = request.form.get("current-password")
        nova_senha = request.form.get("new-password")
        confirmar_senha = request.form.get("confirm-password")

        print(atual_senha, nova_senha)

        if nova_senha == confirmar_senha:
            print("Pode mudar de senha")

        else:
            print("Ta errado")
        
        # Recupere o usuário do banco
        usuario = db.get(Usuario, session["id"])
        if not usuario:
            db.close()
            return "Usuário não encontrado", 404

        if check_password_hash(usuario.senha, atual_senha):

        # Atualize os dados
            usuario.senha = generate_password_hash(nova_senha)


            db.commit()

    return render_template("atualizar_senha.html")

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

# Endpoint usado como tool pelo agente do Chatbot para analisar informações do card do cliente
@app.route('/get_cards/<name>')
def get_specific_card(name):

    for card in cards["data"]:
        if name.lower() in card.get("title").lower():
            return jsonify(card)
    
    return jsonify({
        "erro": "deu erro aqui"
    })




# >>>>>>>>>>>>>>>>> TOOLS DO AGENTE ABAIXO <<<<<<<<<<<<<<<<<<

# Endpoint usado como tool pelo agente do Chatbot para analisar valores
@app.route("/vendas/recorrente/squad", methods=["GET"])
# Lembrar de colocar a autenticação "gabrielbucetinha123" <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<< NÃO ESQUECER
@require_api_key
def calcular_recorrencia_squad():
    def formatar_valor_monetario(valor):
        """
        Formata um valor float no padrão monetário brasileiro.
        """
        valor_formatado = f"R$ {valor:,.2f}".replace(",", "TEMP").replace(".", ",").replace("TEMP", ".")
        return valor_formatado

    def extrair_valor_fee(item):
        """
        Extrai e converte o valor de fee de um item, considerando o câmbio se necessário.
        """
        for chave, valor in item.items():
            if "fee" in chave.lower() and valor:
                # valor_limpo = valor.strip().replace("\xa0", "").replace(",", ".")
                valor_limpo = valor
                try:
                    valor_fee = float(valor_limpo)
                    if item.get("Sigla - Câmbio") == "USD":
                        # cambio = float(item.get("Cotação - Câmbio", "1").replace(",", "."))
                        cambio = float(item.get("Cotação - Câmbio", "1"))
                        return valor_fee * cambio
                    return valor_fee
                except ValueError:
                    print(f"[WARN] Valor inválido para conversão: {valor_limpo}")
        return 0.0

    # Obter o parâmetro de query
    squad_param = request.args.get("squad_id", "").lower()

    # Coletar dados da planilha
    response = req.get("https://n8n.v4lisboatech.com.br/webhook/planilha-clientes") # Webhook (Workflow: GL > Webhooks Importantes) que retorna os dados da planilha [Lisboa & CO] - Operação SQUADS (Aba: Clientes)
    dados = response.json()

    # Inicialização de variáveis
    receita_recorrente_ativa = receita_recorrente_churn = receita_one_time = 0.0
    qtd_ativo_recorrente = qtd_churn_recorrente = qtd_ativo_one_time = 0
    nome_squad = ""
    CONTRATO_RECORRENTE = "Recorrente"
    CONTRATO_ONE_TIME = "One Time"

    # Processamento dos dados
    for item in dados:
        if squad_param in item.get("Squad", "").lower():
            nome_squad = item.get("Squad", "")

            status = item.get("Status")
            contrato = item.get("Modal - Contrato")

            if status == "Churn" and contrato == CONTRATO_RECORRENTE:
                qtd_churn_recorrente += 1
                receita_recorrente_churn += extrair_valor_fee(item)

            elif status == "Ativo" and contrato == CONTRATO_RECORRENTE:
                qtd_ativo_recorrente += 1
                receita_recorrente_ativa += extrair_valor_fee(item)

            elif status == "Ativo" and contrato == CONTRATO_ONE_TIME:
                qtd_ativo_one_time += 1
                receita_one_time += extrair_valor_fee(item)

    # Montagem do JSON de resposta
    resposta = {
        "success": True,
        "squad": nome_squad,
        "recorrente": {
            "projetos_ativos": qtd_ativo_recorrente,
            "projetos_churn": qtd_churn_recorrente,
            "receita_recorrente_ativa": formatar_valor_monetario(receita_recorrente_ativa),
            "receita_recorrente_churn": formatar_valor_monetario(receita_recorrente_churn)
        },
        "one_time": {
            "projetos": qtd_ativo_one_time,
            "receita_one_time": formatar_valor_monetario(receita_one_time)
        },
        "total_receita": formatar_valor_monetario(receita_recorrente_ativa + receita_one_time)
    }

    return jsonify(resposta)


# Recorrência Geral
@app.route("/vendas/recorrente/geral", methods=["GET"])
@require_api_key
def calcular_recorrencia_geral():
    def formatar_valor_monetario(valor):
        """
        Formata um valor float no padrão monetário brasileiro.
        """
        valor_formatado = f"R$ {valor:,.2f}".replace(",", "TEMP").replace(".", ",").replace("TEMP", ".")
        return valor_formatado

    def extrair_valor_fee(item):
        """
        Extrai e converte o valor de fee de um item, considerando o câmbio se necessário.
        """
        for chave, valor in item.items():
            if "fee" in chave.lower() and valor:
                # valor_limpo = valor.strip().replace("\xa0", "").replace(",", ".")
                valor_limpo = valor
                try:
                    valor_fee = float(valor_limpo)
                    if item.get("Sigla - Câmbio") == "USD":
                        # cambio = float(item.get("Cotação - Câmbio", "1").replace(",", "."))
                        cambio = float(item.get("Cotação - Câmbio", "1"))
                        return valor_fee * cambio
                    return valor_fee
                except ValueError:
                    print(f"[WARN] Valor inválido para conversão: {valor_limpo}")
        return 0.0


    # Coletar dados da planilha
    response = req.get("https://n8n.v4lisboatech.com.br/webhook/planilha-clientes") # Webhook (Workflow: GL > Webhooks Importantes) que retorna os dados da planilha [Lisboa & CO] - Operação SQUADS (Aba: Clientes)
    dados = response.json()

    # Inicialização de variáveis
    receita_recorrente_ativa = receita_recorrente_churn = receita_one_time = 0.0
    qtd_ativo_recorrente = qtd_churn_recorrente = qtd_ativo_one_time = 0
    CONTRATO_RECORRENTE = "Recorrente"
    CONTRATO_ONE_TIME = "One Time"

    # Processamento dos dados
    for item in dados:
        status = item.get("Status")
        contrato = item.get("Modal - Contrato")

        if status == "Churn" and contrato == CONTRATO_RECORRENTE:
            qtd_churn_recorrente += 1
            receita_recorrente_churn += extrair_valor_fee(item)

        elif status == "Ativo" and contrato == CONTRATO_RECORRENTE:
            qtd_ativo_recorrente += 1
            receita_recorrente_ativa += extrair_valor_fee(item)

        elif status == "Ativo" and contrato == CONTRATO_ONE_TIME:
            qtd_ativo_one_time += 1
            receita_one_time += extrair_valor_fee(item)

    # Montagem do JSON de resposta
    resposta = {
        "success": True,
        "recorrente": {
            "projetos_ativos": qtd_ativo_recorrente,
            "projetos_churn": qtd_churn_recorrente,
            "receita_recorrente_ativa": formatar_valor_monetario(receita_recorrente_ativa),
            "receita_recorrente_churn": formatar_valor_monetario(receita_recorrente_churn)
        },
        "one_time": {
            "projetos": qtd_ativo_one_time,
            "receita_one_time": formatar_valor_monetario(receita_one_time)
        },
        "total_receita": formatar_valor_monetario(receita_recorrente_ativa + receita_one_time)
    }

    return jsonify(resposta)


# Analise de projetos por fase
@app.route("/projetos/fases", methods=["GET"])
@require_api_key
def contar_fases_projetos():
    def normalizar_fase(fase_texto):
        """
        Mapeia uma fase interna da planilha para um nome padronizado.
        """
        mapa_fases = {
            "onboarding": ["ONB"],
            "one_time": ["ONE TIME"],
            "churn": ["CHURN"],
            "ongoing": ["Ongoing"],
            "offboarding": ["Offboarding"],
            "perda_vendas": ["Perda de vendas"],
        }
        for nome_padrao, palavras_chave in mapa_fases.items():
            if any(p in fase_texto for p in palavras_chave):
                return nome_padrao
        return "desconhecida"

    def obter_dados_planilha():
        """
        Requisição aos dados da planilha via webhook.
        """
        try:
            url = "https://n8n.v4lisboatech.com.br/webhook/planilha-clientes"
            response = req.get(url)
            return response.json()
        except Exception as e:
            print(f"[ERRO] Falha ao obter dados da planilha: {e}")
            return []

    # Query param: ?fase=onboarding,churn,ongoing
    fases_solicitadas = request.args.get("fase", "")
    fases_solicitadas = [f.strip().lower() for f in fases_solicitadas.split(",") if f.strip()]

    # Obtem os dados reais da planilha
    dados = obter_dados_planilha()

    # Contar os projetos por fase padronizada
    contagem_por_fase = Counter()
    total_projetos = 0

    for item in dados:
        fase_bruta = item.get("Fase Pipefy", "")
        fase_norm = normalizar_fase(fase_bruta)
        contagem_por_fase[fase_norm] += 1
        total_projetos += 1

    # Identificar fases que o usuário pediu mas não existem nos dados
    fases_nao_encontradas = [f for f in fases_solicitadas if f not in contagem_por_fase]

    # Montagem dos detalhes das fases
    detalhes_fase = []
    for fase_nome in fases_solicitadas:
        count = contagem_por_fase.get(fase_nome, 0)
        detalhes_fase.append({
            "fase": fase_nome,
            "descricao": f"Fase padronizada: {fase_nome}",
            "porcentagem_total": f"{round((count / total_projetos) * 100, 2)}%" if total_projetos else 0
        })

    # Estrutura de resposta final
    resposta = {
        "success": True,
        "resumo": {
            "total_projetos": total_projetos,
            "projetos_por_fase": {fase: contagem_por_fase.get(fase, 0) for fase in fases_solicitadas},
            "fases_nao_encontradas": fases_nao_encontradas,
            "data_consulta": datetime.utcnow().isoformat()
        },
        "detalhes_fase": detalhes_fase
    }

    return jsonify(resposta)

thread = threading.Thread(target = agendador)
thread.daemon = True
thread.start()

print("Totalmente iniciado")

# if __name__ == "__main__":
#     app.run(host="0.0.0.0", port=5005, debug = True)