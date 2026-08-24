"""Торговые точки — basic create.

Клиенты ro'yxati sarlavhasidagi "Торговые точки" sub-nav bo'limi (biruni
``outlet_list``). Форма ota Клиентга bog'liq: "Юр. лица название *", "Краткое
название *", "Клиент *" (majburiy select — smtid=``client_id``; navbar'dagi
"Клиент" tugmasi bilan to'qnashmaslik uchun smtid ishlatiladi), Статус radio +
Адрес tab (Регион/телефон/адрес, ixtiyoriy) — MCP tasdiqlangan 2026-08-21.

Majburiy "Клиент" uchun avval ``ensure_refs`` + ``run_client`` bilan mijoz
yaratiladi (muhitda oldindan bor narsaga tayanmaymiz). ``client_name`` berilsa
(runner zanjirida) mavjud mijoz qayta ishlatiladi — dublikat nom yaratilmaydi.
"""
import allure
from playwright.sync_api import Page

from flows.flow_authorization import authorization
from flows.flow_navbar import flow_navigate
from tests.test_setup.test_client import run_client
from tests.test_setup.test_supplier import ensure_refs
from utils.base_page import BasePage


def run_outlet(page: Page, code, client_name=None) -> None:
    m = BasePage(page)
    name = f"Outlet-{code}"
    if client_name is None:
        ensure_refs(page, code)
        client_name = run_client(page, code)["name"]

    with allure.step("Навигация: Модератор → Клиенты"):
        flow_navigate(page, tab="Модератор", name="Клиенты")
        m.expect_heading("Клиенты")

    with allure.step("Торговые точки bo'limiga o'tish"):
        m.click_link("Торговые точки")
        m.expect_heading("Торговые точки")

    with allure.step("Создать: yangi savdo nuqtasi formasi ochish"):
        m.open_create()
        m.expect_heading("Торговая точка (Создания)")

    with allure.step(f"Форма: Название = {name}, Клиент = {client_name}"):
        m.input(smtid="name", value=name)
        m.input(smtid="short_name", value=name)
        m.select(client_name, smtid="client_id")

    with allure.step("Сохранить va ro'yxatga qaytish"):
        m.save_and_expect_heading("Торговые точки")

    with allure.step(f"Qidiruv va ro'yxatda '{name}' tekshirish"):
        m.search(name)
        m.grid_row(name)


@allure.epic("Модератор")
@allure.feature("Клиент")
@allure.story("Торговые точки")
@allure.title("Yangi savdo nuqtasi (Торговая точка) yaratish")
def test_outlet(page: Page, code) -> None:
    with allure.step("Tizimga kirish"):
        authorization(page)
    run_outlet(page, code)
