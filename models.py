import psycopg2
from psycopg2.extras import RealDictCursor
from config import Config
from forms_data import DIMENSIONS


def get_connection():
    """
    Abre conexão com o PostgreSQL usando a DATABASE_URL do .env.
    """
    if not Config.DATABASE_URL:
        raise ValueError("DATABASE_URL não foi configurada no arquivo .env")

    return psycopg2.connect(Config.DATABASE_URL, cursor_factory=RealDictCursor)


def create_table():
    """
    Cria a tabela principal de respostas do formulário CVF.
    Se ela já existir, não apaga nada.
    """
    sql = """
    CREATE TABLE IF NOT EXISTS respostas_cvf (
        id SERIAL PRIMARY KEY,
        ordem_resposta VARCHAR(20) UNIQUE,
        data_resposta TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        consentimento VARCHAR(10) NOT NULL,

        caracteristicas_dominantes_atual_1 INTEGER NOT NULL,
        caracteristicas_dominantes_atual_2 INTEGER NOT NULL,
        caracteristicas_dominantes_atual_3 INTEGER NOT NULL,
        caracteristicas_dominantes_atual_4 INTEGER NOT NULL,
        caracteristicas_dominantes_ideal_1 INTEGER NOT NULL,
        caracteristicas_dominantes_ideal_2 INTEGER NOT NULL,
        caracteristicas_dominantes_ideal_3 INTEGER NOT NULL,
        caracteristicas_dominantes_ideal_4 INTEGER NOT NULL,

        lideranca_atual_1 INTEGER NOT NULL,
        lideranca_atual_2 INTEGER NOT NULL,
        lideranca_atual_3 INTEGER NOT NULL,
        lideranca_atual_4 INTEGER NOT NULL,
        lideranca_ideal_1 INTEGER NOT NULL,
        lideranca_ideal_2 INTEGER NOT NULL,
        lideranca_ideal_3 INTEGER NOT NULL,
        lideranca_ideal_4 INTEGER NOT NULL,

        gestao_de_pessoas_atual_1 INTEGER NOT NULL,
        gestao_de_pessoas_atual_2 INTEGER NOT NULL,
        gestao_de_pessoas_atual_3 INTEGER NOT NULL,
        gestao_de_pessoas_atual_4 INTEGER NOT NULL,
        gestao_de_pessoas_ideal_1 INTEGER NOT NULL,
        gestao_de_pessoas_ideal_2 INTEGER NOT NULL,
        gestao_de_pessoas_ideal_3 INTEGER NOT NULL,
        gestao_de_pessoas_ideal_4 INTEGER NOT NULL,

        fator_de_coesao_atual_1 INTEGER NOT NULL,
        fator_de_coesao_atual_2 INTEGER NOT NULL,
        fator_de_coesao_atual_3 INTEGER NOT NULL,
        fator_de_coesao_atual_4 INTEGER NOT NULL,
        fator_de_coesao_ideal_1 INTEGER NOT NULL,
        fator_de_coesao_ideal_2 INTEGER NOT NULL,
        fator_de_coesao_ideal_3 INTEGER NOT NULL,
        fator_de_coesao_ideal_4 INTEGER NOT NULL,

        foco_estrategico_atual_1 INTEGER NOT NULL,
        foco_estrategico_atual_2 INTEGER NOT NULL,
        foco_estrategico_atual_3 INTEGER NOT NULL,
        foco_estrategico_atual_4 INTEGER NOT NULL,
        foco_estrategico_ideal_1 INTEGER NOT NULL,
        foco_estrategico_ideal_2 INTEGER NOT NULL,
        foco_estrategico_ideal_3 INTEGER NOT NULL,
        foco_estrategico_ideal_4 INTEGER NOT NULL,

        definicao_de_sucesso_atual_1 INTEGER NOT NULL,
        definicao_de_sucesso_atual_2 INTEGER NOT NULL,
        definicao_de_sucesso_atual_3 INTEGER NOT NULL,
        definicao_de_sucesso_atual_4 INTEGER NOT NULL,
        definicao_de_sucesso_ideal_1 INTEGER NOT NULL,
        definicao_de_sucesso_ideal_2 INTEGER NOT NULL,
        definicao_de_sucesso_ideal_3 INTEGER NOT NULL,
        definicao_de_sucesso_ideal_4 INTEGER NOT NULL
    );
    """

    conn = get_connection()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(sql)
    finally:
        conn.close()


def build_resposta_data(form_data, consentimento="sim"):
    """
    Monta um dicionário com todos os campos do formulário
    no mesmo formato da tabela do banco.
    """
    resposta = {
        "consentimento": consentimento
    }

    for dimension in DIMENSIONS:
        dimension_id = dimension["id"]

        for indice in range(1, 5):
            campo_atual = f"{dimension_id}_atual_{indice}"
            campo_ideal = f"{dimension_id}_ideal_{indice}"

            resposta[campo_atual] = int(form_data.get(campo_atual, 0))
            resposta[campo_ideal] = int(form_data.get(campo_ideal, 0))

    return resposta


