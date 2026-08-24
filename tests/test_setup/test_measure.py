"""Единицы измерения — basic create.

Товары ro'yxati sarlavhasidagi "Единицы измерения" sub-nav bo'limi (biruni
``measure_list``). Sodda справочnik: Статус switch, Код, Название *, Краткое
название, "Знаков после запятой *" (default "0", to'ldirilgan) — MCP
tasdiqlangan 2026-08-21. ``run_measure`` yaratilgan nomni qaytaradi (Услуги
formasidagi majburiy "Ед. изм." shu birlikni tanlaydi).
"""
import allure
from playwright.sync_api import Page

from flows.flow_authorization import authorization
from flows.flow_navbar import flow_navigate
from utils.base_page import BasePage


def run_measure(page: Page, code) -> str:
    m = BasePage(page)
    name = f"Measure-{code}"

    with allure.step("Навигация: Модератор → Товары"):
        flow_navigate(page, tab="Модератор", name="Товары")
        m.expect_heading("Товары")

    with allure.step("Единицы измерения bo'limiga o'tish"):
        m.click_link("Единицы измерения")
        m.expect_heading("Единицы измерения")

    with allure.step("Создать: yangi o'lchov birligi formasi ochish"):
        m.open_create()
        m.expect_heading("Единица измерения")

    with allure.step(f"Форма: Название = {name}, Краткое название = mu{code} (Знаков после запятой = default 0)"):
        # "Краткое название" bo'sh qolsa server uni Название'dan avto-to'ldirib
        # ~10 belgigacha kesadi va dublikat beradi — qisqa unikal qiymat beramiz
        #.
        m.input(smtid="name", value=name)
        m.input(smtid="short_name", value=f"mu{code}")

    with allure.step("Сохранить va ro'yxatga qaytish"):
        m.save_and_expect_heading("Единицы измерения")

    with allure.step(f"Qidiruv va ro'yxatda '{name}' tekshirish"):
        m.search(name)
        m.grid_row(name)

    return name


@allure.epic("Модератор")
@allure.feature("Товары")
@allure.story("Единицы измерения")
@allure.title("Yangi o'lchov birligi yaratish")
def test_measure(page: Page, code) -> None:
    with allure.step("Tizimga kirish"):
        authorization(page)
    run_measure(page, code)
