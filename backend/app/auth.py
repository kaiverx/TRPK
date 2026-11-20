"""Проверка пользователя и его прав доступа.

Вход в систему выполняется в модуле «Авторизация». Здесь находится
только то, что нужно модулю структуры: получить пользователя по
токену и убедиться, что его роль разрешает выполнить действие.
"""
import hashlib
import hmac
import secrets

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from .database import get_db
from .models import Role, User

_SALT = b"news-portal-structure"


def hash_password(password: str) -> str:
    """Получить хеш пароля (сам пароль в базе не хранится)."""
    return hashlib.pbkdf2_hmac("sha256", password.encode(), _SALT, 100_000).hex()


def verify_password(password: str, password_hash: str) -> bool:
    """Сравнить введённый пароль с сохранённым хешем."""
    return hmac.compare_digest(hash_password(password), password_hash)


def issue_token(db: Session, user: User) -> str:
    """Выдать пользователю новый токен – пропуск для следующих запросов."""
    user.token = secrets.token_hex(32)
    db.commit()
    return user.token


def get_current_user(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> User:
    """Определить пользователя по заголовку Authorization: Bearer <токен>."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Требуется вход в систему")
    token = authorization.removeprefix("Bearer ").strip()
    user = db.scalar(select(User).where(User.token == token))
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Требуется вход в систему")
    return user


def require_roles(*roles: str):
    """Создать проверку: пропустить только пользователей с указанными ролями."""

    def checker(user: User = Depends(get_current_user)) -> User:
        if user.role not in roles:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Недостаточно прав для этого действия")
        return user

    return checker


require_manager = require_roles(Role.MANAGER)
require_journalist = require_roles(Role.JOURNALIST)
