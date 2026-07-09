import allure
from playwright.sync_api import Page

from flows.flow_authorization import authorization
from flows.flow_navbar import flow_navigate
from utils.base_page import BasePage


def run_region(page: Page, code, name=None, active=True) -> None:
    """Yangi Регион yaratadi. ``name`` berilmasa Region-{code}; ``active=False``
    bo'lsa Статус switch o'chirib yaratiladi (passiv region default ro'yxatda
    ko'rinmaydi — tekshiruv "Показать все" bilan bajariladi)."""
    m = BasePage(page)
    if name is None:
        name = f"Region-{code}"

    with allure.step("Навигация: Модератор → Регионы"):
        flow_navigate(page, tab="Модератор", name="Регионы")
        m.expect_heading("Регионы")

    with allure.step("Создать: yangi Регион formasi ochish"):
        m.open_create()
        m.expect_heading("Регион (Создания)")

    with allure.step(f"Форма: Название = {name}, Статус = {'Активный' if active else 'Неактивный'}"):
        m.input(label="Название", value=name)
        m.checkbox(label="Статус", checked=active)

    with allure.step("Сохранить"):
        # Saqlangach redirect barqaror emas (seansdagi keyingi create-savelarda
        # ilova dashboard'ga qaytarib yuboradi) — ro'yxatga o'zimiz kiramiz
        m.save()

    with allure.step(f"Qidiruv va ro'yxatda '{name}' tekshirish"):
        flow_navigate(page, tab="Модератор", name="Регионы")
        m.expect_heading("Регионы")
        m.search(name)
        if active:
            m.grid_row(name)
        else:
            m.show_all()
            m.grid_row(name, "Неактивный")


@allure.epic("Модератор")
@allure.feature("Регионы")
@allure.story("Создание региона")
@allure.title("Yangi Регион yaratish")
def test_region(page: Page, code) -> None:
    with allure.step("Tizimga kirish"):
        authorization(page)
    run_region(page, code)


# CRUD testlari ko'chirilgan: tests/test_regression/ — bu yerda faqat basic create qoladi.
