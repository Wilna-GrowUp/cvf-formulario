document.addEventListener("DOMContentLoaded", function () {
    const formulario = document.getElementById("form-pesquisa");
    const grupos = document.querySelectorAll(".grupo-dimensao");
    const erroGeral = document.getElementById("erro-geral-formulario");
    const mensagemResumo = document.getElementById("mensagem-resumo-erros");
    const botaoEnviar = document.getElementById("botao-enviar");

    if (!formulario || grupos.length === 0) {
        return;
    }

    function converterParaNumero(valor) {
        if (valor === "" || valor === null) {
            return 0;
        }

        const numero = parseInt(valor, 10);

        if (isNaN(numero) || numero < 0) {
            return 0;
        }

        return numero;
    }

    function atualizarGrupo(grupo) {
        const camposAtual = grupo.querySelectorAll(".campo-atual");
        const camposIdeal = grupo.querySelectorAll(".campo-ideal");

        let somaAtual = 0;
        let somaIdeal = 0;

        camposAtual.forEach(function (campo) {
            somaAtual += converterParaNumero(campo.value);
        });

        camposIdeal.forEach(function (campo) {
            somaIdeal += converterParaNumero(campo.value);
        });

        const valorSomaAtual = grupo.querySelector(".valor-soma-atual");
        const valorSomaIdeal = grupo.querySelector(".valor-soma-ideal");
        const statusSomaAtual = grupo.querySelector(".status-soma-atual");
        const statusSomaIdeal = grupo.querySelector(".status-soma-ideal");
        const erroDimensao = grupo.querySelector(".erro-dimensao");

        valorSomaAtual.textContent = somaAtual;
        valorSomaIdeal.textContent = somaIdeal;

        const atualCorreto = somaAtual === 100;
        const idealCorreto = somaIdeal === 100;

        if (atualCorreto) {
            statusSomaAtual.textContent = "✅ Correto";
            statusSomaAtual.classList.remove("soma-erro");
            statusSomaAtual.classList.add("soma-ok");
        } else {
            statusSomaAtual.textContent = "❌ Deve ser 100";
            statusSomaAtual.classList.remove("soma-ok");
            statusSomaAtual.classList.add("soma-erro");
        }

        if (idealCorreto) {
            statusSomaIdeal.textContent = "✅ Correto";
            statusSomaIdeal.classList.remove("soma-erro");
            statusSomaIdeal.classList.add("soma-ok");
        } else {
            statusSomaIdeal.textContent = "❌ Deve ser 100";
            statusSomaIdeal.classList.remove("soma-ok");
            statusSomaIdeal.classList.add("soma-erro");
        }

        if (atualCorreto && idealCorreto) {
            erroDimensao.textContent = "";
            grupo.style.borderColor = "#d9dee5";
            return true;
        }

        let mensagemErro = "Corrija esta dimensão: ";

        if (!atualCorreto && !idealCorreto) {
            mensagemErro += "a soma do cenário atual e a soma do cenário ideal devem ser 100.";
        } else if (!atualCorreto) {
            mensagemErro += "a soma do cenário atual deve ser 100.";
        } else {
            mensagemErro += "a soma do cenário ideal deve ser 100.";
        }

        erroDimensao.textContent = mensagemErro;
        grupo.style.borderColor = "#f1b5b5";

        return false;
    }

    function validarFormulario() {
        let formularioValido = true;
        let dimensoesComErro = [];

        grupos.forEach(function (grupo) {
            const grupoValido = atualizarGrupo(grupo);

            if (!grupoValido) {
                formularioValido = false;

                const titulo = grupo.querySelector("h2").textContent.trim();
                dimensoesComErro.push(titulo);
            }
        });

        if (formularioValido) {
            erroGeral.style.display = "none";
            mensagemResumo.style.display = "none";
            mensagemResumo.textContent = "";
            botaoEnviar.disabled = false;
        } else {
            erroGeral.style.display = "block";
            botaoEnviar.disabled = true;

            if (dimensoesComErro.length === 1) {
                mensagemResumo.textContent =
                    "Revise a soma da pontuação na dimensão: " + dimensoesComErro[0];
            } else {
                mensagemResumo.textContent =
                    "Revise a soma da pontuação nas dimensões: " + dimensoesComErro.join(", ");
            }

            mensagemResumo.style.display = "block";
        }

        return formularioValido;
    }

    grupos.forEach(function (grupo) {
        const campos = grupo.querySelectorAll("input[type='number']");

        campos.forEach(function (campo) {
            campo.addEventListener("input", function () {
                validarFormulario();
            });
        });
    });

    formulario.addEventListener("submit", function (evento) {
        const formularioValido = validarFormulario();

        if (!formularioValido) {
            evento.preventDefault();
            mensagemResumo.scrollIntoView({
                behavior: "smooth",
                block: "center"
            });
        }
    });

    validarFormulario();
});