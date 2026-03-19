from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class RespostaCVF(db.Model):
    __tablename__ = "respostas_cvf"

    id = db.Column(db.Integer, primary_key=True)
    identificador = db.Column(db.String(20), unique=True, nullable=True)

    consentimento = db.Column(db.Boolean, nullable=False, default=False)
    data_envio = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    # CENÁRIO ATUAL - DIMENSÃO 1
    atual_d1_a = db.Column(db.Integer, nullable=False)
    atual_d1_b = db.Column(db.Integer, nullable=False)
    atual_d1_c = db.Column(db.Integer, nullable=False)
    atual_d1_d = db.Column(db.Integer, nullable=False)

    # CENÁRIO ATUAL - DIMENSÃO 2
    atual_d2_a = db.Column(db.Integer, nullable=False)
    atual_d2_b = db.Column(db.Integer, nullable=False)
    atual_d2_c = db.Column(db.Integer, nullable=False)
    atual_d2_d = db.Column(db.Integer, nullable=False)

    # CENÁRIO ATUAL - DIMENSÃO 3
    atual_d3_a = db.Column(db.Integer, nullable=False)
    atual_d3_b = db.Column(db.Integer, nullable=False)
    atual_d3_c = db.Column(db.Integer, nullable=False)
    atual_d3_d = db.Column(db.Integer, nullable=False)

    # CENÁRIO ATUAL - DIMENSÃO 4
    atual_d4_a = db.Column(db.Integer, nullable=False)
    atual_d4_b = db.Column(db.Integer, nullable=False)
    atual_d4_c = db.Column(db.Integer, nullable=False)
    atual_d4_d = db.Column(db.Integer, nullable=False)

    # CENÁRIO ATUAL - DIMENSÃO 5
    atual_d5_a = db.Column(db.Integer, nullable=False)
    atual_d5_b = db.Column(db.Integer, nullable=False)
    atual_d5_c = db.Column(db.Integer, nullable=False)
    atual_d5_d = db.Column(db.Integer, nullable=False)

    # CENÁRIO ATUAL - DIMENSÃO 6
    atual_d6_a = db.Column(db.Integer, nullable=False)
    atual_d6_b = db.Column(db.Integer, nullable=False)
    atual_d6_c = db.Column(db.Integer, nullable=False)
    atual_d6_d = db.Column(db.Integer, nullable=False)

    # CENÁRIO IDEAL - DIMENSÃO 1
    ideal_d1_a = db.Column(db.Integer, nullable=False)
    ideal_d1_b = db.Column(db.Integer, nullable=False)
    ideal_d1_c = db.Column(db.Integer, nullable=False)
    ideal_d1_d = db.Column(db.Integer, nullable=False)

    # CENÁRIO IDEAL - DIMENSÃO 2
    ideal_d2_a = db.Column(db.Integer, nullable=False)
    ideal_d2_b = db.Column(db.Integer, nullable=False)
    ideal_d2_c = db.Column(db.Integer, nullable=False)
    ideal_d2_d = db.Column(db.Integer, nullable=False)

    # CENÁRIO IDEAL - DIMENSÃO 3
    ideal_d3_a = db.Column(db.Integer, nullable=False)
    ideal_d3_b = db.Column(db.Integer, nullable=False)
    ideal_d3_c = db.Column(db.Integer, nullable=False)
    ideal_d3_d = db.Column(db.Integer, nullable=False)

    # CENÁRIO IDEAL - DIMENSÃO 4
    ideal_d4_a = db.Column(db.Integer, nullable=False)
    ideal_d4_b = db.Column(db.Integer, nullable=False)
    ideal_d4_c = db.Column(db.Integer, nullable=False)
    ideal_d4_d = db.Column(db.Integer, nullable=False)

    # CENÁRIO IDEAL - DIMENSÃO 5
    ideal_d5_a = db.Column(db.Integer, nullable=False)
    ideal_d5_b = db.Column(db.Integer, nullable=False)
    ideal_d5_c = db.Column(db.Integer, nullable=False)
    ideal_d5_d = db.Column(db.Integer, nullable=False)

    # CENÁRIO IDEAL - DIMENSÃO 6
    ideal_d6_a = db.Column(db.Integer, nullable=False)
    ideal_d6_b = db.Column(db.Integer, nullable=False)
    ideal_d6_c = db.Column(db.Integer, nullable=False)
    ideal_d6_d = db.Column(db.Integer, nullable=False)

    def __repr__(self):
        return f"<RespostaCVF {self.identificador}>"
