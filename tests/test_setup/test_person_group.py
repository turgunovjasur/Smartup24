"""Характеристики (Юр. лица) — basic create.

Юридическое лицо ro'yxati sarlavhasidagi "Характеристики (Юр. лица)" sub-nav
bo'limi (biruni ``person_group_list``). Sodda справочnik: Статус switch, Код,
Название *. Форма собственности bilan bir xil
naqsh — Юридическое лицо bo'limidan chiqadi.
"""
import allure
from playwright.sync_api import Page

from flows.flow_authorization import authorization
from flows.flow_navbar import flow_navigate
from utils.base_page import BasePage


def run_person_group(page: Page, code) -> None:
    m = BasePage(page)
    name = f"PersonGroup-{code}"

    with allure.step("Навигация: Модератор → Юридическое лицо"):
        flow_navigate(page, tab="Модератор", name="Юридическое лицо")
        m.expect_heading("Юридическое лицо")

    with allure.step("Характеристики (Юр. лица) bo'limiga o'tish"):
        m.click_link("Характеристики (Юр. лица)")
        m.expect_heading("Характеристики (Юр. лица)")

    with allure.step("Создать: yangi характеристика formasi ochish"):
        m.open_create()
        m.expect_heading("Характеристика Юр. лица")

    with allure.step(f"Форма: Название = {name}, Статус = Активный"):
        m.checkbox(label="Статус", checked=True)
        m.input(label="Название", value=name)

    with allure.step("Сохранить va ro'yxatga qaytish"):
        m.save_and_expect_heading("Характеристики (Юр. лица)")

    with allure.step(f"Qidiruv va ro'yxatda '{name}' tekshirish"):
        m.search(name)
        m.grid_row(name)


@allure.epic("Модератор")
@allure.feature("Юридическое лицо")
@allure.story("Характеристики (Юр. лица)")
@allure.title("Yangi Юр. лицо характеристикаси yaratish")
def test_person_group(page: Page, code) -> None:
    with allure.step("Tizimga kirish"):
        authorization(page)
    run_person_group(page, code)
