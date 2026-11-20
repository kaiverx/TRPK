import pytest

from app.models import Category
from app.services import StructureService, make_name_key


@pytest.mark.unit
def test_category_exists_ignores_case_spaces_and_yo(db):
    """
    Модульный тест.
    Проверяет отдельный метод category_exists() класса StructureService:
    наименования, которые отличаются только регистром букв, лишними
    пробелами и буквой «ё», должны считаться одинаковыми.
    """
    print("\n[Модульный тест] Проверка наличия категории в списке")

    # В списке уже есть категория «Учёба и наука»
    db.add(Category(name="Учёба и наука", name_key=make_name_key("Учёба и наука"), description=""))
    db.commit()
    service = StructureService(db)

    # Тот же текст, но другим регистром, с лишними пробелами и через «е»
    entered = "  учеба   И НАУКА "
    result = service.category_exists(entered)

    assert result is True
    # Действительно новое наименование не должно считаться существующим
    assert service.category_exists("Экология") is False

    print(f"Входные данные: «{entered}»")
    print("Ожидаемый результат: True (категория уже есть в списке)")
    print(f"Фактический результат: {result}, тест пройден")
