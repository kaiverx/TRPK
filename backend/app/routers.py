"""Маршруты API модуля «Управление структурой портала».

Каждая функция здесь принимает HTTP-запрос, передаёт работу
классу StructureService и возвращает ответ в формате JSON.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session

from .auth import issue_token, require_journalist, require_manager, verify_password
from .database import get_db
from .models import Proposal, ProposalKind, Territory, User
from .schemas import (
    CategoryIn,
    CategoryOut,
    LoginIn,
    LoginOut,
    ProposalIn,
    ProposalOut,
    ProposeResultOut,
    RecordOut,
    SpellingIn,
    TerritoryIn,
    TerritoryOut,
)
from .services import (
    DuplicateNameError,
    NotFoundError,
    ProposalClosedError,
    StructureService,
)

router = APIRouter(prefix="/api")


def _service(db: Session = Depends(get_db)) -> StructureService:
    return StructureService(db)


def _proposal_out(p: Proposal) -> ProposalOut:
    out = ProposalOut.model_validate(p)
    out.proposed_by_name = p.proposed_by.full_name if p.proposed_by else ""
    return out


# ---------- Вход (упрощённо, полностью реализуется модулем «Авторизация») ----------

@router.post("/auth/login/", response_model=LoginOut)
def login(data: LoginIn, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.login == data.login))
    if user is None or not verify_password(data.password, user.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Неверный логин или пароль")
    return LoginOut(token=issue_token(db, user), full_name=user.full_name, role=user.role)


# ---------- Категории ----------

@router.get("/categories/", response_model=list[CategoryOut])
def get_categories(all: bool = False, service: StructureService = Depends(_service)):
    """Список категорий для выбора (без заблокированных) доступен всем.

    all=true – полный список вместе с заблокированными (для менеджера).
    """
    return service.list_categories(include_blocked=all)


@router.post("/categories/", response_model=CategoryOut, status_code=status.HTTP_201_CREATED)
def add_category(
    data: CategoryIn,
    user: User = Depends(require_manager),
    service: StructureService = Depends(_service),
):
    try:
        return service.add_category(data, user)
    except DuplicateNameError as error:
        raise HTTPException(status.HTTP_409_CONFLICT, str(error))


@router.patch("/categories/{category_id}/", response_model=CategoryOut)
def update_category(
    category_id: int,
    data: CategoryIn,
    user: User = Depends(require_manager),
    service: StructureService = Depends(_service),
):
    try:
        return service.change_category(category_id, data, user)
    except NotFoundError as error:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(error))
    except DuplicateNameError as error:
        raise HTTPException(status.HTTP_409_CONFLICT, str(error))


# ---------- Территории ----------

@router.get("/territories/", response_model=list[TerritoryOut])
def get_territories(all: bool = False, service: StructureService = Depends(_service)):
    """Список территорий для выбора (без заблокированных) доступен всем.

    all=true – полный список вместе с заблокированными (для менеджера).
    """
    return service.list_territories(include_blocked=all)


@router.post("/territories/", response_model=TerritoryOut, status_code=status.HTTP_201_CREATED)
def add_territory(
    data: TerritoryIn,
    user: User = Depends(require_manager),
    service: StructureService = Depends(_service),
):
    try:
        return service.add_territory(data, user)
    except DuplicateNameError as error:
        raise HTTPException(status.HTTP_409_CONFLICT, str(error))


@router.patch("/territories/{territory_id}/", response_model=TerritoryOut)
def update_territory(
    territory_id: int,
    data: TerritoryIn,
    user: User = Depends(require_manager),
    service: StructureService = Depends(_service),
):
    try:
        return service.change_territory(territory_id, data, user)
    except NotFoundError as error:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(error))
    except DuplicateNameError as error:
        raise HTTPException(status.HTTP_409_CONFLICT, str(error))


# ---------- Блокировка ----------

def _set_blocked(kind, record_id, blocked, user, service):
    try:
        record = service.set_blocked(kind, record_id, blocked, user)
    except NotFoundError as error:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(error))
    except DuplicateNameError as error:
        raise HTTPException(status.HTTP_409_CONFLICT, f"{error}, блокировку снять нельзя")
    if kind == ProposalKind.TERRITORY:
        return TerritoryOut.model_validate(record)
    return CategoryOut.model_validate(record)


@router.post("/categories/{record_id}/block/", response_model=CategoryOut)
def block_category(record_id: int, user: User = Depends(require_manager),
                   service: StructureService = Depends(_service)):
    return _set_blocked(ProposalKind.CATEGORY, record_id, True, user, service)


@router.post("/categories/{record_id}/unblock/", response_model=CategoryOut)
def unblock_category(record_id: int, user: User = Depends(require_manager),
                     service: StructureService = Depends(_service)):
    return _set_blocked(ProposalKind.CATEGORY, record_id, False, user, service)


@router.post("/territories/{record_id}/block/", response_model=TerritoryOut)
def block_territory(record_id: int, user: User = Depends(require_manager),
                    service: StructureService = Depends(_service)):
    return _set_blocked(ProposalKind.TERRITORY, record_id, True, user, service)


@router.post("/territories/{record_id}/unblock/", response_model=TerritoryOut)
def unblock_territory(record_id: int, user: User = Depends(require_manager),
                      service: StructureService = Depends(_service)):
    return _set_blocked(ProposalKind.TERRITORY, record_id, False, user, service)


# ---------- Предложения журналистов ----------

def _answer_out(answer) -> ProposeResultOut:
    return ProposeResultOut(
        result=answer.result,
        saved=answer.proposal is not None,
        message=answer.message,
        proposal=_proposal_out(answer.proposal) if answer.proposal else None,
        record=RecordOut(id=answer.record.id, name=answer.record.name) if answer.record else None,
    )

@router.post("/proposals/", response_model=ProposeResultOut)
def create_proposal(
    data: ProposalIn,
    user: User = Depends(require_journalist),
    service: StructureService = Depends(_service),
):
    return _answer_out(service.propose(data.kind, data.name, user))


@router.post("/proposals/spelling/", response_model=ProposeResultOut)
def report_spelling(
    data: SpellingIn,
    user: User = Depends(require_journalist),
    service: StructureService = Depends(_service),
):
    try:
        return _answer_out(service.report_spelling(data.kind, data.record_id, data.name, user))
    except NotFoundError as error:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(error))


@router.get("/proposals/", response_model=list[ProposalOut])
def get_new_proposals(
    user: User = Depends(require_manager),
    service: StructureService = Depends(_service),
):
    return [_proposal_out(p) for p in service.list_new_proposals()]


@router.post("/proposals/{proposal_id}/accept/", status_code=status.HTTP_201_CREATED)
def accept_proposal(
    proposal_id: int,
    data: dict,
    user: User = Depends(require_manager),
    service: StructureService = Depends(_service),
):
    try:
        record = service.accept_proposal(proposal_id, data, user)
    except ValidationError as error:
        first = error.errors()[0]
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, first["msg"].removeprefix("Value error, "))
    except NotFoundError as error:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(error))
    except ProposalClosedError as error:
        raise HTTPException(status.HTTP_409_CONFLICT, str(error))
    except DuplicateNameError as error:
        raise HTTPException(status.HTTP_409_CONFLICT, f"{error}, новая запись не создана")
    if isinstance(record, Territory):
        return TerritoryOut.model_validate(record)
    return CategoryOut.model_validate(record)
