from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Lido da variável de ambiente DATABASE_URL ou do arquivo .env. Sem valor
    # padrão de propósito: se faltar, a aplicação nem inicia. SecretStr esconde
    # o valor em print/logs, porque a URL do PostgreSQL vai conter a senha.
    database_url: SecretStr

    model_config = SettingsConfigDict(
        env_file=".env",
        # utf-8-sig aceita o arquivo com ou sem BOM (o Out-File -Encoding utf8
        # do PowerShell 5.1 grava com BOM).
        env_file_encoding="utf-8-sig",
        # O .env pode ter variáveis de outros serviços (ex.: as do PostgreSQL
        # no Docker Compose); as que não são da aplicação são ignoradas.
        extra="ignore",
    )


settings = Settings()
