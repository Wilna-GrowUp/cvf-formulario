from flask import Flask, render_template, request, redirect, url_for, flash
from forms_data import FORM_TITLE, FORM_DESCRIPTION, FORM_INSTRUCTIONS, DIMENSIONS

app = Flask(__name__)
app.secret_key = "chave-temporaria-desenvolvimento"


def converter_para_int(valor):
    """
    Converte o valor recebido do formulário para inteiro.
    Se vier vazio, inválido ou negativo, retorna 0.
    """
    try:
        numero = int(valor)
        if numero < 0:
            return 0
        return numero
    except (TypeError, ValueError):
        return 0


def validar_respostas_backend(form_data):
    """
    Valida se, em cada dimensão:
    - a soma do cenário atual é 100
    - a soma do cenário ideal é 100

    Retorna:
    - lista de erros
    """
    erros = []

    for dimension in DIMENSIONS:
        soma_atual = 0
        soma_ideal = 0

        for indice in range(1, 5):
            campo_atual = f"{dimension['id']}_atual_{indice}"
            campo_ideal = f"{dimension['id']}_ideal_{indice}"

            valor_atual = converter_para_int(form_data.get(campo_atual))
            valor_ideal = converter_para_int(form_data.get(campo_ideal))

            soma_atual += valor_atual
            soma_ideal += valor_ideal

        if soma_atual != 100 and soma_ideal != 100:
            erros.append(
                f"{dimension['title']}: a soma do cenário atual e a soma do cenário ideal devem ser 100."
            )
        elif soma_atual != 100:
            erros.append(
                f"{dimension['title']}: a soma do cenário atual deve ser 100."
            )
        elif soma_ideal != 100:
            erros.append(
                f"{dimension['title']}: a soma do cenário ideal deve ser 100."
            )

    return erros


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        consentimento = request.form.get("consentimento")

        if consentimento != "sim":
            flash("Você precisa aceitar o termo de consentimento para iniciar a pesquisa.")
            return redirect(url_for("index"))

        return redirect(url_for("pesquisa"))

    return render_template(
        "index.html",
        form_title=FORM_TITLE,
        form_description=FORM_DESCRIPTION,
    )


@app.route("/pesquisa", methods=["GET", "POST"])
def pesquisa():
    if request.method == "POST":
        erros_validacao = validar_respostas_backend(request.form)

        if erros_validacao:
            for erro in erros_validacao:
                flash(erro)

            return render_template(
                "pesquisa.html",
                form_title=FORM_TITLE,
                form_instructions=FORM_INSTRUCTIONS,
                dimensions=DIMENSIONS,
            )

        return redirect(url_for("sucesso"))

    return render_template(
        "pesquisa.html",
        form_title=FORM_TITLE,
        form_instructions=FORM_INSTRUCTIONS,
        dimensions=DIMENSIONS,
    )


@app.route("/sucesso")
def sucesso():
    return render_template("sucesso.html", form_title=FORM_TITLE)


if __name__ == "__main__":
    app.run(debug=True)