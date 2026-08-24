import allure
from playwright.sync_api import Page

from flows.flow_authorization import authorization
from flows.flow_navbar import flow_menu, flow_navigate
from utils.base_page import BasePage


def run_currency(page: Page, code, name=None, kod=None, active=True) -> dict:
    """Yangi Валюта yaratadi. ``name``/``kod`` berilmasa so`m{code}/{code};
    ``active=False`` bo'lsa Статус switch o'chirib yaratiladi. Yaratilgan
    qiymatlarni qaytaradi (Код unikal bo'lishi shart)."""
    m = BasePage(page)
    if name is None:
        name = f"so`m{code}"
    if kod is None:
        kod = f"{code}"

    with allure.step("Навигация: Модератор → Валюты"):
        flow_navigate(page, tab="Модератор", name="Валюты")
        m.expect_heading("Валюты")

    with allure.step("Создать: yangi Валюта formasi ochish"):
        m.open_create()
        m.expect_heading("Валюта (Создания)")

    with allure.step(f"Форма: Название = {name}, Код = {kod}"):
        m.input(label="Название", value=name)
        m.input(smtid="code", value=kod)  # label "Код" ikkinchi formada "Код сервера" ga aralashadi
        m.input(label="Базовая денежная единица", value=kod)
        m.checkbox(label="Статус", checked=active)

    if active:
        with allure.step("Сохранить va ro'yxatda tekshirish"):
            # Saqlangach redirect barqaror emas (dashboard'ga ketishi mumkin) —
            # ro'yxatga o'zimiz kiramiz
            m.save()
            flow_navigate(page, tab="Модератор", name="Валюты")
            m.expect_heading("Валюты")
            # Валютыда qidiruv default Название bo'yicha ISHLAMAYDI —
            # "Настройки поиска" orqali yoqiladi
            flow_menu(page)
            m.search(name)
            m.grid_row(name)
    else:
        with allure.step("Сохранить va Показать все bilan tekshirish"):
            # Passiv yozuv default ro'yxatda ko'rinmaydi; redirect'ga tayanmay
            # ro'yxatga o'zimiz kiramiz
            m.save()
            flow_navigate(page, tab="Модератор", name="Валюты")
            m.expect_heading("Валюты")
            flow_menu(page)
            m.search(name)
            m.show_all()
            m.grid_row(name, "Неактивный")

    return {"name": name, "kod": str(kod)}


@allure.epic("Модератор")
@allure.feature("Валюты")
@allure.story("Создание валюты")
@allure.title("Yangi Валюта yaratish")
def test_currency(page: Page, code) -> None:
    with allure.step("Tizimga kirish"):
        authorization(page)
    run_currency(page, code)


# CRUD testlari ko'chirilgan: tests/test_regression/ — bu yerda faqat basic create qoladi.
