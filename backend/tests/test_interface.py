import json
import os

import pytest
from playwright.sync_api import expect

PORTAL_URL = os.getenv("PORTAL_URL", "http://localhost:8001")


@pytest.mark.interface
def test_empty_territory_form_shows_error_and_does_not_send_request(page):
    """
    Интерфейсный тест.
    Проверяет, что форма добавления территории с пустым наименованием
    или слишком коротким наименованием показывает ошибку и не отправляет запрос на сервер.
    """
    print("\n[Интерфейсный тест] Проверка пустой формы добавления территории")

    # Список для фиксации запросов на добавление записи по предложению
    accept_requests = []

    # Интерфейс должен считать, что вошёл менеджер:
    # данные сеанса записываются в браузер до загрузки страницы
    page.add_init_script(
        "sessionStorage.setItem('token','test-token');"
        "sessionStorage.setItem('fullName','Тестовый менеджер');"
        "sessionStorage.setItem('role','manager');"
    )

    # Мок списка предложений: одно предложение территории
    page.route("**/api/proposals/", lambda route: route.fulfill(
        status=200,
        content_type="application/json",
        body=json.dumps([{
            "id": 7, "kind": "territory", "name": "Шелехов", "status": "new",
            "created_at": "2026-10-20T10:00:00", "proposed_by_name": "Петров А.И.",
        }]),
    ))

    # Любой запрос на добавление фиксируется, чтобы проверить, что его не было
    def handle_accept(route):
        accept_requests.append(route.request)
        route.fulfill(status=201, content_type="application/json", body="{}")

    page.route("**/api/proposals/*/accept/", handle_accept)

    # Открываем страницу предложений и форму добавления
    page.goto(f"{PORTAL_URL}/manager/proposals")
    page.click("[data-test=accept]")

    # Стираем наименование
    page.fill("[data-test=field-name]", "   ")
    page.click("[data-test=save]")

    # Форма показывает понятную ошибку и остаётся открытой
    error = page.locator("[data-test=form-error]")
    expect(error).to_have_text("Наименование должно содержать не менее 2 символов")
    expect(page.locator("[data-test=structure-form]")).to_be_visible()

    # Вводим наименование из одной буквы
    page.fill("[data-test=field-name]", "Ш")
    page.click("[data-test=save]")
    expect(error).to_have_text("Наименование должно содержать не менее 2 символов")
    expect(page.locator("[data-test=structure-form]")).to_be_visible()

    # Запрос на сервер ни разу не отправлялся
    assert accept_requests == []

    print("Действие: «Сохранить» с пустым наименованием, затем с наименованием из одной буквы")
    print(f"Сообщение формы: «{error.inner_text()}»")
    print(f"Отправлено запросов на добавление: {len(accept_requests)}")
    print("Ожидаемый результат: ошибка показана, запрос не отправлен")
    print("Фактический результат: тест пройден")
