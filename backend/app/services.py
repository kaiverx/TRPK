"""Логика модуля «Управление структурой портала».

Класс StructureService выполняет все действия с категориями и территориями:
ведение (добавление, изменение, блокировка), проверку данных записи,
формирование списков и обработку предложений журналистов.
"""
from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import (
    Category,
    Proposal,
    ProposalKind,
    ProposalPurpose,
    ProposalStatus,
    Territory,
    User,
)
from .schemas import CategoryIn, TerritoryIn


class StructureError(Exception):
    """Общая ошибка модуля: операция не может быть выполнена."""


class DuplicateNameError(StructureError):
    """Действующая запись с таким наименованием уже есть."""


class NotFoundError(StructureError):
    """Запись не найдена."""


class ProposalClosedError(StructureError):
    """По предложению уже принято решение."""


def make_name_key(name: str) -> str:
    """Сформировать ключ для сравнения наименований.

    Ключ не зависит от регистра букв, лишних пробелов и
    написания «ё»/«е», поэтому «Усть-Кут», «усть-кут » и «УСТЬ-КУТ»
    при сравнении считаются одним наименованием. Выводится же
    наименование так, как его записал менеджер.
    """
    return " ".join(name.split()).lower().replace("ё", "е")


def clean_name(name: str) -> str:
    """Убрать лишние пробелы, сохранив написание букв."""
    return " ".join(name.split())


class ProposalAnswer:
    """Ответ системы на предложение журналиста (одна из трёх ветвей проверки)."""

    EXISTS = "exists"                  # запись есть и написана так же – выбрать её
    OTHER_SPELLING = "other_spelling"  # запись есть, но написана иначе
    WAITING = "waiting"                # такое предложение уже ожидает решения менеджера
    SENT = "sent"                      # записи нет – предложение отправлено менеджеру

    def __init__(self, result: str, message: str, proposal=None, record=None):
        self.result = result
        self.message = message
        self.proposal = proposal
        self.record = record


