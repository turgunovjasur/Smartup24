from playwright.sync_api import Page

from flows.flow_authorization import authorization
from flows.flow_navbar import flow_navigate
from utils.base_page import BasePage


def run_territory(page: Page, code) -> None:
    """Testcase: Territory yaratish.

    1. Модератор -> territory ro'yxatini ochish.
    2. "Создать" -> nom/
    3. Saqlab, ro'yxatда qidirib nom bo'yicha ko'rinishini tekshirish.
    """
    m = BasePage(page)
    name = f"territory-{code}"

    flow_navigate(page, tab="Модератор", name="Tерритории")
    m.expect_heading("Tерритории")

    m.open_create()
    m.expect_heading("Tерритория (Создания)")
    m.input(label="Название", value=name)

    m.save_and_expect_heading("Tерритории")

    m.search(name)
    m.grid_row(name)


def test_territory(page: Page, code) -> None:
    authorization(page)
    run_territory(page, code)
