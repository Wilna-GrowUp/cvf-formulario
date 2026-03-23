from functools import wraps
from io import BytesIO
import secrets
import hashlib

from datetime import datetime, date, timezone
from flask import Flask, render_template, request, redirect, url_for, flash, session, send_file, make_response
from openpyxl import Workbook
from sqlalchemy import func, text
from zoneinfo import ZoneInfo

from config import Config
from models import db, RespostaCVF, Empresa
from forms_data import FORM_INSTRUCTIONS, DIMENSIONS


app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)

with app.app_context():
    db.create_all()

COOKIE_NAME = "cvf_resposta_token"


def converter_para_int(nome_campo):
    """
    Lê um campo do formulário e converte para inteiro.
    Se vier vazio ou inválido, retorna 0.
    """
    valor = request.form.get(nome_campo, "").strip()

    if valor == "":
        return 0

    try:
        return int(valor)
    except ValueError:
        return 0


def coletar_respostas():
    """
    Monta um dicionário com todos os 48 campos da pesquisa.
    """
    dados = {}

    for dimension in DIMENSIONS:
        dimension_id = dimension["id"]

        for numero_afirmacao in range(1, 5):
            campo_atual = f"{dimension_id}_atual_{numero_afirmacao}"
            campo_ideal = f"{dimension_id}_ideal_{numero_afirmacao}"

            dados[campo_atual] = converter_para_int(campo_atual)
            dados[campo_ideal] = converter_para_int(campo_ideal)

    return dados


def cookie_deve_ser_secure():
    """
    Em produção (Render com HTTPS), o cookie deve ser secure=True.
    Localmente, deve ser False.
    """
    return not app.debug


def converter_utc_para_brasil(data_utc):
    """
    Recebe uma data UTC salva no banco e converte para o horário de São Paulo.
    """
    if not data_utc:
        return None

    if data_utc.tzinfo is None:
        data_utc = data_utc.replace(tzinfo=timezone.utc)

    return data_utc.astimezone(ZoneInfo("America/Sao_Paulo"))


def formatar_data_hora_brasil(data_utc):
    """
    Converte a data UTC para horário de São Paulo e devolve em texto.
    """
    data_brasil = converter_utc_para_brasil(data_utc)

    if not data_brasil:
        return ""

    return data_brasil.strftime("%Y-%m-%d %H:%M:%S")


def validar_somas(dados):
    """
    Verifica se cada dimensão soma exatamente 100
    no cenário atual e no cenário ideal.
    Retorna uma lista com mensagens de erro.
    """
    erros = []

    for dimension in DIMENSIONS:
        dimension_id = dimension["id"]
        titulo = dimension["title"]

        soma_atual = sum(dados[f"{dimension_id}_atual_{i}"] for i in range(1, 5))
        soma_ideal = sum(dados[f"{dimension_id}_ideal_{i}"] for i in range(1, 5))

        if soma_atual != 100:
            erros.append(f"{titulo} - cenário atual soma {soma_atual} e deve ser 100")

        if soma_ideal != 100:
            erros.append(f"{titulo} - cenário ideal soma {soma_ideal} e deve ser 100")

    return erros


def gerar_token_anonimo():
    """
    Gera um código aleatório para marcar anonimamente o navegador.
    """
    return secrets.token_urlsafe(32)


def gerar_hash_token(token):
    """
    Transforma o token em um hash para não salvar o valor original no banco.
    """
    base = f"{token}{app.config['SECRET_KEY']}"
    return hashlib.sha256(base.encode("utf-8")).hexdigest()


def navegador_ja_respondeu():
    """
    Verifica se este navegador já enviou uma resposta antes.
    """
    token = request.cookies.get(COOKIE_NAME)

    if not token:
        return False

    token_hash = gerar_hash_token(token)
    resposta_existente = RespostaCVF.query.filter_by(response_token_hash=token_hash).first()

    return resposta_existente is not None


def normalizar_nome_empresa(nome_empresa):
    """
    Padroniza o nome para comparação.
    Exemplo: remove espaços extras e deixa tudo minúsculo.
    """
    return " ".join(nome_empresa.strip().lower().split())


