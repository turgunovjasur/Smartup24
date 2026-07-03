import allure
from playwright.sync_api import Page

from flows.flow_authorization import authorization
from flows.flow_navbar import flow_navigate
from utils.base_page import BasePage


def run_valyuta(page: Page, code) -> None:
    m = BasePage(page)
    name = f"so`m{code}"
    kod = f"{code}"

    with allure.step("Навигация: Модератор → Валюты"):
        flow_navigate(page, tab="Модератор", name="Валюты")
        m.expect_heading("Валюты")

    with allure.step("Создать: yangi Валюта formasi ochish"):
        m.open_create()
        m.expect_heading("Валюта (Создания)")

    with allure.step(f"Форма: Название = {name}, Код = {kod}, Базовая денежная единица = {kod}"):
        m.input(label="Название ", value=name)
        m.input(label="Код", value=kod)
        m.input(label="Базовая денежная единица", value=kod)

    with allure.step("Сохранить va ro'yxatga qaytish"):
        m.save_and_expect_heading("Валюты")

    with allure.step(f"Qidiruv va ro'yxatda '{name}' tekshirish"):
        m.search(name)
        m.grid_row(name)


@allure.epic("Модератор")
@allure.feature("Валюты")
@allure.story("Создание валюты")
@allure.title("Yangi Валюта yaratish")
def test_valyuta(page: Page, code) -> None:
    with allure.step("Tizimga kirish"):
        authorization(page)
    run_valyuta(page, code)
