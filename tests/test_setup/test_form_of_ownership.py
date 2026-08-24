import allure
from playwright.sync_api import Page

from flows.flow_authorization import authorization
from flows.flow_navbar import flow_navigate
from utils.base_page import BasePage


def run_form_of_ownership(page: Page, code) -> None:
    m = BasePage(page)
    name = f"MCHJ-{code}"
    short_name = f"MCHJ-{code}"

    with allure.step("Навигация: Модератор → Юридическое лицо"):
        flow_navigate(page, tab="Модератор", name="Юридическое лицо")
        m.expect_heading("Юридическое лицо")

    with allure.step("Организационно-правовые формы bo'limiga o'tish"):
        m.click_link("Организационно-правовые формы")
        m.expect_heading("Организационно-правовые формы")

    with allure.step("Создать: yangi forma yaratish formasi ochish"):
        m.open_create()
        m.expect_heading("Организационно-правовая форма (создание)")

    with allure.step(f"Форма: Название = {name}, Краткое название = {short_name}, Статус = Активный"):
        m.input(label="Название", value=name)
        m.input(label="Краткое название", value=short_name)
        m.checkbox(label="Статус", checked=True)

    with allure.step("Сохранить va ro'yxatga qaytish"):
        m.save_and_expect_heading("Организационно-правовые формы")

    with allure.step(f"Qidiruv va ro'yxatda '{name}' tekshirish"):
        # Ro'yxat sahifalangan (50 tadan ortiq yozuv bo'lishi mumkin) —
        # qidiruvsiz yangi yozuv keyingi sahifada qolib ketadi
        m.search(name)
        m.grid_row(name)


@allure.epic("Модератор")
@allure.feature("Юридическое лицо")
@allure.story("Организационно-правовые формы")
@allure.title("Yangi tashkiliy-huquqiy shakl yaratish")
def test_form_of_ownership(page: Page, code) -> None:
    with allure.step("Tizimga kirish"):
        authorization(page)
    run_form_of_ownership(page, code)
