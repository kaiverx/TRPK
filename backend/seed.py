"""Начальное заполнение базы данных.

Создаёт тестовых пользователей и начальный перечень категорий и
территорий Иркутской области, который загружается при вводе портала
в эксплуатацию.
"""
from app.auth import hash_password
from app.database import Base, SessionLocal, engine
from app.models import Category, Proposal, ProposalKind, ProposalPurpose, Role, Territory, User
from app.services import make_name_key

USERS = [
    ("Иванова Мария Сергеевна", "manager", Role.MANAGER),
    ("Петров Алексей Игоревич", "journalist", Role.JOURNALIST),
    ("Смирнова Ольга Викторовна", "editor", Role.EDITOR),
]
CATEGORIES = [
    ("Образование", "Школы, вузы, колледжи, детские сады"),
    ("Культура", "Театры, музеи, концерты, выставки"),
    ("Спорт", "Соревнования, спортивные объекты, достижения спортсменов"),
    ("Транспорт", "Дороги, общественный транспорт, авиа- и железнодорожное сообщение"),
    ("Здравоохранение", "Больницы, поликлиники, профилактика заболеваний"),
]
TERRITORIES = [
    "Иркутск",
    "Ангарск",
    "Братск",
    "Иркутский район",
    "Слюдянский район",
    "посёлок Листвянка",
    "Усть-кут",          # записано с ошибкой: правильно «Усть-Кут»
]
BLOCKED_TERRITORIES = ["Усть-Ордынский Бурятский округ"]


def run():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    users = {}
    for full_name, login, role in USERS:
        user = User(full_name=full_name, login=login, password_hash=hash_password("password123"), role=role)
        db.add(user)
        users[login] = user
    db.flush()
    for name, description in CATEGORIES:
        db.add(Category(name=name, name_key=make_name_key(name), description=description))
    for name in TERRITORIES:
        db.add(Territory(name=name, name_key=make_name_key(name)))
    for name in BLOCKED_TERRITORIES:
        db.add(Territory(name=name, name_key=make_name_key(name), is_blocked=True))
    db.add(Proposal(kind=ProposalKind.CATEGORY, name="Экология", proposed_by_id=users["journalist"].id))
    db.add(Proposal(kind=ProposalKind.TERRITORY, name="Усолье-Сибирское", proposed_by_id=users["journalist"].id))
    db.add(Proposal(kind=ProposalKind.CATEGORY, name="Туризм", proposed_by_id=users["journalist"].id))
    db.flush()
    wrong = db.query(Territory).filter_by(name="Усть-кут").one()
    db.add(Proposal(kind=ProposalKind.TERRITORY, purpose=ProposalPurpose.FIX, name="Усть-Кут",
                    record_id=wrong.id, record_name=wrong.name, proposed_by_id=users["journalist"].id))
    db.commit()
    db.close()
    print("База данных заполнена начальными данными")


if __name__ == "__main__":
    run()
