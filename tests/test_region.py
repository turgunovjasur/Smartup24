from playwright.sync_api import Page

from flows.flow_authorization import authorization
from flows.flow_navbar import flow_navigate
from utils.base_page import BasePage


def run_region(page: Page, code) -> None:
    """Testcase: Yangi region (Регион) yaratish.

    Boshqa modulda base funksiyalar ishlashini tasdiqlaydi: Регионы to'g'ridan-to'g'ri
    menyudan ochiladi (sub-nav emas) va "Статус" bu yerda ``smt-switch`` (radio emas).

    1. Модератор -> Регионы ro'yxatini ochish.
    2. "Создать" -> "Название" to'ldirish, "Статус" switchini yoqilgan holatda tasdiqlash.
    3. Saqlab, ro'yxatда qidirib nom bo'yicha ko'rinishini tekshirish.
    """
    m = BasePage(page)
    name = f"Region-{code}"

    flow_navigate(page, tab="Модератор", name="Регионы")
    m.expect_heading("Регионы")

    m.open_create()
    m.expect_heading("Регион (Создания)")
    m.input(label="Название", value=name)
    m.checkbox(label="Статус", checked=True)   # smt-switch — toggle funksiyasini tekshiradi
    m.save_and_expect_heading("Регионы")

    m.search(name)
    m.grid_row(name)


def test_region(page: Page, code) -> None:
    authorization(page)
    run_region(page, code)
