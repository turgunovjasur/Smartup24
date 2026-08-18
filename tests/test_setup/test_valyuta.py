import allure
from playwright.sync_api import Page

from flows.flow_authorization import authorization
from flows.flow_valyuta import run_valyuta


@allure.epic("Модератор")
@allure.feature("Валюты")
@allure.story("Создание валюты")
@allure.title("Yangi Валюта yaratish")
def test_valyuta(page: Page, code) -> None:
    with allure.step("Tizimga kirish"):
        authorization(page)
    run_valyuta(page, code)


# Basic create mantig'i flows/flow_valyuta.py ga ko'chirildi (yagona manba).
# CRUD ssenariylari tests/test_regression/ — bu yerda faqat basic create qoladi.
