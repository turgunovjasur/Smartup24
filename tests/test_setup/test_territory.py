import allure
from playwright.sync_api import Page

from flows.flow_authorization import authorization
from flows.flow_navbar import flow_navigate
from utils.base_page import BasePage


def run_territory(page: Page, code, name=None, active=True) -> None:
    """Yangi Tерритория yaratadi. ``name`` berilmasa territory-{code};
    ``active=False`` bo'lsa Статус switch o'chirib yaratiladi."""
    m = BasePage(page)
    if name is None:
        name = f"territory-{code}"

    with allure.step("Навигация: Модератор → Tерритории"):
        flow_navigate(page, tab="Модератор", name="Tерритории")
        m.expect_heading("Tерритории")

    with allure.step("Создать: yangi Tерритория formasi ochish"):
        m.open_create()
        m.expect_heading("Tерритория (Создания)")

    with allure.step(f"Форма: Название = {name}, Статус = {'Активный' if active else 'Неактивный'}"):
        m.input(label="Название", value=name)
        m.checkbox(label="Статус", checked=active)

    with allure.step("Сохранить"):
        # Saqlangach redirect barqaror emas (seansdagi keyingi create-savelarda
        # ilova dashboard'ga qaytarib yuboradi) — ro'yxatga o'zimiz kiramiz
        m.save()

    with allure.step(f"Qidiruv va ro'yxatda '{name}' tekshirish"):
        flow_navigate(page, tab="Модератор", name="Tерритории")
        m.expect_heading("Tерритории")
        m.search(name)
        if active:
            m.grid_row(name)
        else:
            m.show_all()
            m.grid_row(name, "Неактивный")


@allure.epic("Модератор")
@allure.feature("Tерритории")
@allure.story("Создание территории")
@allure.title("Yangi Tерритория yaratish")
def test_territory(page: Page, code) -> None:
    with allure.step("Tizimga kirish"):
        authorization(page)
    run_territory(page, code)


# CRUD testlari ko'chirilgan: tests/test_regression/ — bu yerda faqat basic create qoladi.
