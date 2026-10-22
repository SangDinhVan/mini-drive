from fastapi import HTTPException, Request
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


def build_sessions(database_url: str):
    engine = create_engine(database_url, pool_pre_ping=True, connect_args={"connect_timeout": 10})
    return engine, sessionmaker(engine, expire_on_commit=False)


def get_db(request: Request):
    sessions = request.app.state.sessions
    if sessions is None:
        raise HTTPException(503, "Set DATABASE_URL in backend/.env and run alembic upgrade head.")
    with sessions() as session:
        yield session
