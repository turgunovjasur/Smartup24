import allure
from playwright.sync_api import Page

from flows.flow_authorization import authorization
from flows.flow_navbar import flow_navigate
from utils.base_page import BasePage


def run_territory(page: Page, code) -> None:
    m = BasePage(page)
    name = f"territory-{code}"

    with allure.step("Навигация: Модератор → Tерритории"):
        flow_navigate(page, tab="Модератор", name="Tерритории")
        m.expect_heading("Tерритории")

    with allure.step("Создать: yangi Tерритория formasi ochish"):
        m.open_create()
        m.expect_heading("Tерритория (Создания)")

    with allure.step(f"Форма: Название = {name}"):
        m.input(label="Название", value=name)

    with allure.step("Сохранить va ro'yxatga qaytish"):
        m.save_and_expect_heading("Tерритории")

    with allure.step(f"Qidiruv va ro'yxatda '{name}' tekshirish"):
        m.search(name)
        m.grid_row(name)


@allure.epic("Модератор")
@allure.feature("Tерритории")
@allure.story("Создание территории")
@allure.title("Yangi Tерритория yaratish")
def test_territory(page: Page, code) -> None:
    with allure.step("Tizimga kirish"):
        authorization(page)
    run_territory(page, code)
