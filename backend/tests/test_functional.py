import pytest

from app.models import Category, Proposal, ProposalStatus

from .conftest import login


@pytest.mark.functional
def test_manager_adds_category_from_journalist_proposal(client, db, manager, journalist):
    """
    Функциональный тест.
    Проверяет полный путь: журналист предлагает категорию,
    менеджер добавляет её, категория появляется в общем списке.
    """
    print("\n[Функциональный тест] Добавление категории по предложению журналиста")

    # 1. Журналист отправляет предложение новой категории
    journalist_headers = login(client, "journalist")
    response = client.post("/api/proposals/", json={"kind": "category", "name": "Экология"},
                           headers=journalist_headers)
    assert response.status_code == 200
    assert response.json()["saved"] is True
    proposal_id = response.json()["proposal"]["id"]
    assert response.json()["proposal"]["status"] == ProposalStatus.NEW

    # 2. Менеджер видит предложение в списке новых
    manager_headers = login(client, "manager")
    proposals = client.get("/api/proposals/", headers=manager_headers).json()
    assert [p["name"] for p in proposals] == ["Экология"]

    # 3. Менеджер добавляет категорию с описанием
    response = client.post(f"/api/proposals/{proposal_id}/accept/",
                           json={"name": "Экология", "description": "Охрана природы, качество воздуха и воды"},
                           headers=manager_headers)
    assert response.status_code == 201

    # 4. Категория появилась в списке, предложение закрыто
    categories = client.get("/api/categories/").json()
    assert [c["name"] for c in categories] == ["Экология"]
    assert db.get(Proposal, proposal_id).status == ProposalStatus.ADDED
    assert db.query(Category).count() == 1

    # 5. Повторное предложение той же категории не сохраняется,
    #    журналист сразу получает сообщение, что категория уже есть
    repeat = client.post("/api/proposals/", json={"kind": "category", "name": "Экология"},
                         headers=journalist_headers).json()
    assert repeat["result"] == "exists"
    assert repeat["saved"] is False
    assert repeat["message"] == "Категория «Экология» уже есть, выберите её в поле формы"
    #    То же наименование в другом написании: журналисту показывается
    #    существующее написание, предложение тоже не сохраняется
    other = client.post("/api/proposals/", json={"kind": "category", "name": "экология "},
                        headers=journalist_headers).json()
    assert other["result"] == "other_spelling"
    assert other["record"]["name"] == "Экология"
    assert db.query(Proposal).count() == 1

    # 6. Журналист не может добавлять категории сам
    forbidden = client.post(f"/api/proposals/{proposal_id}/accept/", json={"name": "Экология"},
                            headers=journalist_headers)
    assert forbidden.status_code == 403

    print("Запрос: POST /api/proposals/{id}/accept/")
    print(f"Статус ответа: {response.status_code}")
    print(f"Категорий в списке: {len(categories)} ({categories[0]['name']})")
    print(f"Состояние предложения: {db.get(Proposal, proposal_id).status}")
    print(f"Повторное предложение: «{repeat['message']}»")
    print(f"Другое написание «экология »: ответ {other['result']}, показано «{other['record']['name']}»")
    print(f"Попытка журналиста: статус {forbidden.status_code} (нет прав)")
    print("Ожидаемый результат: категория добавлена, при наличии записи предложение не сохраняется")
    print("Фактический результат: тест пройден")