def insert_resposta(resposta):
    """
    Salva uma resposta na tabela respostas_cvf.
    Depois gera a ordem da resposta no formato R1, R2, R3...
    Retorna o código gerado.
    """
    sql_insert = """
    INSERT INTO respostas_cvf (
        consentimento,

        caracteristicas_dominantes_atual_1,
        caracteristicas_dominantes_atual_2,
        caracteristicas_dominantes_atual_3,
        caracteristicas_dominantes_atual_4,
        caracteristicas_dominantes_ideal_1,
        caracteristicas_dominantes_ideal_2,
        caracteristicas_dominantes_ideal_3,
        caracteristicas_dominantes_ideal_4,

        lideranca_atual_1,
        lideranca_atual_2,
        lideranca_atual_3,
        lideranca_atual_4,
        lideranca_ideal_1,
        lideranca_ideal_2,
        lideranca_ideal_3,
        lideranca_ideal_4,

        gestao_de_pessoas_atual_1,
        gestao_de_pessoas_atual_2,
        gestao_de_pessoas_atual_3,
        gestao_de_pessoas_atual_4,
        gestao_de_pessoas_ideal_1,
        gestao_de_pessoas_ideal_2,
        gestao_de_pessoas_ideal_3,
        gestao_de_pessoas_ideal_4,

        fator_de_coesao_atual_1,
        fator_de_coesao_atual_2,
        fator_de_coesao_atual_3,
        fator_de_coesao_atual_4,
        fator_de_coesao_ideal_1,
        fator_de_coesao_ideal_2,
        fator_de_coesao_ideal_3,
        fator_de_coesao_ideal_4,

        foco_estrategico_atual_1,
        foco_estrategico_atual_2,
        foco_estrategico_atual_3,
        foco_estrategico_atual_4,
        foco_estrategico_ideal_1,
        foco_estrategico_ideal_2,
        foco_estrategico_ideal_3,
        foco_estrategico_ideal_4,

        definicao_de_sucesso_atual_1,
        definicao_de_sucesso_atual_2,
        definicao_de_sucesso_atual_3,
        definicao_de_sucesso_atual_4,
        definicao_de_sucesso_ideal_1,
        definicao_de_sucesso_ideal_2,
        definicao_de_sucesso_ideal_3,
        definicao_de_sucesso_ideal_4
    )
    VALUES (
        %(consentimento)s,

        %(caracteristicas_dominantes_atual_1)s,
        %(caracteristicas_dominantes_atual_2)s,
        %(caracteristicas_dominantes_atual_3)s,
        %(caracteristicas_dominantes_atual_4)s,
        %(caracteristicas_dominantes_ideal_1)s,
        %(caracteristicas_dominantes_ideal_2)s,
        %(caracteristicas_dominantes_ideal_3)s,
        %(caracteristicas_dominantes_ideal_4)s,

        %(lideranca_atual_1)s,
        %(lideranca_atual_2)s,
        %(lideranca_atual_3)s,
        %(lideranca_atual_4)s,
        %(lideranca_ideal_1)s,
        %(lideranca_ideal_2)s,
        %(lideranca_ideal_3)s,
        %(lideranca_ideal_4)s,

        %(gestao_de_pessoas_atual_1)s,
        %(gestao_de_pessoas_atual_2)s,
        %(gestao_de_pessoas_atual_3)s,
        %(gestao_de_pessoas_atual_4)s,
        %(gestao_de_pessoas_ideal_1)s,
        %(gestao_de_pessoas_ideal_2)s,
        %(gestao_de_pessoas_ideal_3)s,
        %(gestao_de_pessoas_ideal_4)s,

        %(fator_de_coesao_atual_1)s,
        %(fator_de_coesao_atual_2)s,
        %(fator_de_coesao_atual_3)s,
        %(fator_de_coesao_atual_4)s,
        %(fator_de_coesao_ideal_1)s,
        %(fator_de_coesao_ideal_2)s,
        %(fator_de_coesao_ideal_3)s,
        %(fator_de_coesao_ideal_4)s,

        %(foco_estrategico_atual_1)s,
        %(foco_estrategico_atual_2)s,
        %(foco_estrategico_atual_3)s,
        %(foco_estrategico_atual_4)s,
        %(foco_estrategico_ideal_1)s,
        %(foco_estrategico_ideal_2)s,
        %(foco_estrategico_ideal_3)s,
        %(foco_estrategico_ideal_4)s,

        %(definicao_de_sucesso_atual_1)s,
        %(definicao_de_sucesso_atual_2)s,
        %(definicao_de_sucesso_atual_3)s,
        %(definicao_de_sucesso_atual_4)s,
        %(definicao_de_sucesso_ideal_1)s,
        %(definicao_de_sucesso_ideal_2)s,
        %(definicao_de_sucesso_ideal_3)s,
        %(definicao_de_sucesso_ideal_4)s
    )
    RETURNING id;
    """

    sql_update_ordem = """
    UPDATE respostas_cvf
    SET ordem_resposta = %s
    WHERE id = %s;
    """

    conn = get_connection()

    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(sql_insert, resposta)
                novo_id = cur.fetchone()["id"]

                ordem_resposta = f"R{novo_id}"

                cur.execute(sql_update_ordem, (ordem_resposta, novo_id))

                return ordem_resposta
    finally:
        conn.close()