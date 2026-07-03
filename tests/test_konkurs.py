from playwright.sync_api import Page

from flows.flow_authorization import authorization
from flows.flow_navbar import flow_navigate
from tests.test_region import run_region
from utils.base_page import BasePage


def run_konkurs(page: Page, code) -> None:
    """Testcase: Yangi Конкурс (konkurs) yaratish.

    1. Модератор -> Конкурсы ro'yxatini ochish.
    2. "Создать" -> Название, Количество рангов (rank_count) to'ldirish, Регион tanlash.
    3. Saqlab, ro'yxatда qidirib nom bo'yicha ko'rinishini tekshirish.

    Eslatma: dinamik ``input[name="ng.formN.*"]`` ISHLATILMAYDI — field'lar
    ko'rinadigan label orqali topiladi (BasePage).
    """
    m = BasePage(page)
    name = f"konkurs-{code}"
    region = f"Region-{code}"

    flow_navigate(page, tab="Модератор", name="Конкурсы")
    m.expect_heading("Конкурсы")

    m.open_create()
    m.expect_heading("Конкурсы (Создания)")
    m.input(label="Название", value=name)
    m.input(label="Количество победителей", value=4)
    m.select(option_text=region, label="Регион")

    m.save_and_expect_heading("Конкурсы")

    m.search(name)
    m.grid_row(name)


def test_konkurs(page: Page, code) -> None:
    authorization(page)
    # Регион tree-select'da tanlanadigan f"Region-{code}" avval yaratilgan bo'lishi
    # kerak — test_all zanjirida run_region buni ta'minlaydi, standalone'da o'zimiz.
    run_region(page, code)
    run_konkurs(page, code)
