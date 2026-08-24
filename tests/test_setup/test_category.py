import allure
from playwright.sync_api import Page

from flows.flow_authorization import authorization
from flows.flow_navbar import flow_navigate
from utils.base_page import BasePage


def run_category(page: Page, code) -> None:
    m = BasePage(page)
    name = f"Category-{code}"

    with allure.step("Навигация: Модератор → Товары"):
        flow_navigate(page, tab="Модератор", name="Товары")
        m.expect_heading("Товары")

    with allure.step("Характеристика товаров bo'limiga o'tish"):
        m.click_link("Характеристика товаров")
        m.expect_heading("Характеристика товаров")

    with allure.step("Категория guruhini ochish va Подтипы ga o'tish"):
        m.click_grid_row("Категория")
        m.click_button("Подтипы")
        m.expect_heading("Категория")

    with allure.step("Создать: yangi Категория подтипи formasi ochish"):
        m.open_create()
        m.expect_heading("Характеристика товаров (создание)")

    with allure.step(f"Форма: Название = {name}"):
        m.input(label="Название", value=name)

    with allure.step("Сохранить va ro'yxatga qaytish"):
        m.save_and_expect_heading("Категория")

    with allure.step(f"Qidiruv va ro'yxatda '{name}' tekshirish"):
        # Ro'yxat sahifalangan (50 tadan ortiq yozuv bor) — qidiruvsiz yangi
        # yozuv 2-sahifada qolib ketishi mumkin
        m.search(name)
        m.grid_row(name)


@allure.epic("Модератор")
@allure.feature("Товары")
@allure.story("Характеристика товаров — Категория")
@allure.title("Категория учун yangi подтип yaratish")
def test_category(page: Page, code) -> None:
    with allure.step("Tizimga kirish"):
        authorization(page)
    run_category(page, code)
