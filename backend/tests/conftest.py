"""Общие настройки тестов: отдельная временная база данных для каждого теста."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.auth import hash_password
from app.database import Base, get_db
from app.main import app
from app.models import Role, User


@pytest.fixture
def db():
    # База создаётся в оперативной памяти и исчезает после теста
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    yield session
    session.close()


@pytest.fixture
def client(db):
    # Подменяем базу данных приложения на тестовую
    app.dependency_overrides[get_db] = lambda: db
    yield TestClient(app)
    app.dependency_overrides.clear()


def make_user(db, login, role):
    user = User(full_name=f"Тестовый {login}", login=login, password_hash=hash_password("password123"), role=role)
    db.add(user)
    db.commit()
    return user


def login(client, login_name):
    response = client.post("/api/auth/login/", json={"login": login_name, "password": "password123"})
    return {"Authorization": f"Bearer {response.json()['token']}"}


@pytest.fixture
def manager(db):
    return make_user(db, "manager", Role.MANAGER)


@pytest.fixture
def journalist(db):
    return make_user(db, "journalist", Role.JOURNALIST)
