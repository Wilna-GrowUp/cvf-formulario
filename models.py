from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class RespostaCVF(db.Model):
    __tablename__ = "respostas_cvf"

    id = db.Column(db.Integer, primary_key=True)
    identificador = db.Column(db.String(20), unique=True, nullable=True)

    consentimento = db.Column(db.Boolean, nullable=False, default=False)
    data_envio = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    # Características dominantes
    caracteristicas_dominantes_atual_1 = db.Column(db.Integer, nullable=False)
    caracteristicas_dominantes_atual_2 = db.Column(db.Integer, nullable=False)
    caracteristicas_dominantes_atual_3 = db.Column(db.Integer, nullable=False)
    caracteristicas_dominantes_atual_4 = db.Column(db.Integer, nullable=False)

    caracteristicas_dominantes_ideal_1 = db.Column(db.Integer, nullable=False)
    caracteristicas_dominantes_ideal_2 = db.Column(db.Integer, nullable=False)
    caracteristicas_dominantes_ideal_3 = db.Column(db.Integer, nullable=False)
    caracteristicas_dominantes_ideal_4 = db.Column(db.Integer, nullable=False)

    # Liderança organizacional
    lideranca_organizacional_atual_1 = db.Column(db.Integer, nullable=False)
    lideranca_organizacional_atual_2 = db.Column(db.Integer, nullable=False)
    lideranca_organizacional_atual_3 = db.Column(db.Integer, nullable=False)
    lideranca_organizacional_atual_4 = db.Column(db.Integer, nullable=False)

    lideranca_organizacional_ideal_1 = db.Column(db.Integer, nullable=False)
    lideranca_organizacional_ideal_2 = db.Column(db.Integer, nullable=False)
    lideranca_organizacional_ideal_3 = db.Column(db.Integer, nullable=False)
    lideranca_organizacional_ideal_4 = db.Column(db.Integer, nullable=False)

    # Gestão de pessoas
    gestao_de_pessoas_atual_1 = db.Column(db.Integer, nullable=False)
    gestao_de_pessoas_atual_2 = db.Column(db.Integer, nullable=False)
    gestao_de_pessoas_atual_3 = db.Column(db.Integer, nullable=False)
    gestao_de_pessoas_atual_4 = db.Column(db.Integer, nullable=False)

    gestao_de_pessoas_ideal_1 = db.Column(db.Integer, nullable=False)
    gestao_de_pessoas_ideal_2 = db.Column(db.Integer, nullable=False)
    gestao_de_pessoas_ideal_3 = db.Column(db.Integer, nullable=False)
    gestao_de_pessoas_ideal_4 = db.Column(db.Integer, nullable=False)

    # Elemento de união organizacional
    elemento_de_uniao_atual_1 = db.Column(db.Integer, nullable=False)
    elemento_de_uniao_atual_2 = db.Column(db.Integer, nullable=False)
    elemento_de_uniao_atual_3 = db.Column(db.Integer, nullable=False)
    elemento_de_uniao_atual_4 = db.Column(db.Integer, nullable=False)

    elemento_de_uniao_ideal_1 = db.Column(db.Integer, nullable=False)
    elemento_de_uniao_ideal_2 = db.Column(db.Integer, nullable=False)
    elemento_de_uniao_ideal_3 = db.Column(db.Integer, nullable=False)
    elemento_de_uniao_ideal_4 = db.Column(db.Integer, nullable=False)

    # Ênfase estratégica
    enfase_estrategica_atual_1 = db.Column(db.Integer, nullable=False)
    enfase_estrategica_atual_2 = db.Column(db.Integer, nullable=False)
    enfase_estrategica_atual_3 = db.Column(db.Integer, nullable=False)
    enfase_estrategica_atual_4 = db.Column(db.Integer, nullable=False)

    enfase_estrategica_ideal_1 = db.Column(db.Integer, nullable=False)
    enfase_estrategica_ideal_2 = db.Column(db.Integer, nullable=False)
    enfase_estrategica_ideal_3 = db.Column(db.Integer, nullable=False)
    enfase_estrategica_ideal_4 = db.Column(db.Integer, nullable=False)

    # Critérios de sucesso
    criterios_de_sucesso_atual_1 = db.Column(db.Integer, nullable=False)
    criterios_de_sucesso_atual_2 = db.Column(db.Integer, nullable=False)
    criterios_de_sucesso_atual_3 = db.Column(db.Integer, nullable=False)
    criterios_de_sucesso_atual_4 = db.Column(db.Integer, nullable=False)

    criterios_de_sucesso_ideal_1 = db.Column(db.Integer, nullable=False)
    criterios_de_sucesso_ideal_2 = db.Column(db.Integer, nullable=False)
    criterios_de_sucesso_ideal_3 = db.Column(db.Integer, nullable=False)
    criterios_de_sucesso_ideal_4 = db.Column(db.Integer, nullable=False)

    def __repr__(self):
        return f"<RespostaCVF {self.identificador}>"
