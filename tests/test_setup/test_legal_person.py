import random

import allure
from playwright.sync_api import Page

from flows.flow_authorization import authorization
from flows.flow_navbar import flow_navigate
from utils.base_page import BasePage


def run_legal_person(page: Page, code) -> None:
    m = BasePage(page)
    name = f"LegalPerson-{code}"
    short_name = f"LP-{code}"
    tin = random.randint(100000000, 999999999)
    form = f"MCHJ-{code}"

    with allure.step("Навигация: Модератор → Юридическое лицо"):
        flow_navigate(page, tab="Модератор", name="Юридическое лицо")
        m.expect_heading("Юридическое лицо")

    with allure.step("Создать: yangi Юр. лицо formasi ochish"):
        m.open_create()
        m.expect_heading("Юр. Лицо (Создания)")

    with allure.step(f"Форма asosiy: Юр. лица название = {name}, ИНН = {tin}"):
        m.input(label="Юр. лица название", value=name)
        m.input(label="Краткое название", value=short_name)
        m.input(label="ИНН", value=tin)

    with allure.step(f"Форма: Форма собственности = {form}, Тип = Клиент, Статус = Активный"):
        m.select(option_text=form, label="Форма собственности")
        m.radio("Клиент", label="Тип Юр. лица")
        m.radio("Активный", label="Статус")

    with allure.step(f"Характеристика товаров: Отрасль = Industry-{code}"):
        m.click_button("Характеристика товаров")
        m.select(f"Industry-{code}", label="Отрасль")

    with allure.step("Сохранить va ro'yxatga qaytish"):
        m.save_and_expect_heading("Юридическое лицо")

    with allure.step(f"Qidiruv va ro'yxatda '{name}' tekshirish"):
        m.search(name)
        m.grid_row(name)


@allure.epic("Модератор")
@allure.feature("Юридическое лицо")
@allure.story("Создание юридического лица")
@allure.title("Yangi Юр. лицо yaratish")
def test_legal_person(page: Page, code) -> None:
    with allure.step("Tizimga kirish"):
        authorization(page)
    run_legal_person(page, code)
