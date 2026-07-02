from playwright.sync_api import Page

from flows.flow_authorization import authorization
from flows.flow_navbar import flow_navigate
from utils.base_page import BasePage


def run_product(page: Page, code) -> None:
    """Testcase: Yangi mahsulot (Продукт) yaratish.

    1. Модератор -> Товары ro'yxatini ochish.
    2. "Создать" -> majburiy maydonlarni to'ldirish (Название, Краткое название, Код).
    3. Производитель va measure ni tanlash.
    4. "Характеристика" bo'limida "Отрасль" ni tanlash.
    5. Saqlab, ro'yxatda nom bo'yicha ko'rinishini tekshirish.
    """
    m = BasePage(page)
    name = f"product-{code}"

    flow_navigate(page, tab="Модератор", name="Товары")
    m.expect_heading("Товары")

    m.open_create()
    m.expect_heading("Продукт (создание)")
    m.input(label="Название", value=name)
    m.input(label="Краткое название", value=f"pr-{code}")
    m.input(label="Код", value=f"code-{code}")
    m.select(f"Manufacturer-{code}", label="Производитель")
    m.select("кг", label="measure")

    m.click_button("Характеристика")
    m.select(f"Industry-{code}", label="Отрасль")

    m.save_and_expect_heading("Товары")
    m.grid_row(name)


def test_product(page: Page, code) -> None:
    authorization(page)
    run_product(page, code)
