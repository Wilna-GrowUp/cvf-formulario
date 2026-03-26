import os


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "chave-local-simples")

    database_url = os.getenv("DATABASE_URL")

    if database_url:
        if database_url.startswith("postgres://"):
            database_url = database_url.replace("postgres://", "postgresql://", 1)

        SQLALCHEMY_DATABASE_URI = database_url
    else:
        SQLALCHEMY_DATABASE_URI = "sqlite:///cvf_local.db"

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Usuário inicial do administrador
    ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")

    # Senha inicial do administrador
    ADMIN_PASSWORD_INICIAL = os.getenv("ADMIN_PASSWORD_INICIAL", "admin123")

    # Código secreto usado para recuperar acesso na tela "Esqueci a senha"
    ADMIN_RESET_CODE = os.getenv("ADMIN_RESET_CODE", "RECUPERAR-123")

    # Mantido por compatibilidade com versões antigas do projeto
    ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")