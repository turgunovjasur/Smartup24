import random

import allure
from playwright.sync_api import Page

from flows.flow_authorization import authorization
from flows.flow_navbar import flow_navigate
from utils.base_page import BasePage


def run_client(page: Page, code, name=None, status=None) -> dict:
    """Yangi Клиент yaratadi. ``name`` berilmasa client-{code}; ``status``
    berilsa shu status radiosi tanlanadi. Yaratilgan qiymatlarni qaytaradi."""
    m = BasePage(page)
    if name is None:
        name = f"client-{code}"
    tin = random.randint(100000000, 999999999)
    form = f"MCHJ-{code}"

    with allure.step("Навигация: Модератор → Клиенты"):
        flow_navigate(page, tab="Модератор", name="Клиенты")
        m.expect_heading("Клиенты")

    with allure.step("Создать: yangi Клиент formasi ochish"):
        m.open_create()
        m.expect_heading("Юр. Лицо (Создания)")

    with allure.step(f"Форма asosiy: Юр. лица название = {name}, ИНН = {tin}"):
        m.input(label="Юр. лица название", value=name)
        m.input(label="Краткое название", value=name)
        m.input(label="ИНН", value=tin)

    with allure.step(f"Форма: Форма собственности = {form}, Тип = Клиент, Регион = Region-{code}"):
        m.select(option_text=form, label="Форма собственности")
        m.radio("Клиент", label="Тип Юр. лица")
        if status is not None:
            m.radio(status, label="Статус")
        m.select(option_text=f"Region-{code}", label="Регион")

    with allure.step(f"Характеристика товаров: Отрасль = Industry-{code}"):
        m.click_button("Характеристика товаров")
        m.select(f"Industry-{code}", label="Отрасль")

    with allure.step("Сохранить"):
        # Saqlangach redirect barqaror emas (seansdagi keyingi create-savelarda
        # ilova dashboard'ga qaytarib yuboradi) — ro'yxatga o'zimiz kiramiz
        m.save()

    with allure.step(f"Qidiruv va ro'yxatda '{name}' tekshirish"):
        flow_navigate(page, tab="Модератор", name="Клиенты")
        m.expect_heading("Клиенты")
        m.search(name)
        if status in (None, "Активный"):
            m.grid_row(name)
        else:
            m.show_all()
            m.grid_row(name, status)

    return {"name": name, "tin": str(tin), "form": form}


@allure.epic("Модератор")
@allure.feature("Клиенты")
@allure.story("Создание клиента")
@allure.title("Yangi Клиент (Юр. лицо) yaratish")
def test_client(page: Page, code) -> None:
    with allure.step("Tizimga kirish"):
        authorization(page)
    run_client(page, code)


# CRUD testlari ko'chirilgan: tests/test_regression/ — bu yerda faqat basic create qoladi.
