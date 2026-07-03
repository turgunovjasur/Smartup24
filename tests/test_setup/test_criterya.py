import allure
from playwright.sync_api import Page

from flows.flow_authorization import authorization
from flows.flow_navbar import flow_navigate
from utils.base_page import BasePage


def run_criterya(page: Page, code) -> None:
    m = BasePage(page)
    name = f"Criteria-{code}"

    with allure.step("Навигация: Модератор → Критерии"):
        flow_navigate(page, tab="Модератор", name="Критерии")
        m.expect_heading("Критерии")

    with allure.step("Создать: yangi Критерия formasi ochish"):
        m.open_create()
        m.expect_heading("Критерия (Создание)")

    with allure.step(f"Форма: Название = {name}, Название шага = Лид"):
        m.input(label="Название", value=name)
        m.select(option_text="Лид", label="Название шага ")

    with allure.step("Сохранить va ro'yxatga qaytish"):
        m.save_and_expect_heading("Критерии")

    with allure.step(f"Qidiruv va ro'yxatda '{name}' tekshirish"):
        m.search(name)
        m.grid_row(name)


@allure.epic("Модератор")
@allure.feature("Критерии")
@allure.story("Создание критерия")
@allure.title("Yangi Критерий yaratish")
def test_criterya(page: Page, code) -> None:
    with allure.step("Tizimga kirish"):
        authorization(page)
    run_criterya(page, code)
