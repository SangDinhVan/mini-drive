from alembic import context
from sqlalchemy import create_engine, pool

from app.core.config import Settings
from app.db.models import Base

config = context.config
target_metadata = Base.metadata


def database_url():
    url = Settings.from_env().database_url
    if not url:
        raise RuntimeError("Set DATABASE_URL in backend/.env before running migrations.")
    return url


def run(connection):
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


if context.is_offline_mode():
    context.configure(url=database_url(), target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()
else:
    connection = config.attributes.get("connection")
    if connection is not None:
        run(connection)
    else:
        engine = create_engine(database_url(), poolclass=pool.NullPool, connect_args={"connect_timeout": 10})
        with engine.connect() as connection:
            run(connection)
        engine.dispose()
