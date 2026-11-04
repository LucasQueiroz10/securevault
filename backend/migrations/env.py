from logging.config import fileConfig

from alembic import context

from app.core.database import Base, engine

# Importados para registrar as tabelas em Base.metadata. Sem isso, o Alembic
# acharia que elas não existem nos modelos e tentaria apagá-las.
from app.models import audit_log, category, credential, user  # noqa: F401

if context.config.config_file_name is not None:
    fileConfig(context.config.config_file_name)

# A conexão vem de app.core.config, assim a senha nunca fica no alembic.ini.
with engine.connect() as connection:
    context.configure(connection=connection, target_metadata=Base.metadata)

    with context.begin_transaction():
        context.run_migrations()
