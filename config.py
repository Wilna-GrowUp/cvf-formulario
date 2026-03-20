<<<<<<< HEAD
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

    # Senha simples do administrador
    ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")
=======
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

    # Senha simples do administrador
    ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")
>>>>>>> 4c591baf6ce64bd7edfeb8feb4bbcbfea24a9484
