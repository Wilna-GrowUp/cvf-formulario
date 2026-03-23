# cvf_utils.py

from statistics import mean

# Perfis do CVF
PERFIS = ["cla", "adocracia", "mercado", "hierarquia"]

# Cada grupo do formulário possui 4 alternativas.
# Neste projeto vamos assumir:
# A = Clã
# B = Adocracia
# C = Mercado
# D = Hierarquia
MAPEAMENTO_ALTERNATIVAS = {
    "a": "cla",
    "b": "adocracia",
    "c": "mercado",
    "d": "hierarquia",
}


def normalizar_grupo(grupo):
    """
    Garante que o grupo tenha sempre as chaves:
    a, b, c, d

    Exemplo de entrada:
    {"a": 25, "b": 25, "c": 25, "d": 25}
    """
    grupo_normalizado = {}

    for alternativa in ["a", "b", "c", "d"]:
        valor = grupo.get(alternativa, 0)

        try:
            grupo_normalizado[alternativa] = float(valor)
        except (TypeError, ValueError):
            raise ValueError(
                f"Valor inválido na alternativa '{alternativa}'. "
                f"Recebido: {valor}"
            )

    return grupo_normalizado


def validar_soma_100(grupo):
    """
    Verifica se a soma das 4 alternativas é exatamente 100.
    """
    grupo = normalizar_grupo(grupo)
    soma = grupo["a"] + grupo["b"] + grupo["c"] + grupo["d"]
    return round(soma, 2) == 100.0


def validar_todos_os_grupos(grupos):
    """
    Recebe uma lista de grupos e retorna:
    - True/False
    - lista com mensagens de erro
    """
    erros = []

    for i, grupo in enumerate(grupos, start=1):
        grupo_normalizado = normalizar_grupo(grupo)
        soma = (
            grupo_normalizado["a"]
            + grupo_normalizado["b"]
            + grupo_normalizado["c"]
            + grupo_normalizado["d"]
        )

        if round(soma, 2) != 100.0:
            erros.append(
                f"Grupo {i} está com soma {soma}. A soma deve ser 100."
            )

    return len(erros) == 0, erros


def calcular_perfis_por_cenario(grupos):
    """
    Recebe uma lista de grupos de um cenário (Atual ou Ideal).

    Cada grupo deve ser assim:
    {"a": 25, "b": 25, "c": 25, "d": 25}

    Retorna as médias por perfil.
    """
    if not grupos:
        return {
            "cla": 0,
            "adocracia": 0,
            "mercado": 0,
            "hierarquia": 0,
        }

    valido, erros = validar_todos_os_grupos(grupos)
    if not valido:
        raise ValueError("Erros na validação dos grupos: " + " | ".join(erros))

    acumulado = {
        "cla": [],
        "adocracia": [],
        "mercado": [],
        "hierarquia": [],
    }

    for grupo in grupos:
        grupo_normalizado = normalizar_grupo(grupo)

        for alternativa, perfil in MAPEAMENTO_ALTERNATIVAS.items():
            acumulado[perfil].append(grupo_normalizado[alternativa])

    resultado = {}
    for perfil in PERFIS:
        resultado[perfil] = round(mean(acumulado[perfil]), 2)

    return resultado


def calcular_resultado_cvf(grupos_atual, grupos_ideal):
    """
    Recebe:
    - grupos_atual: lista com 6 grupos do cenário atual
    - grupos_ideal: lista com 6 grupos do cenário ideal

    Retorna um dicionário completo com os resultados.
    """
    resultado_atual = calcular_perfis_por_cenario(grupos_atual)
    resultado_ideal = calcular_perfis_por_cenario(grupos_ideal)

    return {
        "atual": resultado_atual,
        "ideal": resultado_ideal,
    }


def montar_grupos_a_partir_de_dict(dados, prefixo):
    """
    Monta os 6 grupos a partir de um dicionário simples.

    Este formato espera chaves como:

    atual_1_a, atual_1_b, atual_1_c, atual_1_d
    atual_2_a, atual_2_b, atual_2_c, atual_2_d
    ...
    atual_6_a, atual_6_b, atual_6_c, atual_6_d

    ou

    ideal_1_a, ideal_1_b, ideal_1_c, ideal_1_d
    ...
    ideal_6_d
    """
    grupos = []

    for numero_grupo in range(1, 7):
        grupo = {
            "a": dados.get(f"{prefixo}_{numero_grupo}_a", 0),
            "b": dados.get(f"{prefixo}_{numero_grupo}_b", 0),
            "c": dados.get(f"{prefixo}_{numero_grupo}_c", 0),
            "d": dados.get(f"{prefixo}_{numero_grupo}_d", 0),
        }
        grupos.append(normalizar_grupo(grupo))

    return grupos