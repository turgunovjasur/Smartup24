"""Типы упаковок — basic create.

Товары ro'yxati sarlavhasidagi "Типы упаковок" sub-nav bo'limi (biruni
``box_type_list``). Sodda справочnik: Статус switch, Код, Название *,
Альтернативное название, Краткое название (MCP tasdiqlangan 2026-08-21).
Производители bilan bir xil naqsh — Товары bo'limidan chiqadi.
"""
import allure
from playwright.sync_api import Page

from flows.flow_authorization import authorization
from flows.flow_navbar import flow_navigate
from utils.base_page import BasePage


def run_box_type(page: Page, code) -> None:
    m = BasePage(page)
    name = f"BoxType-{code}"

    with allure.step("Навигация: Модератор → Товары"):
        flow_navigate(page, tab="Модератор", name="Товары")
        m.expect_heading("Товары")

    with allure.step("Типы упаковок bo'limiga o'tish"):
        m.click_link("Типы упаковок")
        m.expect_heading("Типы упаковок")

    with allure.step("Создать: yangi упаковка turi formasi ochish"):
        m.open_create()
        m.expect_heading("Типы упаковок (создание)")

    with allure.step(f"Форма: Название = {name}, Краткое название = bt{code}"):
        # "Краткое название" bo'sh qolsa server uni Название'dan avto-to'ldirib
        # ~10 belgigacha kesadi va dublikat ("уже используется") beradi — qisqa
        # unikal qiymat beramiz (MCP tasdiqlangan 2026-08-21).
        m.input(smtid="name", value=name)
        m.input(smtid="short_name", value=f"bt{code}")

    with allure.step("Сохранить va ro'yxatga qaytish"):
        m.save_and_expect_heading("Типы упаковок")

    with allure.step(f"Qidiruv va ro'yxatda '{name}' tekshirish"):
        m.search(name)
        m.grid_row(name)


@allure.epic("Модератор")
@allure.feature("Товары")
@allure.story("Типы упаковок")
@allure.title("Yangi упаковка turi yaratish")
def test_box_type(page: Page, code) -> None:
    with allure.step("Tizimga kirish"):
        authorization(page)
    run_box_type(page, code)
