"""Подключение к базе данных.

Модуль создаёт соединение с базой данных и выдаёт сессию
(«сеанс работы с базой») каждому запросу к API.
"""
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

# Адрес базы данных берётся из переменной окружения.
# По умолчанию используется файл SQLite рядом с приложением.
DATABASE_URL = os.getenv("PORTAL_DATABASE_URL", "sqlite:///./portal.db")

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {},
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    """Базовый класс для всех таблиц базы данных."""


def get_db():
    """Выдать сессию базы данных на время одного запроса и закрыть её после."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
