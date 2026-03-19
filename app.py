from flask import Flask, render_template, request, redirect, url_for, flash
from config import Config
from models import db, RespostaCVF


app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)


with app.app_context():
    db.create_all()


def converter_para_int(nome_campo):
    """
    Lê um campo do formulário e tenta converter para inteiro.
    Se vier vazio ou inválido, retorna 0.
    """
    valor = request.form.get(nome_campo, "").strip()

    if valor == "":
        return 0

    try:
        return int(valor)
    except ValueError:
        return 0


def validar_grupos(dados):
    """
    Valida se cada grupo de 4 campos soma exatamente 100.
    Retorna uma lista com os grupos com erro.
    """
    grupos_com_erro = []

    for cenario in ["atual", "ideal"]:
        for dimensao in range(1, 7):
            soma = (
                dados[f"{cenario}_d{dimensao}_a"] +
                dados[f"{cenario}_d{dimensao}_b"] +
                dados[f"{cenario}_d{dimensao}_c"] +
                dados[f"{cenario}_d{dimensao}_d"]
            )

            if soma != 100:
                grupos_com_erro.append(f"{cenario.capitalize()} - Dimensão {dimensao}")

    return grupos_com_erro


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/formulario")
def formulario():
    return render_template("formulario.html")


@app.route("/enviar", methods=["POST"])
def enviar():
    # Consentimento
    consentimento_valor = request.form.get("consentimento", "").strip().lower()
    consentimento = consentimento_valor == "sim"

    if not consentimento:
        flash("Você precisa aceitar o termo de consentimento para enviar a pesquisa.", "erro")
        return redirect(url_for("formulario"))

    # Coleta dos 48 campos
    dados = {}

    for cenario in ["atual", "ideal"]:
        for dimensao in range(1, 7):
            for alternativa in ["a", "b", "c", "d"]:
                nome_campo = f"{cenario}_d{dimensao}_{alternativa}"
                dados[nome_campo] = converter_para_int(nome_campo)

    # Validação backend da soma 100
    grupos_com_erro = validar_grupos(dados)

    if grupos_com_erro:
        mensagem = "Os grupos abaixo precisam somar exatamente 100: " + ", ".join(grupos_com_erro)
        flash(mensagem, "erro")
        return redirect(url_for("formulario"))

    # Cria o objeto da resposta
    resposta = RespostaCVF(
        consentimento=consentimento,

        atual_d1_a=dados["atual_d1_a"],
        atual_d1_b=dados["atual_d1_b"],
        atual_d1_c=dados["atual_d1_c"],
        atual_d1_d=dados["atual_d1_d"],

        atual_d2_a=dados["atual_d2_a"],
        atual_d2_b=dados["atual_d2_b"],
        atual_d2_c=dados["atual_d2_c"],
        atual_d2_d=dados["atual_d2_d"],

        atual_d3_a=dados["atual_d3_a"],
        atual_d3_b=dados["atual_d3_b"],
        atual_d3_c=dados["atual_d3_c"],
        atual_d3_d=dados["atual_d3_d"],

        atual_d4_a=dados["atual_d4_a"],
        atual_d4_b=dados["atual_d4_b"],
        atual_d4_c=dados["atual_d4_c"],
        atual_d4_d=dados["atual_d4_d"],

        atual_d5_a=dados["atual_d5_a"],
        atual_d5_b=dados["atual_d5_b"],
        atual_d5_c=dados["atual_d5_c"],
        atual_d5_d=dados["atual_d5_d"],

        atual_d6_a=dados["atual_d6_a"],
        atual_d6_b=dados["atual_d6_b"],
        atual_d6_c=dados["atual_d6_c"],
        atual_d6_d=dados["atual_d6_d"],

        ideal_d1_a=dados["ideal_d1_a"],
        ideal_d1_b=dados["ideal_d1_b"],
        ideal_d1_c=dados["ideal_d1_c"],
        ideal_d1_d=dados["ideal_d1_d"],

        ideal_d2_a=dados["ideal_d2_a"],
        ideal_d2_b=dados["ideal_d2_b"],
        ideal_d2_c=dados["ideal_d2_c"],
        ideal_d2_d=dados["ideal_d2_d"],

        ideal_d3_a=dados["ideal_d3_a"],
        ideal_d3_b=dados["ideal_d3_b"],
        ideal_d3_c=dados["ideal_d3_c"],
        ideal_d3_d=dados["ideal_d3_d"],

        ideal_d4_a=dados["ideal_d4_a"],
        ideal_d4_b=dados["ideal_d4_b"],
        ideal_d4_c=dados["ideal_d4_c"],
        ideal_d4_d=dados["ideal_d4_d"],

        ideal_d5_a=dados["ideal_d5_a"],
        ideal_d5_b=dados["ideal_d5_b"],
        ideal_d5_c=dados["ideal_d5_c"],
        ideal_d5_d=dados["ideal_d5_d"],

        ideal_d6_a=dados["ideal_d6_a"],
        ideal_d6_b=dados["ideal_d6_b"],
        ideal_d6_c=dados["ideal_d6_c"],
        ideal_d6_d=dados["ideal_d6_d"],
    )

    # Salva primeiro para gerar o ID
    db.session.add(resposta)
    db.session.flush()

    # Gera identificador do tipo R1, R2, R3...
    resposta.identificador = f"R{resposta.id}"

    db.session.commit()

    return render_template("sucesso.html", identificador=resposta.identificador)


if __name__ == "__main__":
    app.run(debug=True)
    app.run(debug=True)
