from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from .config import SCHEMA, sqlalchemy_url

engine = create_engine(
    sqlalchemy_url(),
    pool_pre_ping=True,
    future=True,
    connect_args={"options": f"-csearch_path={SCHEMA},public"},
)

SessionLocal = sessionmaker(bind=engine, expire_on_commit=False, class_=Session)


def session_scope() -> Session:
    return SessionLocal()
