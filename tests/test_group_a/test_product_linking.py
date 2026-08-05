import re

import allure
from playwright.sync_api import Page

from flows.flow_authorization import authorization
from flows.flow_navbar import flow_navigate
from utils.base_page import BasePage


def run_product_linking(page: Page, code, product_name=None) -> str:
    """Group A: supplier-{code} ga tovar biriktiradi, uni 'В наличие' qiladi
    va 'Цена по умолчанию' bo'yicha narx o'rnatadi (run_supplier dan keyin).

    ``product_name`` berilsa (masalan run_product yaratgan tovar) aynan o'sha
    biriktiriladi — run_zakaz keyin klient katalogida shu tovarni qidiradi.
    Berilmasa ro'yxatdagi birinchi product-* olinadi. Haqiqiy biriktirilgan
    tovar nomini qaytaradi."""
    m = BasePage(page)
    supplier_name = f"supplier-{code}"

    with allure.step("Навигация: Модератор → Поставщики"):
        flow_navigate(page, tab="Модератор", name="Поставщики")
        m.expect_heading("Поставщики")

    with allure.step(f"'{supplier_name}' Просмотр formasini ochish"):
        m.search(supplier_name)
        m.click_grid_row(supplier_name)
        m.click_button("Просмотреть")
        m.expect_heading("Поставщик (Просмотр)")

    with allure.step("Товары → Прикрепить formasini ochish"):
        m.click_button("Товары")
        m.click_button("Прикрепить")
        m.expect_heading(f"Поставщик:{supplier_name}")

    with allure.step(f"Доступные ro'yxatidan tovarni biriktirish ({product_name or 'birinchi product-*'})"):
        m.search(product_name or "product-")
        row = m.grid_row(product_name or "product-")
        product_name = re.search(r"product-\S+", row.inner_text()).group(0)
        # Qator ichidagi ikonka tugma — aria-label="Прикрепить"
        row.get_by_role("button", name="Прикрепить").click()

    with allure.step("Выбранные ro'yxatida tekshirish va Сохранить"):
        m.click_button("Выбранные")
        m.grid_row(product_name)
        m.click_button("Сохранить")
        m.confirm("да")
        m.expect_heading("Поставщик (Просмотр)")

    with allure.step("Товары ro'yxatida tovarni 'В наличие' qilish"):
        m.click_button("Товары")
        m.click_grid_row(product_name)
        m.click_button("В наличие")
        m.confirm("да")

    with allure.step("Тип цены → Цена по умолчанию → Установить цену"):
        m.click_button("Тип цены")
        m.click_grid_row("Цена по умолчанию")
        m.click_button("Установить цену")
        m.expect_heading("Установка цен")

    with allure.step("Narx = 100000 va Сохранить"):
        price_row = m.grid_row(product_name)
        price_input = price_row.locator("input[type=number]").first
        price_input.click()
        price_input.fill("100000")
        m.save()

    return product_name


@allure.epic("Модератор")
@allure.feature("Group A")
@allure.story("Прикрепление товара")
@allure.title("Group A: Поставщикка tovar biriktirish va narx o'rnatish")
def test_product_linking(page: Page, code) -> None:
    with allure.step("Tizimga kirish"):
        authorization(page)
    run_product_linking(page, code)
