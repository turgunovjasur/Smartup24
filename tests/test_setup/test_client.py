import random

import allure
from playwright.sync_api import Page

from flows.flow_authorization import authorization
from flows.flow_navbar import flow_navigate
from utils.base_page import BasePage


def run_client(page: Page, code) -> None:
    m = BasePage(page)
    name = f"client-{code}"
    short_name = f"client-{code}"
    tin = random.randint(100000000, 999999999)

    with allure.step("Навигация: Модератор → Клиенты"):
        flow_navigate(page, tab="Модератор", name="Клиенты")
        m.expect_heading("Клиенты")

    with allure.step("Создать: yangi Клиент formasi ochish"):
        m.open_create()
        m.expect_heading("Юр. Лицо (Создания)")

    with allure.step(f"Форма asosiy: Юр. лица название = {name}, ИНН = {tin}"):
        m.input(label="Юр. лица название", value=name)
        m.input(label="Краткое название", value=short_name)
        m.input(label="ИНН", value=tin)

    with allure.step(f"Форма: Форма собственности = MCHJ-1, Тип = Клиент, Регион = Region-{code}"):
        m.select(option_text='MCHJ-1', label="Форма собственности")
        m.radio("Клиент", label="Тип Юр. лица")
        m.select(option_text=f"Region-{code}", label="Регион")

    with allure.step(f"Характеристика товаров: Отрасль = Industry-{code}"):
        m.click_button("Характеристика товаров")
        m.select(f"Industry-{code}", label="Отрасль")

    with allure.step("Сохранить va ro'yxatga qaytish"):
        m.save_and_expect_heading("Клиенты")

    with allure.step(f"Qidiruv va ro'yxatda '{name}' tekshirish"):
        m.search(name)
        m.grid_row(name)


@allure.epic("Модератор")
@allure.feature("Клиенты")
@allure.story("Создание клиента")
@allure.title("Yangi Клиент (Юр. лицо) yaratish")
def test_client(page: Page, code) -> None:
    with allure.step("Tizimga kirish"):
        authorization(page)
    run_client(page, code)
