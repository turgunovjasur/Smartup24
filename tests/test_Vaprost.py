from playwright.sync_api import Page

from flows.flow_authorization import authorization
from flows.flow_navbar import flow_navigate
from utils.base_page import BasePage


def run_vaprost(page: Page, code) -> None:
    """Testcase: valyuta yaratish.

    1. Модератор -> Vaprost ro'yxatini ochish.
    2. "Создать" -> nom/INN/Форма собственности to'ldirish,
    3. Saqlab, ro'yxatда qidirib nom bo'yicha ko'rinishini tekshirish.
    """
    m = BasePage(page)
    name = f"Vaprost{code}"

    flow_navigate(page, tab="Модератор", name="Вопросы")
    m.expect_heading("Вопросы")

    m.open_create()
    m.expect_heading("Вопрос (Создание)")
    m.input(label="Название ", value=name)

    m.save_and_expect_heading("Вопросы")

    m.search(name)
    m.grid_row(name)


def test_vaprost(page: Page, code) -> None:
    authorization(page)
    run_vaprost(page, code)
