"""Main zanjiri — test_main guruhidagi barcha run_* testlarni bitta login
bilan ketma-ket ishga tushiradi (test_all_group_a / test_all_regression
patterni).

2026-07-15 da Организации formasida "Сохранить" tugmasi yo'q edi (UI bag'i,
zanjirda faqat ro'yxat/forma/Просмотр bor edi); 2026-07-19 da tugma qaytgan —
endi to'liq CRUD zanjiri (create, minimal, view, edit, status, delete,
duplicate).
"""
import time

import allure
from playwright.sync_api import Page

from flows.flow_authorization import authorization
from tests.test_main.test_organization import (
    run_organization,
    run_organization_delete,
    run_organization_duplicate,
    run_organization_edit,
    run_organization_minimal,
    run_organization_status,
    run_organization_view,
)
from tests.test_main.test_role import (
    run_role,
    run_role_delete,
    run_role_duplicate,
    run_role_edit,
    run_role_minimal,
    run_role_status,
    run_role_view,
)
from tests.test_main.test_polzovatel import (
    run_user,
    run_user_delete,
    run_user_edit,
    run_user_full,
    run_user_status,
    run_user_view,
)
from tests.test_main.test_announcement import (
    run_announcement,
    run_announcement_delete,
    run_announcement_edit,
    run_announcement_full,
    run_announcement_publish,
    run_announcement_view,
)
from tests.test_main.test_company_client import (
    run_company_client,
    run_company_client_delete,
    run_company_client_edit,
    run_company_client_full,
)


@allure.epic("Модератор")
@allure.feature("Main chain")
@allure.story("Организации + Роли — to'liq CRUD zanjiri")
@allure.title("Main: Организации va Роли CRUD — bitta seansda")
def test_all_main(page: Page, code) -> None:
    """Main guruh testlarini bitta seansda ketma-ket ishga tushiradi."""
    # Bir sessiyada individual testlar bilan nom to'qnashmasligi uchun zanjir
    # o'z code'i bilan ishlaydi
    code = str(int(time.time()))[-7:]
    with allure.step("Tizimga kirish"):
        authorization(page)

    with allure.step("Организации 1. Создание"):
        run_organization(page, code)

    with allure.step("Организации 2. Создание — minimal maydonlar"):
        run_organization_minimal(page, code)

    with allure.step("Организации 3. Просмотр"):
        run_organization_view(page, code)

    with allure.step("Организации 4. Редактирование"):
        run_organization_edit(page, code)

    with allure.step("Организации 5. Статус — Неактивный/Активный"):
        run_organization_status(page, code)

    with allure.step("Организации 6. Удаление"):
        run_organization_delete(page, code)

    with allure.step("Организации 7. Дубликат — nom bilan xatolik"):
        run_organization_duplicate(page, code)

    with allure.step("Роли 1. Создание"):
        run_role(page, code)

    with allure.step("Роли 2. Создание — minimal maydonlar"):
        run_role_minimal(page, code)

    with allure.step("Роли 3. Просмотр"):
        run_role_view(page, code)

    with allure.step("Роли 4. Редактирование"):
        run_role_edit(page, code)

    with allure.step("Роли 5. Статус — Неактивный/Активный"):
        run_role_status(page, code)

    with allure.step("Роли 6. Удаление"):
        run_role_delete(page, code)

    with allure.step("Роли 7. Дубликат — nom bilan xatolik"):
        run_role_duplicate(page, code)

    with allure.step("Пользователи 1. Создание"):
        run_user(page, code)

    with allure.step("Пользователи 2. Создание — barcha maydonlar"):
        run_user_full(page, code)

    with allure.step("Пользователи 3. Просмотр"):
        run_user_view(page, code)

    with allure.step("Пользователи 4. Редактирование"):
        run_user_edit(page, code)

    with allure.step("Пользователи 5. Статус — Неактивный"):
        run_user_status(page, code)

    with allure.step("Пользователи 6. Удаление"):
        run_user_delete(page, code)

    with allure.step("Объявления 1. Создание (Черновик)"):
        run_announcement(page, code)

    with allure.step("Объявления 2. Создание — Отрасли va Регион bilan"):
        run_announcement_full(page, code)

    with allure.step("Объявления 3. Просмотр"):
        run_announcement_view(page, code)

    with allure.step("Объявления 4. Редактирование"):
        run_announcement_edit(page, code)

    with allure.step("Объявления 5. Публикация — статус Опубликовано"):
        run_announcement_publish(page, code)

    with allure.step("Объявления 6. Удаление"):
        run_announcement_delete(page, code)

    with allure.step("Клиенты OAuth2 1. Создание"):
        run_company_client(page, code)

    with allure.step("Клиенты OAuth2 2. Создание — оба доступа"):
        run_company_client_full(page, code)

    with allure.step("Клиенты OAuth2 3. Редактирование"):
        run_company_client_edit(page, code)

    with allure.step("Клиенты OAuth2 4. Удаление"):
        run_company_client_delete(page, code)
