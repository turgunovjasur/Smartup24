from playwright.sync_api import Page

from flows.flow_authorization import authorization
from flows.flow_navbar import flow_navigate
from utils.base_page import BasePage


def run_form_of_ownership(page: Page, code) -> None:
    """Testcase: Yangi tashkiliy-huquqiy shakl (Организационно-правовая форма) yaratish.

    1. Модератор -> Юридическое лицо ro'yxatini ochish.
    2. "Организационно-правовые формы" sub-nav bo'limiga o'tish.
    3. "Создать" -> "Название" va "Краткое название" maydonlarini to'ldirish,
       "Статус" switchini yoqilgan holatda tasdiqlash ("Место расположение" default "Правый").
    4. Saqlab, ro'yxatda nom bo'yicha ko'rinishini tekshirish.
    """
    m = BasePage(page)
    name = f"FormOfOwnership-{code}"
    short_name = f"FOO-{code}"

    flow_navigate(page, tab="Модератор", name="Юридическое лицо")
    m.expect_heading("Юридическое лицо")
    m.click_link("Организационно-правовые формы")
    m.expect_heading("Организационно-правовые формы")

    m.open_create()
    m.expect_heading("Организационно-правовая форма (создание)")
    m.input(label="Название", value=name)
    m.input(label="Краткое название", value=short_name)
    m.checkbox(label="Статус", checked=True)   # smt-switch — default Активный
    m.save_and_expect_heading("Организационно-правовые формы")

    m.grid_row(name)


def test_form_of_ownership(page: Page, code) -> None:
    authorization(page)
    run_form_of_ownership(page, code)