class StructureService:
    """Действия со структурой портала: категориями и территориями."""

    def __init__(self, db: Session):
        self.db = db

    @staticmethod
    def _model(kind: str):
        return (Category, "Категория") if kind == ProposalKind.CATEGORY else (Territory, "Территория")

    # ---------- Проверка данных записи ----------

    def find_active(self, kind: str, name: str, exclude_id: int | None = None):
        """Найти действующую (незаблокированную) запись с таким наименованием."""
        model, _ = self._model(kind)
        query = select(model).where(model.name_key == make_name_key(name), model.is_blocked.is_(False))
        if exclude_id is not None:
            query = query.where(model.id != exclude_id)
        return self.db.scalar(query)

    def category_exists(self, name: str, exclude_id: int | None = None) -> bool:
        """Проверить, есть ли действующая категория с таким наименованием."""
        return self.find_active(ProposalKind.CATEGORY, name, exclude_id) is not None

    def territory_exists(self, name: str, exclude_id: int | None = None) -> bool:
        """Проверить, есть ли действующая территория с таким наименованием."""
        return self.find_active(ProposalKind.TERRITORY, name, exclude_id) is not None

    def _check(self, kind: str, name: str, exclude_id: int | None = None):
        """Проверить данные записи перед сохранением (длина проверяется в схеме)."""
        found = self.find_active(kind, name, exclude_id)
        if found is not None:
            _, label = self._model(kind)
            raise DuplicateNameError(f"{label} «{found.name}» уже есть")

    # ---------- Ведение: добавление ----------

    def add_category(self, data: CategoryIn, user: User) -> Category:
        """Добавить новую категорию."""
        self._check(ProposalKind.CATEGORY, data.name)
        category = Category(
            name=data.name,
            name_key=make_name_key(data.name),
            description=data.description.strip(),
            updated_by_id=user.id,
        )
        self.db.add(category)
        self.db.commit()
        self.db.refresh(category)
        return category

    def add_territory(self, data: TerritoryIn, user: User) -> Territory:
        """Добавить новую территорию."""
        self._check(ProposalKind.TERRITORY, data.name)
        territory = Territory(name=data.name, name_key=make_name_key(data.name), updated_by_id=user.id)
        self.db.add(territory)
        self.db.commit()
        self.db.refresh(territory)
        return territory

    # ---------- Ведение: изменение ----------

    def change_category(self, category_id: int, data: CategoryIn, user: User) -> Category:
        """Изменить наименование или описание категории."""
        category = self.db.get(Category, category_id)
        if category is None:
            raise NotFoundError("Категория не найдена")
        self._check(ProposalKind.CATEGORY, data.name, exclude_id=category_id)
        category.name = data.name
        category.name_key = make_name_key(data.name)
        category.description = data.description.strip()
        category.updated_by_id = user.id
        self.db.commit()
        self.db.refresh(category)
        return category

    def change_territory(self, territory_id: int, data: TerritoryIn, user: User) -> Territory:
        """Изменить наименование территории."""
        territory = self.db.get(Territory, territory_id)
        if territory is None:
            raise NotFoundError("Территория не найдена")
        self._check(ProposalKind.TERRITORY, data.name, exclude_id=territory_id)
        territory.name = data.name
        territory.name_key = make_name_key(data.name)
        territory.updated_by_id = user.id
        self.db.commit()
        self.db.refresh(territory)
        return territory

    # ---------- Ведение: блокировка ----------

    def set_blocked(self, kind: str, record_id: int, blocked: bool, user: User):
        """Заблокировать запись или снять блокировку.

        Заблокированная запись не выдаётся для выбора, но не удаляется:
        опубликованные новости остаются отнесёнными к ней.
        """
        model, label = self._model(kind)
        record = self.db.get(model, record_id)
        if record is None:
            raise NotFoundError(f"{label} не найдена")
        if not blocked:
            self._check(kind, record.name, exclude_id=record_id)
        record.is_blocked = blocked
        record.updated_by_id = user.id
        self.db.commit()
        self.db.refresh(record)
        return record

    # ---------- Формирование списков ----------

    def list_categories(self, include_blocked: bool = False) -> list[Category]:
        """Сформировать список категорий по алфавиту (для выбора – без заблокированных)."""
        query = select(Category).order_by(Category.name_key)
        if not include_blocked:
            query = query.where(Category.is_blocked.is_(False))
        return list(self.db.scalars(query))

    def list_territories(self, include_blocked: bool = False) -> list[Territory]:
        """Сформировать список территорий по алфавиту (для выбора – без заблокированных)."""
        query = select(Territory).order_by(Territory.name_key)
        if not include_blocked:
            query = query.where(Territory.is_blocked.is_(False))
        return list(self.db.scalars(query))

    # ---------- Обработка предложений журналистов ----------

    def _waiting(self, kind: str, purpose: str, name: str):
        key = make_name_key(name)
        for p in self.list_new_proposals():
            if p.kind == kind and p.purpose == purpose and make_name_key(p.name) == key:
                return p
        return None

    def propose(self, kind: str, name: str, user: User) -> ProposalAnswer:
        """Проверить предложение журналиста и сформировать ответ.

        Три ветви проверки:
        1) действующая запись есть и написана так же – предлагается выбрать её;
        2) запись есть, но написана иначе (другой регистр, пробелы, «ё»/«е») –
           журналисту показывается существующее написание; если оно неверное,
           журналист может сообщить об ошибке написания (report_spelling);
        3) записи нет – предложение сохраняется в состоянии «новое»
           и передаётся менеджеру (если такое же уже не ожидает решения).
        """
        _, label = self._model(kind)
        name = clean_name(name)
        found = self.find_active(kind, name)
        if found is not None and found.name == name:
            return ProposalAnswer(ProposalAnswer.EXISTS,
                                  f"{label} «{found.name}» уже есть, выберите её в поле формы", record=found)
        if found is not None:
            return ProposalAnswer(ProposalAnswer.OTHER_SPELLING,
                                  f"{label} уже есть в написании «{found.name}». Выберите её или, "
                                  f"если написание неверное, сообщите об ошибке", record=found)
        waiting = self._waiting(kind, ProposalPurpose.ADD, name)
        if waiting is not None:
            return ProposalAnswer(ProposalAnswer.WAITING,
                                  f"{label} «{waiting.name}» уже предложена и ожидает решения менеджера")
        proposal = Proposal(kind=kind, purpose=ProposalPurpose.ADD, name=name,
                            status=ProposalStatus.NEW, proposed_by_id=user.id)
        self.db.add(proposal)
        self.db.commit()
        self.db.refresh(proposal)
        return ProposalAnswer(ProposalAnswer.SENT, "Предложение отправлено менеджеру", proposal=proposal)

    def report_spelling(self, kind: str, record_id: int, name: str, user: User) -> ProposalAnswer:
        """Сообщить менеджеру об ошибке в написании существующей записи."""
        model, label = self._model(kind)
        record = self.db.get(model, record_id)
        if record is None or record.is_blocked:
            raise NotFoundError(f"{label} не найдена")
        name = clean_name(name)
        waiting = self._waiting(kind, ProposalPurpose.FIX, name)
        if waiting is not None:
            return ProposalAnswer(ProposalAnswer.WAITING,
                                  f"Сообщение об ошибке в написании «{record.name}» уже ожидает решения менеджера")
        proposal = Proposal(kind=kind, purpose=ProposalPurpose.FIX, name=name,
                            record_id=record.id, record_name=record.name,
                            status=ProposalStatus.NEW, proposed_by_id=user.id)
        self.db.add(proposal)
        self.db.commit()
        self.db.refresh(proposal)
        return ProposalAnswer(ProposalAnswer.SENT, "Сообщение об ошибке написания отправлено менеджеру",
                              proposal=proposal)

    def list_new_proposals(self) -> list[Proposal]:
        """Выбрать предложения в состоянии «новое» в порядке поступления."""
        query = (
            select(Proposal)
            .where(Proposal.status == ProposalStatus.NEW)
            .order_by(Proposal.created_at, Proposal.id)
        )
        return list(self.db.scalars(query))

    def accept_proposal(self, proposal_id: int, data: dict, user: User):
        """Выполнить предложение журналиста.

        Добавление: менеджер добавляет запись, предложение получает «добавлено».
        Исправление: менеджер блокирует запись с неверным написанием
        (опубликованные новости остаются с ней) и добавляет запись
        в правильном написании, предложение получает «исправлено».
        """
        proposal = self.db.get(Proposal, proposal_id)
        if proposal is None:
            raise NotFoundError("Предложение не найдено")
        if proposal.status != ProposalStatus.NEW:
            raise ProposalClosedError("По этому предложению решение уже принято")

        schema = CategoryIn if proposal.kind == ProposalKind.CATEGORY else TerritoryIn
        clean = schema(**data)
        model, _ = self._model(proposal.kind)
        if proposal.purpose == ProposalPurpose.FIX and proposal.record_id:
            old = self.db.get(model, proposal.record_id)
            if old is not None and not old.is_blocked:
                old.is_blocked = True
                old.updated_by_id = user.id
                self.db.flush()
        try:
            if proposal.kind == ProposalKind.CATEGORY:
                record = self.add_category(clean, user)
            else:
                record = self.add_territory(clean, user)
        except DuplicateNameError:
            self.db.rollback()
            raise
        proposal.status = ProposalStatus.FIXED if proposal.purpose == ProposalPurpose.FIX else ProposalStatus.ADDED
        self.db.commit()
        return record
