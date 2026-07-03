import allure
from playwright.sync_api import Page

from flows.flow_authorization import authorization
from flows.flow_navbar import flow_navigate
from utils.base_page import BasePage


def run_region(page: Page, code) -> None:
    m = BasePage(page)
    name = f"Region-{code}"

    with allure.step("Навигация: Модератор → Регионы"):
        flow_navigate(page, tab="Модератор", name="Регионы")
        m.expect_heading("Регионы")

    with allure.step("Создать: yangi Регион formasi ochish"):
        m.open_create()
        m.expect_heading("Регион (Создания)")

    with allure.step(f"Форма: Название = {name}, Статус = Активный"):
        m.input(label="Название", value=name)
        m.checkbox(label="Статус", checked=True)

    with allure.step("Сохранить va ro'yxatga qaytish"):
        m.save_and_expect_heading("Регионы")

    with allure.step(f"Qidiruv va ro'yxatda '{name}' tekshirish"):
        m.search(name)
        m.grid_row(name)


@allure.epic("Модератор")
@allure.feature("Регионы")
@allure.story("Создание региона")
@allure.title("Yangi Регион yaratish")
def test_region(page: Page, code) -> None:
    with allure.step("Tizimga kirish"):
        authorization(page)
    run_region(page, code)
