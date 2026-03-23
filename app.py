from functools import wraps
from io import BytesIO
import secrets
import hashlib

from datetime import datetime, date, timezone
from flask import Flask, render_template, request, redirect, url_for, flash, session, send_file, make_response
from openpyxl import Workbook
from sqlalchemy import func, text, inspect
from zoneinfo import ZoneInfo

from config import Config
from models import db, RespostaCVF, Empresa, Admin
from forms_data import FORM_INSTRUCTIONS, DIMENSIONS
from cvf_utils import calcular_resultado_cvf, montar_grupos_a_partir_de_dict


app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)


def garantir_admin_inicial():
    """
    Cria o primeiro administrador, se ainda não existir.
    """
    username = app.config["ADMIN_USERNAME"]
    senha_inicial = app.config["ADMIN_PASSWORD_INICIAL"]

    admin = Admin.query.filter_by(username=username).first()

    if not admin:
        admin = Admin(username=username)
        admin.set_password(senha_inicial)
        db.session.add(admin)
        db.session.commit()
        print(f"Admin inicial criado com usuário: {username}")
    else:
        print(f"Admin já existe: {username}")


def garantir_colunas_producao():
    """
    Garante que colunas novas existentes no código também existam
    no banco de produção.
    """
    inspector = inspect(db.engine)
    colunas = [col["name"] for col in inspector.get_columns("respostas_cvf")]

    comandos = []

    if "cod_emp" not in colunas:
        comandos.append("ALTER TABLE respostas_cvf ADD COLUMN cod_emp VARCHAR(50)")

    if "response_token_hash" not in colunas:
        comandos.append("ALTER TABLE respostas_cvf ADD COLUMN response_token_hash VARCHAR(255)")

    for sql in comandos:
        db.session.execute(text(sql))

    if comandos:
        db.session.commit()
        print("Banco atualizado com sucesso. Colunas adicionadas:", comandos)
    else:
        print("Banco já está atualizado. Nenhuma coluna nova foi necessária.")


with app.app_context():
    db.create_all()
    garantir_colunas_producao()
    garantir_admin_inicial()

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

    Aceita:
    - datetime do Python
    - string em formato de data/hora
    """
    if not data_utc:
        return None

    if isinstance(data_utc, str):
        texto = data_utc.strip()

        try:
            data_utc = datetime.fromisoformat(texto)
        except ValueError:
            try:
                if texto.endswith("Z"):
                    texto = texto.replace("Z", "+00:00")
                    data_utc = datetime.fromisoformat(texto)
                else:
                    return None
            except ValueError:
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
        return str(data_utc) if data_utc else ""

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


def admin_logado():
    """
    Retorna True se existe um admin logado na sessão.
    """
    return "admin_id" in session


def resposta_para_dict(resposta):
    """
    Converte um objeto RespostaCVF em dicionário simples,
    no formato esperado pelo cvf_utils.py.

    Saída esperada:
    atual_1_a, atual_1_b, atual_1_c, atual_1_d
    ...
    atual_6_d
    ideal_1_a ... ideal_6_d
    """
    dados = {}

    mapeamento_dimensoes = [
        ("caracteristicas_dominantes", 1),
        ("lideranca_organizacional", 2),
        ("gestao_de_pessoas", 3),
        ("elemento_de_uniao", 4),
        ("enfase_estrategica", 5),
        ("criterios_de_sucesso", 6),
    ]

    mapeamento_alternativas = {
        1: "a",
        2: "b",
        3: "c",
        4: "d",
    }

    for nome_dimensao, numero_grupo in mapeamento_dimensoes:
        for numero_alternativa, letra_alternativa in mapeamento_alternativas.items():
            campo_model_atual = f"{nome_dimensao}_atual_{numero_alternativa}"
            campo_model_ideal = f"{nome_dimensao}_ideal_{numero_alternativa}"

            campo_saida_atual = f"atual_{numero_grupo}_{letra_alternativa}"
            campo_saida_ideal = f"ideal_{numero_grupo}_{letra_alternativa}"

            dados[campo_saida_atual] = getattr(resposta, campo_model_atual, 0)
            dados[campo_saida_ideal] = getattr(resposta, campo_model_ideal, 0)

    return dados


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
    Login do administrador com usuário e senha.
    """
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        senha = request.form.get("password", "")

        admin = Admin.query.filter_by(username=username).first()

        if admin and admin.check_password(senha):
            session.permanent = False
            session["admin_logado"] = True
            session["admin_id"] = admin.id
            session["admin_username"] = admin.username
            flash("Login administrativo realizado com sucesso.", "sucesso")
            return redirect(url_for("admin_painel"))

        flash("Usuário ou senha inválidos.", "erro")

    return render_template("admin_login.html")


