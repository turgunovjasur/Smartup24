import random

from playwright.sync_api import Page

from flows.flow_authorization import authorization
from flows.flow_navbar import flow_navigate
from utils.base_page import BasePage


def run_legal_person(page: Page, code) -> None:
    """Testcase: Yangi Юридическое лицо (Юр. лицо) yaratish.

    "Тип Юр. лица" (Поставщик/Клиент) va "Статус" (Активный/...) — ikkalasi ham
    checkbox EMAS, balki ``smt-radio-group`` (bitta variant tanlanadi), shuning uchun
    ``m.radio(option, label=...)`` bilan tanlanadi (MCP bilan tasdiqlangan 2026-07-02).

    1. Модератор -> Юридическое лицо ro'yxatini ochish.
    2. "Создать" -> nom/INN/Форма собственности to'ldirish, "Тип Юр. лица"=Клиент,
       "Статус"=Активный radiolarini tanlash.
    3. Saqlab, ro'yxatда qidirib nom bo'yicha ko'rinishini tekshirish.
    """
    m = BasePage(page)
    name = f"LegalPerson-{code}"
    short_name = f"LP-{code}"
    tin = random.randint(100000000, 999999999)
    # run_form_of_ownership zanjirda aynan shu nom bilan forma yaratadi
    form = f"MCHJ-{code}"

    flow_navigate(page, tab="Модератор", name="Юридическое лицо")
    m.expect_heading("Юридическое лицо")

    m.open_create()
    m.expect_heading("Юр. Лицо (Создания)")
    m.input(label="Юр. лица название", value=name)
    m.input(label="Краткое название", value=short_name)
    m.input(label="ИНН", value=tin)
    m.select(option_text=form, label="Форма собственности")
    m.radio("Клиент", label="Тип Юр. лица")
    m.radio("Активный", label="Статус")
    m.click_button("Характеристика товаров")
    m.select(f"Industry-{code}", label="Отрасль")

    m.save_and_expect_heading("Юридическое лицо")

    m.search(name)
    m.grid_row(name)


def test_legal_person(page: Page, code) -> None:
    authorization(page)
    run_legal_person(page, code)
