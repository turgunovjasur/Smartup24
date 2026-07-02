from playwright.sync_api import Page

from flows.flow_authorization import authorization
from flows.flow_navbar import flow_navigate
from utils.base_page import BasePage


def run_manufacturer(page: Page, code) -> None:
    """Testcase: Yangi ishlab chiqaruvchi (Производитель) yaratish.

    1. Модератор -> Товары -> Производители ro'yxatini ochish.
    2. "Создать" -> "Название" maydonini to'ldirish.
    3. Saqlab, ro'yxatda nom bo'yicha ko'rinishini tekshirish.
    """
    m = BasePage(page)
    name = f"Manufacturer-{code}"

    flow_navigate(page, tab="Модератор", name="Товары")
    m.expect_heading("Товары")
    m.click_link("Производители")
    m.expect_heading("Производители")

    m.open_create()
    m.expect_heading("Производитель (Создание)")
    m.input(label="Название", value=name)
    m.save_and_expect_heading("Производители")

    m.grid_row(name)


def test_manufacturer(page: Page, code) -> None:
    authorization(page)
    run_manufacturer(page, code)
