"""WEB + MOBIL E2E zakaz oqimi — bitta pytest chaqiruvida uch faza:

    1. web (admin)      supplier, client, userlar, hamkorlik, tovar, narx, В наличие
    2. mobil (klient)   web yaratgan client_user bilan zakaz beradi
    3. web (supplier)   o'sha zakaz statusini o'zgartiradi

Web qismi mavjud group_a/setup `run_*` funksiyalarini qayta ishlatadi. Fazalar
root conftest'ning `code` (bir xil) va `runner_state` (tovar nomi, faza natijasi)
orqali bog'lanadi; oldingi faza yiqilsa keyingisi skip bo'ladi.
Kod varianti {code}8 — boshqa bo'limlar bilan to'qnashmaydi. ~5.5 min.
"""
import allure
import pytest
from playwright.sync_api import Page

from flows.flow_authorization import COMPANY_CODE, authorization, logout
from tests.test_group_a.test_client import run_client
from tests.test_group_a.test_client_user import run_client_user
from tests.test_group_a.test_cooperation import run_cooperation
from tests.test_group_a.test_order_status_change import run_order_status_change
from tests.test_group_a.test_product import run_product
from tests.test_group_a.test_product_linking import run_product_linking
from tests.test_group_a.test_supplier import run_supplier
from tests.test_group_a.test_supplier_user import run_supplier_user
from tests.test_setup.test_category import run_category
from tests.test_setup.test_form_of_ownership import run_form_of_ownership
from tests.test_setup.test_industry import run_industry
from tests.test_setup.test_manufacturer import run_manufacturer
from tests.test_setup.test_region import run_region
from tests_mobile.config import WEB_USER_PASSWORD
from tests_mobile.flows import create_and_verify_order
from tests_mobile.screens.login_screen import LoginScreen

pytestmark = [pytest.mark.mobile, allure.epic("Web+Mobil E2E")]


@pytest.fixture
def c(code) -> str:
    return f"{code}8"


@allure.feature("Faza 1 — Web seed")
def test_100_web_seed(session_page: Page, c, runner_state) -> None:
    authorization(session_page)

    with allure.step("Ma'lumotnomalar: Регион / Форма собственности / Отрасль / Производитель / Категория"):
        run_region(session_page, c)
        run_form_of_ownership(session_page, c)
        run_industry(session_page, c)
        run_manufacturer(session_page, c)
        run_category(session_page, c)

    refs = dict(region=f"Region-{c}", ownership=f"MCHJ-{c}", industry=f"Industry-{c}")
    with allure.step("Поставщик, Клиент va ularning userlari"):
        run_supplier(session_page, c, **refs)
        run_client(session_page, c, **refs)
        run_supplier_user(session_page, c)
        run_client_user(session_page, c)

    with allure.step("Сотрудничество"):
        run_cooperation(session_page, c)

    with allure.step("Товар: yaratish, biriktirish, В наличие, narx"):
        product = run_product(session_page, c, manufacturer=f"Manufacturer-{c}",
                              industry=f"Industry-{c}", category=f"Category-{c}")
        runner_state["e2e_product"] = run_product_linking(session_page, c, product_name=product)


@allure.feature("Faza 2 — Mobil zakaz")
def test_200_mobile_order(driver, c, runner_state) -> None:
    product = runner_state.get("e2e_product")
    if not product:
        pytest.skip("Faza 1 (web seed) o'tmadi — zakaz uchun ma'lumot yo'q")

    user = f"client_user-{c}@{COMPANY_CODE}"
    with allure.step(f"Mobil login: {user}"):
        login = LoginScreen(driver)
        login.login(user, WEB_USER_PASSWORD)
        assert login.is_logged_in(), f"Mobil login muvaffaqiyatsiz: {user}"

    create_and_verify_order(driver, f"supplier-{c}", f"Category-{c}", product)
    runner_state["e2e_order_ok"] = True


@allure.feature("Faza 3 — Web status")
def test_300_web_status_change(session_page: Page, c, runner_state) -> None:
    if not runner_state.get("e2e_order_ok"):
        pytest.skip("Faza 2 (mobil zakaz) o'tmadi — status o'zgartiriladigan zakaz yo'q")

    logout(session_page)
    authorization(session_page, email=f"supplier_user-{c}@{COMPANY_CODE}", password=WEB_USER_PASSWORD)
    run_order_status_change(session_page, c)   # Черновик -> ... -> Завершен
