import random

from playwright.sync_api import Page

from flows.flow_authorization import authorization
from flows.flow_navbar import flow_navigate
from utils.base_page import BasePage


def run_supplier(page: Page, code) -> None:
    """Testcase: Yangi Postavshik (Юр. лицо) yaratish.

    "Тип Юр. лица" (Поставщик/Клиент) va "Статус" (Активный/...) — ikkalasi ham
    checkbox EMAS, balki ``smt-radio-group`` (bitta variant tanlanadi), shuning uchun
    ``m.radio(option, label=...)`` bilan tanlanadi (MCP bilan tasdiqlangan 2026-07-02).

    1. Модератор -> Поставщики ro'yxatini ochish.
    2. "Создать" -> nom/INN/Форма собственности to'ldirish, "Тип Юр. лица"=Поставщик,
       "Статус"=Активный radiolarini tanlash.
    3. Saqlab, ro'yxatда qidirib nom bo'yicha ko'rinishini tekshirish.
    """
    m = BasePage(page)
    name = f"Supplier-{code}"
    short_name = f"Sup-{code}"
    tin = random.randint(100000000, 999999999)
    form = f"FormOfOwnership-{code}"

    flow_navigate(page, tab="Модератор", name="Поставщики")
    m.expect_heading("Поставщики")

    m.open_create()
    m.expect_heading("Юр. Лицо (Создания)")
    m.input(label="Юр. лица название", value=name)
    m.input(label="Краткое название", value=short_name)
    m.input(label="ИНН", value=tin)
    m.select(option_text=form, label="Форма собственности")
    m.radio("Поставщик", label="Тип Юр. лица")
    m.radio("Активный", label="Статус")

    m.save_and_expect_heading("Поставщики")

    m.search(name)
    m.grid_row(name)


def test_supplier(page: Page, code) -> None:
    authorization(page)
    run_supplier(page, code)
