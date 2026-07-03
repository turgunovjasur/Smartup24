import allure
from playwright.sync_api import Page

from flows.flow_authorization import authorization
from flows.flow_navbar import flow_navigate
from tests.test_setup.test_region import run_region
from utils.base_page import BasePage


def run_konkurs(page: Page, code) -> None:
    m = BasePage(page)
    name = f"konkurs-{code}"
    region = f"Region-{code}"

    with allure.step("Навигация: Модератор → Конкурсы"):
        flow_navigate(page, tab="Модератор", name="Конкурсы")
        m.expect_heading("Конкурсы")

    with allure.step("Создать: yangi Конкурс formasi ochish"):
        m.open_create()
        m.expect_heading("Конкурсы (Создания)")

    with allure.step(f"Форма: Название = {name}, Количество победителей = 4, Регион = {region}"):
        m.input(label="Название", value=name)
        m.input(label="Количество победителей", value=4)
        m.select(option_text=region, label="Регион")

    with allure.step("Сохранить va ro'yxatga qaytish"):
        m.save_and_expect_heading("Конкурсы")

    with allure.step(f"Qidiruv va ro'yxatda '{name}' tekshirish"):
        m.search(name)
        m.grid_row(name)


@allure.epic("Модератор")
@allure.feature("Конкурсы")
@allure.story("Создание конкурса")
@allure.title("Yangi Конкурс yaratish")
def test_konkurs(page: Page, code) -> None:
    with allure.step("Tizimga kirish"):
        authorization(page)
    with allure.step("Oldindan: Region yaratish (test_konkurs uchun)"):
        run_region(page, code)
    run_konkurs(page, code)