@app.route("/admin/esqueci-senha", methods=["GET", "POST"])
def admin_esqueci_senha():
    """
    Permite redefinir a senha do administrador usando um código secreto.
    """
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        reset_code = request.form.get("reset_code", "").strip()
        nova_senha = request.form.get("nova_senha", "")
        confirmar_senha = request.form.get("confirmar_senha", "")

        admin = Admin.query.filter_by(username=username).first()

        if not admin:
            flash("Usuário administrador não encontrado.", "erro")
            return render_template("admin_esqueci_senha.html")

        if reset_code != app.config["ADMIN_RESET_CODE"]:
            flash("Código de recuperação inválido.", "erro")
            return render_template("admin_esqueci_senha.html")

        if len(nova_senha) < 6:
            flash("A nova senha deve ter pelo menos 6 caracteres.", "erro")
            return render_template("admin_esqueci_senha.html")

        if nova_senha != confirmar_senha:
            flash("A confirmação da senha não confere.", "erro")
            return render_template("admin_esqueci_senha.html")

        admin.set_password(nova_senha)
        db.session.commit()

        flash("Senha redefinida com sucesso. Faça login com a nova senha.", "sucesso")
        return redirect(url_for("admin_login"))

    return render_template("admin_esqueci_senha.html")


@app.route("/admin/alterar-senha", methods=["GET", "POST"])
@admin_required
def admin_alterar_senha():
    """
    Permite ao administrador logado alterar a própria senha.
    """
    admin_id = session.get("admin_id")
    admin = Admin.query.get(admin_id)

    if not admin:
        flash("Administrador não encontrado.", "erro")
        return redirect(url_for("admin_login"))

    if request.method == "POST":
        senha_atual = request.form.get("senha_atual", "")
        nova_senha = request.form.get("nova_senha", "")
        confirmar_senha = request.form.get("confirmar_senha", "")

        if not admin.check_password(senha_atual):
            flash("A senha atual está incorreta.", "erro")
            return render_template("admin_alterar_senha.html")

        if len(nova_senha) < 6:
            flash("A nova senha deve ter pelo menos 6 caracteres.", "erro")
            return render_template("admin_alterar_senha.html")

        if nova_senha != confirmar_senha:
            flash("A confirmação da nova senha não confere.", "erro")
            return render_template("admin_alterar_senha.html")

        admin.set_password(nova_senha)
        db.session.commit()

        flash("Senha alterada com sucesso.", "sucesso")
        return redirect(url_for("admin_painel"))

    return render_template("admin_alterar_senha.html")


@app.route("/admin/logout")
def admin_logout():
    """
    Encerra a sessão do administrador.
    """
    session.pop("admin_logado", None)
    session.pop("admin_id", None)
    session.pop("admin_username", None)
    flash("Logout administrativo realizado com sucesso.", "sucesso")
    return redirect(url_for("admin_login"))


@app.route("/admin/logout-beacon", methods=["POST"])
def admin_logout_beacon():
    """
    Logout silencioso para ser chamado automaticamente
    quando a guia/janela for fechada.
    """
    session.pop("admin_logado", None)
    session.pop("admin_id", None)
    session.pop("admin_username", None)
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