def gerar_iniciais_empresa(nome_empresa):
    """
    Gera as iniciais da empresa com base nas palavras do nome.
    Exemplo: GrowUp Teste -> GT
    """
    palavras = [palavra for palavra in nome_empresa.strip().split() if palavra]

    if not palavras:
        return "EM"

    iniciais = "".join(palavra[0].upper() for palavra in palavras[:2])

    if len(iniciais) == 1:
        iniciais += "X"

    return iniciais


def gerar_codigo_empresa(nome_empresa, data_cadastro, quantidade_existente):
    """
    Gera o código no formato:
    INICIAIS-AAAAMMDDNN
    Exemplo: GT-2026031901
    """
    iniciais = gerar_iniciais_empresa(nome_empresa)
    data_formatada = data_cadastro.strftime("%Y%m%d")
    sequencial = quantidade_existente + 1

    return f"{iniciais}-{data_formatada}{sequencial:02d}"


def admin_required(func):
    """
    Protege rotas administrativas.
    Só permite acesso se o admin estiver logado.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not session.get("admin_logado"):
            flash("Faça login como administrador para acessar esta área.", "erro")
            return redirect(url_for("admin_login"))
        return func(*args, **kwargs)

    return wrapper


@app.route("/")
def index():
    """
    Tela inicial de apresentação da pesquisa.
    """
    return render_template("index.html")


@app.route("/consentimento", methods=["GET", "POST"])
def consentimento():
    """
    Tela separada de consentimento.
    """
    if request.method == "POST":
        resposta_consentimento = request.form.get("consentimento", "").strip().lower()

        if resposta_consentimento != "sim":
            flash("Você precisa aceitar o termo de consentimento para continuar.", "erro")
            return render_template("consentimento.html")

        session["consentimento_aceito"] = True
        return redirect(url_for("codigo_empresa"))

    return render_template("consentimento.html")


@app.route("/codigo", methods=["GET", "POST"])
def codigo_empresa():
    """
    Tela onde o respondente informa o código da empresa.
    """
    if not session.get("consentimento_aceito"):
        flash("Você precisa aceitar o termo antes de continuar.", "erro")
        return redirect(url_for("consentimento"))

    if request.method == "POST":
        codigo = request.form.get("codigo", "").strip()

        if not codigo:
            flash("Informe o código da empresa.", "erro")
            return render_template("codigo_empresa.html")

        empresa = Empresa.query.filter_by(codigo=codigo).first()

        if not empresa:
            flash("Código da empresa inválido.", "erro")
            return render_template("codigo_empresa.html")

        hoje = date.today()

        if hoje < empresa.data_inicio:
            flash(
                f"Esta pesquisa estará disponível a partir de {empresa.data_inicio.strftime('%d/%m/%Y')}.",
                "erro"
            )
            return render_template("codigo_empresa.html")

        if hoje > empresa.data_fim:
            flash(
                f"O período desta pesquisa foi encerrado em {empresa.data_fim.strftime('%d/%m/%Y')}.",
                "erro"
            )
            return render_template("codigo_empresa.html")

        session["cod_emp"] = empresa.codigo

        return redirect(url_for("pesquisa"))

    return render_template("codigo_empresa.html")


@app.route("/pesquisa", methods=["GET", "POST"])
def pesquisa():
    if not session.get("cod_emp"):
        flash("Informe o código da empresa para acessar a pesquisa.", "erro")
        return redirect(url_for("codigo_empresa"))

    if navegador_ja_respondeu():
        return render_template("resposta_bloqueada.html")

    if not session.get("consentimento_aceito"):
        flash("Você precisa aceitar o termo de consentimento antes de responder a pesquisa.", "erro")
        return redirect(url_for("consentimento"))

    if request.method == "POST":
        if navegador_ja_respondeu():
            return render_template("resposta_bloqueada.html")

        dados = coletar_respostas()
        erros = validar_somas(dados)

        if erros:
            mensagem = "Corrija os seguintes pontos: " + " | ".join(erros)
            flash(mensagem, "erro")
            return render_template(
                "pesquisa.html",
                form_instructions=FORM_INSTRUCTIONS,
                dimensions=DIMENSIONS
            )

        token = gerar_token_anonimo()
        token_hash = gerar_hash_token(token)

        while RespostaCVF.query.filter_by(response_token_hash=token_hash).first():
            token = gerar_token_anonimo()
            token_hash = gerar_hash_token(token)

        resposta = RespostaCVF(
            cod_emp=session.get("cod_emp"),
            consentimento=True,
            response_token_hash=token_hash,

            caracteristicas_dominantes_atual_1=dados["caracteristicas_dominantes_atual_1"],
            caracteristicas_dominantes_atual_2=dados["caracteristicas_dominantes_atual_2"],
            caracteristicas_dominantes_atual_3=dados["caracteristicas_dominantes_atual_3"],
            caracteristicas_dominantes_atual_4=dados["caracteristicas_dominantes_atual_4"],
            caracteristicas_dominantes_ideal_1=dados["caracteristicas_dominantes_ideal_1"],
            caracteristicas_dominantes_ideal_2=dados["caracteristicas_dominantes_ideal_2"],
            caracteristicas_dominantes_ideal_3=dados["caracteristicas_dominantes_ideal_3"],
            caracteristicas_dominantes_ideal_4=dados["caracteristicas_dominantes_ideal_4"],

            lideranca_organizacional_atual_1=dados["lideranca_organizacional_atual_1"],
            lideranca_organizacional_atual_2=dados["lideranca_organizacional_atual_2"],
            lideranca_organizacional_atual_3=dados["lideranca_organizacional_atual_3"],
            lideranca_organizacional_atual_4=dados["lideranca_organizacional_atual_4"],
            lideranca_organizacional_ideal_1=dados["lideranca_organizacional_ideal_1"],
            lideranca_organizacional_ideal_2=dados["lideranca_organizacional_ideal_2"],
            lideranca_organizacional_ideal_3=dados["lideranca_organizacional_ideal_3"],
            lideranca_organizacional_ideal_4=dados["lideranca_organizacional_ideal_4"],

            gestao_de_pessoas_atual_1=dados["gestao_de_pessoas_atual_1"],
            gestao_de_pessoas_atual_2=dados["gestao_de_pessoas_atual_2"],
            gestao_de_pessoas_atual_3=dados["gestao_de_pessoas_atual_3"],
            gestao_de_pessoas_atual_4=dados["gestao_de_pessoas_atual_4"],
            gestao_de_pessoas_ideal_1=dados["gestao_de_pessoas_ideal_1"],
            gestao_de_pessoas_ideal_2=dados["gestao_de_pessoas_ideal_2"],
            gestao_de_pessoas_ideal_3=dados["gestao_de_pessoas_ideal_3"],
            gestao_de_pessoas_ideal_4=dados["gestao_de_pessoas_ideal_4"],

            elemento_de_uniao_atual_1=dados["elemento_de_uniao_atual_1"],
            elemento_de_uniao_atual_2=dados["elemento_de_uniao_atual_2"],
            elemento_de_uniao_atual_3=dados["elemento_de_uniao_atual_3"],
            elemento_de_uniao_atual_4=dados["elemento_de_uniao_atual_4"],
            elemento_de_uniao_ideal_1=dados["elemento_de_uniao_ideal_1"],
            elemento_de_uniao_ideal_2=dados["elemento_de_uniao_ideal_2"],
            elemento_de_uniao_ideal_3=dados["elemento_de_uniao_ideal_3"],
            elemento_de_uniao_ideal_4=dados["elemento_de_uniao_ideal_4"],

            enfase_estrategica_atual_1=dados["enfase_estrategica_atual_1"],
            enfase_estrategica_atual_2=dados["enfase_estrategica_atual_2"],
            enfase_estrategica_atual_3=dados["enfase_estrategica_atual_3"],
            enfase_estrategica_atual_4=dados["enfase_estrategica_atual_4"],
            enfase_estrategica_ideal_1=dados["enfase_estrategica_ideal_1"],
            enfase_estrategica_ideal_2=dados["enfase_estrategica_ideal_2"],
            enfase_estrategica_ideal_3=dados["enfase_estrategica_ideal_3"],
            enfase_estrategica_ideal_4=dados["enfase_estrategica_ideal_4"],

            criterios_de_sucesso_atual_1=dados["criterios_de_sucesso_atual_1"],
            criterios_de_sucesso_atual_2=dados["criterios_de_sucesso_atual_2"],
            criterios_de_sucesso_atual_3=dados["criterios_de_sucesso_atual_3"],
            criterios_de_sucesso_atual_4=dados["criterios_de_sucesso_atual_4"],
            criterios_de_sucesso_ideal_1=dados["criterios_de_sucesso_ideal_1"],
            criterios_de_sucesso_ideal_2=dados["criterios_de_sucesso_ideal_2"],
            criterios_de_sucesso_ideal_3=dados["criterios_de_sucesso_ideal_3"],
            criterios_de_sucesso_ideal_4=dados["criterios_de_sucesso_ideal_4"],
        )

        db.session.add(resposta)
        db.session.flush()

        resposta.identificador = f"R{resposta.id}"

        db.session.commit()

        session.pop("consentimento_aceito", None)

        resposta_http = make_response(
            render_template("sucesso.html", identificador=resposta.identificador)
        )

        resposta_http.set_cookie(
            COOKIE_NAME,
            token,
            max_age=60 * 60 * 24 * 365,
            httponly=True,
            secure=cookie_deve_ser_secure(),
            samesite="Lax"
        )

        return resposta_http

    return render_template(
        "pesquisa.html",
        form_instructions=FORM_INSTRUCTIONS,
        dimensions=DIMENSIONS
    )


@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    """
    Login simples do administrador.
    """
    if request.method == "POST":
        senha = request.form.get("senha", "").strip()

        if senha == app.config["ADMIN_PASSWORD"]:
            session.permanent = False
            session["admin_logado"] = True
            flash("Login administrativo realizado com sucesso.", "sucesso")
            return redirect(url_for("admin_painel"))

        flash("Senha de administrador incorreta.", "erro")

    return render_template("admin_login.html")


@app.route("/admin/logout")
def admin_logout():
    """
    Encerra a sessão do administrador.
    """
    session.pop("admin_logado", None)
    flash("Logout administrativo realizado com sucesso.", "sucesso")
    return redirect(url_for("admin_login"))


@app.route("/admin/logout-beacon", methods=["POST"])
def admin_logout_beacon():
    """
    Logout silencioso para ser chamado automaticamente
    quando a guia/janela for fechada.
    """
    session.pop("admin_logado", None)
    return ("", 204)


@app.route("/admin", methods=["GET", "POST"])
@admin_required
def admin_painel():
    """
    Painel do administrador com resumo e cadastro de empresas/pesquisas.
    """
    if request.method == "POST":
        nome = request.form.get("nome_empresa", "").strip()
        data_inicio_str = request.form.get("data_inicio", "").strip()
        data_fim_str = request.form.get("data_fim", "").strip()

        if not nome or not data_inicio_str or not data_fim_str:
            flash("Preencha nome da empresa, data de início e data de encerramento.", "erro")
            return redirect(url_for("admin_painel"))

        try:
            data_inicio = datetime.strptime(data_inicio_str, "%Y-%m-%d").date()
            data_fim = datetime.strptime(data_fim_str, "%Y-%m-%d").date()
        except ValueError:
            flash("As datas informadas são inválidas.", "erro")
            return redirect(url_for("admin_painel"))

        data_cadastro = date.today()

        if data_inicio < data_cadastro:
            flash("A data de início da pesquisa não pode ser anterior à data do cadastro.", "erro")
            return redirect(url_for("admin_painel"))

        if data_fim < data_inicio:
            flash("A data de encerramento não pode ser menor que a data de início.", "erro")
            return redirect(url_for("admin_painel"))

        nome_normalizado = normalizar_nome_empresa(nome)

        empresas_mesmo_nome = Empresa.query.filter(
            func.lower(Empresa.nome) == nome_normalizado
        ).order_by(Empresa.data_inicio.asc()).all()

        for empresa_existente in empresas_mesmo_nome:
            nome_existente_normalizado = normalizar_nome_empresa(empresa_existente.nome)

            if nome_existente_normalizado == nome_normalizado and empresa_existente.data_inicio == data_inicio:
                empresa_existente.data_fim = data_fim
                db.session.commit()

                flash(
                    f"Empresa já cadastrada com esta data de início. A data de encerramento foi atualizada e o código {empresa_existente.codigo} foi mantido.",
                    "sucesso"
                )
                return redirect(url_for("admin_painel"))

        for empresa_existente in empresas_mesmo_nome:
            nome_existente_normalizado = normalizar_nome_empresa(empresa_existente.nome)

            if nome_existente_normalizado == nome_normalizado:
                if empresa_existente.data_inicio <= data_inicio <= empresa_existente.data_fim:
                    flash(
                        "Já existe uma pesquisa cadastrada para esta empresa com período que cobre a data de início informada. Cadastre uma nova pesquisa com início posterior ao encerramento da anterior.",
                        "erro"
                    )
                    return redirect(url_for("admin_painel"))

        quantidade_existente = len(empresas_mesmo_nome)
        codigo = gerar_codigo_empresa(nome, data_cadastro, quantidade_existente)

        nova_empresa = Empresa(
            nome=nome,
            codigo=codigo,
            data_inicio=data_inicio,
            data_fim=data_fim
        )

        db.session.add(nova_empresa)
        db.session.commit()

        flash(f"Empresa/pesquisa cadastrada com sucesso. Código gerado: {codigo}", "sucesso")
        return redirect(url_for("admin_painel"))

    total_respostas = 0
    empresas = []
    erro_painel = None

    try:
        # Contagem mais segura para produção:
        # conta apenas o ID, sem depender de carregar todas as colunas do modelo.
        total_respostas = db.session.query(func.count(RespostaCVF.id)).scalar() or 0
    except Exception as e:
        erro_painel = f"Erro ao contar respostas: {e}"
        print(erro_painel)

    try:
        empresas = Empresa.query.order_by(Empresa.id.desc()).all()
    except Exception as e:
        if erro_painel:
            erro_painel += f" | Erro ao buscar empresas: {e}"
        else:
            erro_painel = f"Erro ao buscar empresas: {e}"
        print(erro_painel)

    return render_template(
        "admin_painel.html",
        total_respostas=total_respostas,
        empresas=empresas,
        erro_painel=erro_painel
    )


@app.route("/admin/exportar-excel")
@admin_required
def exportar_excel():
    """
    Exporta todas as respostas para um arquivo Excel.
    """
    respostas = RespostaCVF.query.all()

    wb = Workbook()
    ws = wb.active
    ws.title = "Respostas CVF"

    colunas = ["cod_emp", "ID", "Consentimento", "Data"]

    for dimension in DIMENSIONS:
        dimension_id = dimension["id"]

        for i in range(1, 5):
            colunas.append(f"{dimension_id}_atual_{i}")

        for i in range(1, 5):
            colunas.append(f"{dimension_id}_ideal_{i}")

    ws.append(colunas)

    for resposta in respostas:
        linha = [
            resposta.cod_emp,
            resposta.id,
            resposta.consentimento,
            formatar_data_hora_brasil(resposta.data_envio)
        ]

        for dimension in DIMENSIONS:
            dimension_id = dimension["id"]

            for i in range(1, 5):
                linha.append(getattr(resposta, f"{dimension_id}_atual_{i}"))

            for i in range(1, 5):
                linha.append(getattr(resposta, f"{dimension_id}_ideal_{i}"))

        ws.append(linha)

    arquivo = BytesIO()
    wb.save(arquivo)
    arquivo.seek(0)

    return send_file(
        arquivo,
        as_attachment=True,
        download_name="respostas_cvf.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


@app.route("/criar-coluna")
def criar_coluna():
    try:
        db.session.execute(text("""
            ALTER TABLE respostas_cvf
            ADD COLUMN response_token_hash VARCHAR(64);
        """))

        db.session.execute(text("""
            CREATE UNIQUE INDEX IF NOT EXISTS ix_respostas_cvf_response_token_hash
            ON respostas_cvf (response_token_hash);
        """))

        db.session.commit()

        return "Coluna criada com sucesso!"

    except Exception as e:
        db.session.rollback()
        return f"Erro: {e}"


if __name__ == "__main__":
    app.run(debug=True)