"""Валюта — to'liq CRUD regression testlari.

Ssenariy mantig'i flows/flow_valyuta.py da (run_valyuta_* — regression
wrapperlari va test_all_runner bilan BO'LISHILADI, yagona manba). Bu yerda faqat
standalone test_* wrapperlari: allure metadata + `m` fixture orqali login.
Basic create (run_valyuta/test_valyuta) tests/test_setup/test_valyuta.py da.
Har test o'z unikal Код bilan ishlaydi (kod prefikslari: 1..7 + {code}).
(MCP tasdiqlangan 2026-07-05).
"""

import allure
from playwright.sync_api import Page

from flows.flow_valyuta import (
    run_valyuta_delete, run_valyuta_duplicate, run_valyuta_edit,
    run_valyuta_full, run_valyuta_status, run_valyuta_view,
)
from utils.base_page import BasePage


@allure.epic("Модератор")
@allure.feature("Валюты")
@allure.story("Создание валюты — все поля")
@allure.title("Валютани BARCHA maydonlar bilan yaratish")
def test_valyuta_full(m: BasePage, page: Page, code) -> None:
    run_valyuta_full(page, code)


#---------------------------------------------------------------------------------------------------


@allure.epic("Модератор")
@allure.feature("Валюты")
@allure.story("Редактирование валюты")
@allure.title("Валютани tahrirlash va o'zgarishni tekshirish")
def test_valyuta_edit(m: BasePage, page: Page, code) -> None:
    run_valyuta_edit(page, code)


#---------------------------------------------------------------------------------------------------


@allure.epic("Модератор")
@allure.feature("Валюты")
@allure.story("Просмотр валюты")
@allure.title("Валюта ma'lumotlari Просмотр formasida to'g'ri ko'rinishi")
def test_valyuta_view(m: BasePage, page: Page, code) -> None:
    run_valyuta_view(page, code)


#---------------------------------------------------------------------------------------------------


@allure.epic("Модератор")
@allure.feature("Валюты")
@allure.story("Удаление валюты")
@allure.title("Валютани o'chirish va ro'yxatdan yo'qolganini tekshirish")
def test_valyuta_delete(m: BasePage, page: Page, code) -> None:
    run_valyuta_delete(page, code)


#---------------------------------------------------------------------------------------------------


@allure.epic("Модератор")
@allure.feature("Валюты")
@allure.story("Статус валюты")
@allure.title("Валюта statusini Неактивный/Активный qilish va tekshirish")
def test_valyuta_status(m: BasePage, page: Page, code) -> None:
    run_valyuta_status(page, code)


#---------------------------------------------------------------------------------------------------


@allure.epic("Модератор")
@allure.feature("Валюты")
@allure.story("Дубликат валюты")
@allure.title("Bir xil Код bilan Валюта qayta yaratishda xatolik chiqishi")
def test_valyuta_duplicate(m: BasePage, page: Page, code) -> None:
    run_valyuta_duplicate(page, code)
