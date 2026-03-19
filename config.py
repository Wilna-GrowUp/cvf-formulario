import os

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "chave-local-simples")

    # Render/PostgreSQL normalmente envia DATABASE_URL como variável de ambiente
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL")

    # Evita aviso desnecessário do SQLAlchemy
    SQLALCHEMY_TRACK_MODIFICATIONS = False
