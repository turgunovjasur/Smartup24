import allure
from playwright.sync_api import Page

from flows.flow_authorization import authorization
from flows.flow_navbar import flow_navigate
from utils.base_page import BasePage


def run_oprsoniki(page: Page, code) -> None:
    m = BasePage(page)
    name = f"oprsoniki-{code}"

    with allure.step("Навигация: Модератор → Опросники"):
        flow_navigate(page, tab="Модератор", name="Опросники")
        m.expect_heading("Опросники")

    with allure.step("Создать: yangi Опросник formasi ochish"):
        m.open_create()
        m.expect_heading("Опросник (Создание)")

    with allure.step(f"Форма: Название = {name}"):
        m.input(label="Название", value=name)

    with allure.step("Сохранить va ro'yxatga qaytish"):
        m.save_and_expect_heading("Опросники")

    with allure.step(f"Qidiruv va ro'yxatda '{name}' tekshirish"):
        m.search(name)
        m.grid_row(name)


@allure.epic("Модератор")
@allure.feature("Опросники")
@allure.story("Создание опросника")
@allure.title("Yangi Опросник yaratish")
def test_bonus(page: Page, code) -> None:
    with allure.step("Tizimga kirish"):
        authorization(page)
    run_oprsoniki(page, code)
