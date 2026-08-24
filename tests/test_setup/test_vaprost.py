import allure
from playwright.sync_api import Page

from flows.flow_authorization import authorization
from flows.flow_navbar import flow_navigate
from utils.base_page import BasePage


def run_vaprost(page: Page, code) -> None:
    m = BasePage(page)
    name = f"Vaprost{code}"

    with allure.step("Навигация: Модератор → Вопросы"):
        flow_navigate(page, tab="Модератор", name="Вопросы")
        m.expect_heading("Вопросы")

    with allure.step("Создать: yangi Вопрос formasi ochish"):
        m.open_create()
        m.expect_heading("Вопрос (Создание)")

    with allure.step(f"Форма: Название = {name}"):
        m.input(label="Название ", value=name)

    with allure.step("Сохранить va ro'yxatga qaytish"):
        m.save_and_expect_heading("Вопросы")

    with allure.step(f"Qidiruv va ro'yxatda '{name}' tekshirish"):
        m.search(name)
        m.grid_row(name)


@allure.epic("Модератор")
@allure.feature("Вопросы")
@allure.story("Создание вопроса")
@allure.title("Yangi Вопрос yaratish")
def test_vaprost(page: Page, code) -> None:
    with allure.step("Tizimga kirish"):
        authorization(page)
    run_vaprost(page, code)
