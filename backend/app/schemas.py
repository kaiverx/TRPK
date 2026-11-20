"""Схемы данных: что API принимает и что возвращает.

Здесь же выполняется первичная проверка введённых значений
(длина наименования).
"""
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .models import ProposalKind

NAME_MIN = 2
NAME_MAX = 40          # самое длинное наименование территории (30 символов) + 10
DESCRIPTION_MAX = 150


def _clean_name(value: str) -> str:
    """Убрать лишние пробелы и проверить длину наименования."""
    value = " ".join(value.split())
    if len(value) < NAME_MIN:
        raise ValueError(f"Наименование должно содержать не менее {NAME_MIN} символов")
    if len(value) > NAME_MAX:
        raise ValueError(f"Наименование должно содержать не более {NAME_MAX} символов")
    return value


class LoginIn(BaseModel):
    login: str
    password: str


class LoginOut(BaseModel):
    token: str
    full_name: str
    role: str


class CategoryIn(BaseModel):
    name: str
    description: str = Field(default="", max_length=DESCRIPTION_MAX)

    @field_validator("name")
    @classmethod
    def check_name(cls, value: str) -> str:
        return _clean_name(value)


class CategoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str
    is_blocked: bool = False
    updated_at: datetime | None = None


class TerritoryIn(BaseModel):
    name: str

    @field_validator("name")
    @classmethod
    def check_name(cls, value: str) -> str:
        return _clean_name(value)


class TerritoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    is_blocked: bool = False
    updated_at: datetime | None = None


class ProposalIn(BaseModel):
    kind: str
    name: str

    @field_validator("kind")
    @classmethod
    def check_kind(cls, value: str) -> str:
        if value not in (ProposalKind.CATEGORY, ProposalKind.TERRITORY):
            raise ValueError("Можно предложить только категорию или территорию")
        return value

    @field_validator("name")
    @classmethod
    def check_name(cls, value: str) -> str:
        return _clean_name(value)


class ProposalOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    kind: str
    purpose: str
    name: str
    record_id: int | None = None
    record_name: str = ""
    status: str
    created_at: datetime | None = None
    proposed_by_name: str = ""


class RecordOut(BaseModel):
    """Существующая запись, найденная при проверке предложения."""

    id: int
    name: str


class ProposeResultOut(BaseModel):
    """Ответ журналисту на предложение (одна из ветвей проверки).

    result:
      exists         – запись есть в том же написании, её нужно выбрать;
      other_spelling – запись есть в другом написании (record), журналист
                       может выбрать её или сообщить об ошибке написания;
      waiting        – такое же предложение уже ожидает решения менеджера;
      sent           – предложение сохранено в состоянии «новое».
    """

    result: str
    saved: bool
    message: str
    proposal: ProposalOut | None = None
    record: RecordOut | None = None


class SpellingIn(BaseModel):
    """Сообщение журналиста об ошибке в написании существующей записи."""

    kind: str
    record_id: int
    name: str

    @field_validator("kind")
    @classmethod
    def check_kind(cls, value: str) -> str:
        if value not in (ProposalKind.CATEGORY, ProposalKind.TERRITORY):
            raise ValueError("Можно указать только категорию или территорию")
        return value

    @field_validator("name")
    @classmethod
    def check_name(cls, value: str) -> str:
        return _clean_name(value)


class AcceptCategoryIn(CategoryIn):
    """Данные категории, которые менеджер вносит при добавлении по предложению."""


class AcceptTerritoryIn(TerritoryIn):
    """Данные территории, которые менеджер вносит при добавлении по предложению."""
