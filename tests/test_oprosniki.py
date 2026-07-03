from playwright.sync_api import Page

from flows.flow_authorization import authorization
from flows.flow_navbar import flow_navigate
from utils.base_page import BasePage


def run_oprsoniki(page: Page, code) -> None:
    """Testcase: Oprosniki tizimi (oprosniki) yaratish.

    "Начало"/"Конец" — smt-date-picker (sana matn sifatida kiritiladi).

    1. Модератор -> oprosniki система ro'yxatini ochish.
    2. "Создать" -> Название, Значение va sana oralig'ini to'ldirish.
    3. Saqlab, ro'yxatда qidirib nom bo'yicha ko'rinishini tekshirish.
    """
    m = BasePage(page)
    name = f"oprsoniki-{code}"

    flow_navigate(page, tab="Модератор", name="Опросники")
    m.expect_heading("Опросники")

    m.open_create()
    m.expect_heading("Опросник (Создание)")
    m.input(label="Название", value=name)
    m.save_and_expect_heading("Опросники")

    m.search(name)
    m.grid_row(name)


def test_bonus(page: Page, code) -> None:
    authorization(page)
    run_oprsoniki(page, code)