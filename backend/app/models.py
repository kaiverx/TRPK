"""Классы данных модуля «Управление структурой портала».

Каждый класс соответствует одной таблице базы данных.
"""
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class Role:
    """Роли пользователей портала."""

    JOURNALIST = "journalist"
    EDITOR = "editor"
    MANAGER = "manager"
    ADMIN = "admin"


class ProposalKind:
    """Что именно предлагается добавить: категорию или территорию."""

    CATEGORY = "category"
    TERRITORY = "territory"


class ProposalPurpose:
    """С какой целью журналист направил предложение."""

    ADD = "add"            # добавить новую запись (такой записи нет)
    FIX = "fix"            # исправить написание существующей записи


class ProposalStatus:
    """Состояние предложения."""

    NEW = "new"            # ожидает решения менеджера
    ADDED = "added"        # менеджер добавил запись
    FIXED = "fixed"        # менеджер заблокировал неверную запись и добавил правильную


class User(Base):
    """Учётная запись пользователя портала."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    full_name: Mapped[str] = mapped_column(String(150))
    login: Mapped[str] = mapped_column(String(100), unique=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(20))
    token: Mapped[str | None] = mapped_column(String(64), unique=True, nullable=True)


class Category(Base):
    """Категория – тема новости (например, «Образование»).

    Заблокированная категория не выдаётся для выбора, но остаётся
    в базе данных: к ней уже могут быть отнесены опубликованные новости.
    """

    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(40))
    name_key: Mapped[str] = mapped_column(String(40), index=True)
    description: Mapped[str] = mapped_column(String(150), default="")
    is_blocked: Mapped[bool] = mapped_column(Boolean, default=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())
    updated_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)

    updated_by: Mapped[User | None] = relationship()


class Territory(Base):
    """Территория – любое место, к которому относится новость.

    Вид места не ограничивается: у территории есть только наименование.
    """

    __tablename__ = "territories"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(40))
    name_key: Mapped[str] = mapped_column(String(40), index=True)
    is_blocked: Mapped[bool] = mapped_column(Boolean, default=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())
    updated_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)

    updated_by: Mapped[User | None] = relationship()


class Proposal(Base):
    """Предложение журналиста.

    purpose = add – добавить запись, которой нет;
    purpose = fix – исправить написание существующей записи record_id.
    """

    __tablename__ = "proposals"

    id: Mapped[int] = mapped_column(primary_key=True)
    kind: Mapped[str] = mapped_column(String(10))
    purpose: Mapped[str] = mapped_column(String(5), default=ProposalPurpose.ADD)
    name: Mapped[str] = mapped_column(String(40))
    record_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    record_name: Mapped[str] = mapped_column(String(40), default="")
    status: Mapped[str] = mapped_column(String(10), default=ProposalStatus.NEW)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    proposed_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"))

    proposed_by: Mapped[User] = relationship()
