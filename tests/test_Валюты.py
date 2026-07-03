from playwright.sync_api import Page

from flows.flow_authorization import authorization
from flows.flow_navbar import flow_navigate
from utils.base_page import BasePage


def run_valyuta(page: Page, code) -> None:
    """Testcase: valyuta yaratish.

    1. Модератор -> Valyuta ro'yxatini ochish.
    2. "Создать" -> nom/INN/Форма собственности to'ldirish,
    3. Saqlab, ro'yxatда qidirib nom bo'yicha ko'rinishini tekshirish.
    """
    m = BasePage(page)
    name = f"so`m{code}"
    kod = f"{code}"

    flow_navigate(page, tab="Модератор", name="Валюты")
    m.expect_heading("Валюты")

    m.open_create()
    m.expect_heading("Валюта (Создания)")
    m.input(label="Название ", value=name)
    m.input(label="Код", value=kod)
    m.input(label="Базовая денежная единица", value=kod)

    m.save_and_expect_heading("Валюты")

    m.search(name)
    m.grid_row(name)


def test_valyuta(page: Page, code) -> None:
    authorization(page)
    run_valyuta(page, code)
#msdnbfmndnbcdbncdbncvbdmnvbdmvnd