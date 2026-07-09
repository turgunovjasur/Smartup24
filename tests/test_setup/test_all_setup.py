import allure
from playwright.sync_api import Page

from flows.flow_authorization import authorization
from tests.test_setup.test_Templates import run_shablon
from tests.test_setup.test_Vaprost import run_vaprost
from tests.test_setup.test_bonus import run_bonus
from tests.test_setup.test_category import run_category
from tests.test_setup.test_client import run_client
from tests.test_setup.test_criterya import run_criterya
from tests.test_setup.test_form_of_ownership import run_form_of_ownership
from tests.test_setup.test_industry import run_industry
from tests.test_setup.test_konkurs import run_konkurs
from tests.test_setup.test_legal_person import run_legal_person
from tests.test_setup.test_manufacturer import run_manufacturer
from tests.test_setup.test_oprosniki import run_oprosniki
from tests.test_setup.test_product import run_product
from tests.test_setup.test_region import run_region
from tests.test_setup.test_supplier import run_supplier
from tests.test_setup.test_teritory import run_territory
from tests.test_setup.test_Валюты import run_valyuta


@allure.epic("Модератор")
@allure.feature("Setup chain")
@allure.story("Basic create — barcha formalar")
@allure.title("Setup: barcha formalarning basic create testlari — bitta seansda zanjir")
def test_all_setup(page: Page, code) -> None:
    """Barcha moderator testlarini bitta seansda ketma-ket ishga tushiradi."""
    with allure.step("Tizimga kirish"):
        authorization(page)

    with allure.step("1. Производители — yangi ishlab chiqaruvchi"):
        run_manufacturer(page, code)

    with allure.step("2. Отрасль — yangi sanoat turi"):
        run_industry(page, code)

    with allure.step("3. Категория — yangi tovar kategoriyasi"):
        run_category(page, code)

    with allure.step("4. Регион — yangi hudud"):
        run_region(page, code)

    with allure.step("5. Продукт — yangi mahsulot"):
        run_product(page, code)

    with allure.step("6. Форма собственности — yangi tashkiliy-huquqiy shakl"):
        run_form_of_ownership(page, code)

    with allure.step("7. Поставщик — yangi yetkazib beruvchi"):
        run_supplier(page, code)

    with allure.step("8. Клиент — yangi mijoz"):
        run_client(page, code)

    with allure.step("9. Юридическое лицо — yangi yuridik shaxs"):
        run_legal_person(page, code)

    with allure.step("10. Валюта — yangi valyuta"):
        run_valyuta(page, code)

    with allure.step("11. Конкурс — yangi konkurs"):
        run_konkurs(page, code)

    with allure.step("12. Бонусная система — yangi bonus tizimi"):
        run_bonus(page, code)

    with allure.step("13. Tерритория — yangi hudud"):
        run_territory(page, code)

    with allure.step("14. Вопрос — yangi savol"):
        run_vaprost(page, code)

    with allure.step("15. Опросник — yangi so'rovnoma"):
        run_oprosniki(page, code)

    with allure.step("16. Критерий — yangi mezon"):
        run_criterya(page, code)

    with allure.step("17. Шаблон отчета — yangi shablon"):
        run_shablon(page, code)
