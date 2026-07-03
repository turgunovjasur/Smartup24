import random

from playwright.sync_api import Page

from flows.flow_authorization import authorization
from flows.flow_navbar import flow_navigate
from utils.base_page import BasePage


def run_shablon(page: Page, code) -> None:
    """Testcase: shablon (otechetov) yaratish.


    1. Модератор -> Шаблоны отчетов по опросам ro'yxatini ochish.
    2. "Создать" -> nom/INN/Форма собственности to'ldirish,
       "Статус"=Активный radiolarini tanlash.
    3. Saqlab, ro'yxatда qidirib nom bo'yicha ko'rinishini tekshirish.
    """
    m = BasePage(page)
    name = f"Shablon-{code}"

    flow_navigate(page, tab="Модератор", name="Шаблоны отчетов по опросам")
    m.expect_heading("Шаблоны отчетов по опросам")

    m.open_create()
    m.expect_heading("Шаблон отчета по опросам (Создание)")
    m.input(label="Название", value=name)

    m.save_and_expect_heading("Шаблоны отчетов по опросам")

    m.search(name)
    m.grid_row(name)


def test_shablon(page: Page, code) -> None:
    authorization(page)
    run_shablon(page, code)