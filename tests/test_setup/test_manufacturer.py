import allure
from playwright.sync_api import Page

from flows.flow_authorization import authorization
from flows.flow_navbar import flow_navigate
from utils.base_page import BasePage


def run_manufacturer(page: Page, code) -> None:
    m = BasePage(page)
    name = f"Manufacturer-{code}"

    with allure.step("Навигация: Модератор → Товары"):
        flow_navigate(page, tab="Модератор", name="Товары")
        m.expect_heading("Товары")

    with allure.step("Производители bo'limiga o'tish"):
        m.click_link("Производители")
        m.expect_heading("Производители")

    with allure.step("Создать: yangi производитель formasi ochish"):
        m.open_create()
        m.expect_heading("Производитель (Создание)")

    with allure.step(f"Форма: Название = {name}"):
        m.input(label="Название", value=name)

    with allure.step("Сохранить va ro'yxatga qaytish"):
        m.save_and_expect_heading("Производители")

    with allure.step(f"Qidiruv va ro'yxatda '{name}' tekshirish"):
        # Ro'yxat sahifalangan bo'lishi mumkin — qidiruvsiz yangi yozuv
        # keyingi sahifada qolib ketadi
        m.search(name)
        m.grid_row(name)


@allure.epic("Модератор")
@allure.feature("Товары")
@allure.story("Производители")
@allure.title("Yangi производитель yaratish")
def test_manufacturer(page: Page, code) -> None:
    with allure.step("Tizimga kirish"):
        authorization(page)
    run_manufacturer(page, code)
