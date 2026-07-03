import allure
from playwright.sync_api import Page

from flows.flow_authorization import authorization
from flows.flow_navbar import flow_navigate
from utils.base_page import BasePage


def run_bonus(page: Page, code) -> None:
    m = BasePage(page)
    name = f"bonus-{code}"

    with allure.step("Навигация: Модератор → Бонусная система"):
        flow_navigate(page, tab="Модератор", name="Бонусная система")
        m.expect_heading("Бонусная система")

    with allure.step("Создать: yangi Бонусная система formasi ochish"):
        m.open_create()
        m.expect_heading("Создать бонусную систему")

    with allure.step(f"Форма: Название = {name}, Значение = 5, Начало = 01.07.2026, Конец = 30.07.2026"):
        m.input(label="Название", value=name)
        m.input(label="Значение", value="5")
        m.input(label="Начало", value="01.07.2026")
        m.input(label="Конец", value="30.07.2026")

    with allure.step("Сохранить va ro'yxatga qaytish"):
        m.save_and_expect_heading("Бонусная система")

    with allure.step(f"Qidiruv va ro'yxatda '{name}' tekshirish"):
        m.search(name)
        m.grid_row(name)


@allure.epic("Модератор")
@allure.feature("Бонусная система")
@allure.story("Создание бонусной системы")
@allure.title("Yangi Бонусная система yaratish")
def test_bonus(page: Page, code) -> None:
    with allure.step("Tizimga kirish"):
        authorization(page)
    run_bonus(page, code)
