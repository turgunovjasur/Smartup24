from playwright.sync_api import Page

from flows.flow_authorization import authorization
from flows.flow_navbar import flow_navigate
from utils.base_page import BasePage


def run_bonus(page: Page, code) -> None:
    """Testcase: Yangi bonus tizimi (Бонусная система) yaratish.

    "Начало"/"Конец" — smt-date-picker (sana matn sifatida kiritiladi).

    1. Модератор -> Бонусная система ro'yxatini ochish.
    2. "Создать" -> Название, Значение va sana oralig'ini to'ldirish.
    3. Saqlab, ro'yxatда qidirib nom bo'yicha ko'rinishini tekshirish.
    """
    m = BasePage(page)
    name = f"bonus-{code}"

    flow_navigate(page, tab="Модератор", name="Бонусная система")
    m.expect_heading("Бонусная система")

    m.open_create()
    m.expect_heading("Создать бонусную систему")
    m.input(label="Название", value=name)
    m.input(label="Значение", value="5")
    m.input(label="Начало", value="01.07.2026")
    m.input(label="Конец", value="30.07.2026")

    m.save_and_expect_heading("Бонусная система")

    m.search(name)
    m.grid_row(name)


def test_bonus(page: Page, code) -> None:
    authorization(page)
    run_bonus(page, code)