@app.route("/admin/dashboard")
@admin_required
def admin_dashboard():
    """
    Dashboard administrativo com médias gerais do CVF
    e filtro opcional por empresa.
    """
    codigo_empresa = request.args.get("cod_emp", "").strip()

    empresas = Empresa.query.order_by(Empresa.nome.asc()).all()

    query_respostas = RespostaCVF.query

    empresa_selecionada = None

    if codigo_empresa:
        query_respostas = query_respostas.filter(RespostaCVF.cod_emp == codigo_empresa)
        empresa_selecionada = Empresa.query.filter_by(codigo=codigo_empresa).first()

    respostas = query_respostas.all()

    if not respostas:
        return render_template(
            "admin_dashboard.html",
            total_respostas=0,
            medias_atual={
                "cla": 0,
                "adocracia": 0,
                "mercado": 0,
                "hierarquia": 0,
            },
            medias_ideal={
                "cla": 0,
                "adocracia": 0,
                "mercado": 0,
                "hierarquia": 0,
            },
            empresas=empresas,
            codigo_empresa_selecionado=codigo_empresa,
            empresa_selecionada=empresa_selecionada,
        )

    lista_resultados = []

    for resposta in respostas:
        dados = resposta_para_dict(resposta)

        grupos_atual = montar_grupos_a_partir_de_dict(dados, "atual")
        grupos_ideal = montar_grupos_a_partir_de_dict(dados, "ideal")

        resultado = calcular_resultado_cvf(grupos_atual, grupos_ideal)
        lista_resultados.append(resultado)

    total = len(lista_resultados)

    medias_atual = {
        "cla": round(sum(r["atual"]["cla"] for r in lista_resultados) / total, 2),
        "adocracia": round(sum(r["atual"]["adocracia"] for r in lista_resultados) / total, 2),
        "mercado": round(sum(r["atual"]["mercado"] for r in lista_resultados) / total, 2),
        "hierarquia": round(sum(r["atual"]["hierarquia"] for r in lista_resultados) / total, 2),
    }

    medias_ideal = {
        "cla": round(sum(r["ideal"]["cla"] for r in lista_resultados) / total, 2),
        "adocracia": round(sum(r["ideal"]["adocracia"] for r in lista_resultados) / total, 2),
        "mercado": round(sum(r["ideal"]["mercado"] for r in lista_resultados) / total, 2),
        "hierarquia": round(sum(r["ideal"]["hierarquia"] for r in lista_resultados) / total, 2),
    }

    return render_template(
        "admin_dashboard.html",
        total_respostas=total,
        medias_atual=medias_atual,
        medias_ideal=medias_ideal,
        empresas=empresas,
        codigo_empresa_selecionado=codigo_empresa,
        empresa_selecionada=empresa_selecionada,
    )


@app.route("/admin/exportar-excel")
@admin_required
def exportar_excel():
    """
    Exporta todas as respostas para um arquivo Excel.
    Usa SQL direto para ler a estrutura real do banco em produção,
    evitando erro por diferença entre o modelo Python e a tabela.
    """
    try:
        resultado = db.session.execute(
            text("SELECT * FROM respostas_cvf ORDER BY id")
        )

        linhas = resultado.mappings().all()

        wb = Workbook()
        ws = wb.active
        ws.title = "Respostas CVF"

        if not linhas:
            ws.append(["Mensagem"])
            ws.append(["Nenhuma resposta encontrada para exportação."])
        else:
            colunas = list(linhas[0].keys())
            ws.append(colunas)

            for linha_dict in linhas:
                linha_excel = []

                for coluna in colunas:
                    valor = linha_dict.get(coluna)

                    if coluna == "data_envio" and valor:
                        valor = formatar_data_hora_brasil(valor)

                    linha_excel.append(valor)

                ws.append(linha_excel)

        arquivo = BytesIO()
        wb.save(arquivo)
        arquivo.seek(0)

        return send_file(
            arquivo,
            as_attachment=True,
            download_name="respostas_cvf.xlsx",
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    except Exception as e:
        print(f"Erro ao exportar Excel: {e}")
        flash(f"Erro ao exportar Excel: {e}", "erro")
        return redirect(url_for("admin_painel"))


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