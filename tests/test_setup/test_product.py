import allure
from playwright.sync_api import Page

from flows.flow_authorization import authorization
from flows.flow_navbar import flow_navigate
from utils.base_page import BasePage


def run_product(page: Page, code) -> None:
    m = BasePage(page)
    name = f"product-{code}"

    with allure.step("Навигация: Модератор → Товары"):
        flow_navigate(page, tab="Модератор", name="Товары")
        m.expect_heading("Товары")

    with allure.step("Создать: yangi Продукт formasi ochish"):
        m.open_create()
        m.expect_heading("Продукт (создание)")

    with allure.step("Форма asosiy: Название, Краткое название, Код"):
        m.input(label="Название", value=name)
        m.input(label="Краткое название", value=f"pr-{code}")
        m.input(label="Код", value=f"code-{code}")

    with allure.step(f"Форма: Производитель = Manufacturer-{code}, measure = кг"):
        m.select(f"Manufacturer-{code}", label="Производитель")
        m.select("кг", label="measure")

    with allure.step(f"Характеристика: Отрасль = Industry-{code}"):
        m.click_button("Характеристика")
        m.select(f"Industry-{code}", label="Отрасль")

    with allure.step("Сохранить va ro'yxatga qaytish"):
        m.save_and_expect_heading("Товары")

    with allure.step(f"Ro'yxatda '{name}' ko'rinishini tekshirish"):
        m.grid_row(name)


@allure.epic("Модератор")
@allure.feature("Товары")
@allure.story("Создание продукта")
@allure.title("Yangi Продукт yaratish")
def test_product(page: Page, code) -> None:
    with allure.step("Tizimga kirish"):
        authorization(page)
    run_product(page, code)
