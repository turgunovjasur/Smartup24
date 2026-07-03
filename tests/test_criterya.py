from playwright.sync_api import Page

from flows.flow_authorization import authorization
from flows.flow_navbar import flow_navigate
from utils.base_page import BasePage


def run_criterya(page: Page, code) -> None:
    """Testcase: "Criteria" yaratish.

    1. Модератор -> Criteria->  ro'yxatini ochish.
    2. "Создать" -> "Название" maydonini to'ldirish.
    3. Saqlab, ro'yxatda ko'rinishini tekshirish.
    """
    m = BasePage(page)
    name = f"Criteria-{code}"

    flow_navigate(page, tab="Модератор", name="Критерии")
    m.expect_heading("Критерии")

    m.open_create()
    m.expect_heading("Критерия (Создание)")
    m.input(label="Название", value=name)
    m.select(option_text="Лид", label="Название шага ")
    m.save_and_expect_heading("Критерии")

    m.search(name)
    m.grid_row(name)


def test_criterya(page: Page, code) -> None:
    authorization(page)
    run_criterya(page, code)
