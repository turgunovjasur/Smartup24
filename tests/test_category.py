from playwright.sync_api import Page

from flows.flow_authorization import authorization
from flows.flow_navbar import flow_navigate
from utils.base_page import BasePage


def run_category(page: Page, code) -> None:
    """Testcase: "Категория" xarakteristikasiga yangi podtip qo'shish.

    1. Модератор -> Товары -> Характеристика товаров ro'yxatini ochish.
    2. "Категория" guruhini tanlab "Подтипы" ga o'tish.
    3. "Создать" -> "Название" maydonini to'ldirish.
    4. Saqlab, ro'yxatda ko'rinishini tekshirish.
    """
    m = BasePage(page)
    name = f"Category-{code}"

    flow_navigate(page, tab="Модератор", name="Товары")
    m.expect_heading("Товары")
    m.click_link("Характеристика товаров")
    m.expect_heading("Характеристика товаров")

    m.click_grid_row("Категория")
    m.click_button("Подтипы")
    m.expect_heading("Категория")

    m.open_create()
    m.expect_heading("Характеристика товаров (создание)")
    m.input(label="Название", value=name)
    m.save_and_expect_heading("Категория")

    m.grid_row(name)


def test_category(page: Page, code) -> None:
    authorization(page)
    run_category(page, code)
