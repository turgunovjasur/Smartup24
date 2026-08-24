import random

import allure
from playwright.sync_api import Page

from flows.flow_authorization import authorization
from flows.flow_navbar import flow_navigate
from utils.base_page import BasePage


def run_legal_person(page: Page, code, name=None, status=None) -> dict:
    """Yangi Юр. лицо (Тип=Клиент) yaratadi. ``name`` berilmasa
    LegalPerson-{code}; ``status`` berilsa shu status radiosi tanlanadi
    (masalan "Пассивный" — bunda tekshiruv "Показать все" bilan).
    Yaratilgan qiymatlarni qaytaradi."""
    m = BasePage(page)
    if name is None:
        name = f"LegalPerson-{code}"
    short_name = name if name != f"LegalPerson-{code}" else f"LP-{code}"
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

    with allure.step(f"Форма: Форма собственности = {form}, Тип = Клиент, Статус = {status or 'Активный'}"):
        m.select(option_text=form, label="Форма собственности")
        m.radio("Клиент", label="Тип Юр. лица")
        m.radio(status or "Активный", label="Статус")

    with allure.step(f"Характеристика товаров: Отрасль = Industry-{code}"):
        m.click_button("Характеристика товаров")
        m.select(f"Industry-{code}", label="Отрасль")

    with allure.step("Сохранить"):
        # Saqlangach redirect barqaror emas (seansdagi keyingi create-savelarda
        # ilova dashboard'ga qaytarib yuboradi) — ro'yxatga o'zimiz kiramiz
        m.save()

    with allure.step(f"Qidiruv va ro'yxatda '{name}' tekshirish"):
        flow_navigate(page, tab="Модератор", name="Юридическое лицо")
        m.expect_heading("Юридическое лицо")
        m.search(name)
        if status in (None, "Активный"):
            m.grid_row(name)
        else:
            m.show_all()
            m.grid_row(name, status)

    return {"name": name, "tin": str(tin), "form": form, "short_name": short_name}


@allure.epic("Модератор")
@allure.feature("Юридическое лицо")
@allure.story("Создание юридического лица")
@allure.title("Yangi Юр. лицо yaratish")
def test_legal_person(page: Page, code) -> None:
    with allure.step("Tizimga kirish"):
        authorization(page)
    run_legal_person(page, code)


