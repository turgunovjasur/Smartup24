"""ВОЗВРАТ bo'limi runneri — klient завершен zakazdan возврат yaratadi, admin
tekshiradi. Bitta seansда, order oqimining to'liq DAVOMI.

Bu bo'lim group_a'dan ALOHIDA (aralashib ketmasligi uchun): o'zi ma'lumotnoma +
supplier/client/userlar/hamkorlik/tovar setup'ini quradi (setup va group_a
``run_*`` funksiyalarini QAYTA ISHLATADI), zakaz urib statusni Завершен qiladi,
so'ng klient o'sha zakazdan Возврат yaratadi va admin uni Модератор → Возвраты
da tekshiradi.

DIZAYN (test_all_group_a / test_all_aksiya bilan bir xil)
--------------------------------------------------------
- **Bitta seans / session_page.** ``test_000`` admin bilan kiradi; zakaz/возврат
  bosqichlarida klient user'ga, status/tekshiruvда postavshik/admin'ga rol almashadi.
- **Kod varianti ``{code}5``** — setup(code)/group_a({code}2)/regression({code}3)/
  aksiya({code}4) bilan nom to'qnashmasligi uchun.
- **O'zini ta'minlaydi.** Refs + supplier/client/... shu runnerда yaratiladi.

OQIM
----
setup refs → supplier/client/userlar/hamkorlik/tovar+narx+В наличие →
ZAKAZ(klient) → STATUS→Завершен(postavshik) → ВОЗВРАТ(klient) →
ВОЗВРАТ tekshiruvi(admin, Модератор→Возвраты).

ISHGA TUSHIRISH
---------------
    python -m pytest tests/test_vazrat/test_all_vazrat.py -v
"""
import allure
from playwright.sync_api import Page

from flows.flow_authorization import COMPANY_CODE, authorization, logout

from tests.test_setup.test_manufacturer import run_manufacturer as setup_manufacturer
from tests.test_setup.test_industry import run_industry as setup_industry
from tests.test_setup.test_category import run_category as setup_category
from tests.test_setup.test_region import run_region as setup_region
from tests.test_setup.test_form_of_ownership import run_form_of_ownership as setup_ownership

from tests.test_group_a.test_supplier import run_supplier as ga_supplier
from tests.test_group_a.test_client import run_client as ga_client
from tests.test_group_a.test_supplier_user import run_supplier_user as ga_supplier_user
from tests.test_group_a.test_client_user import run_client_user as ga_client_user
from tests.test_group_a.test_cooperation import run_cooperation as ga_cooperation
from tests.test_group_a.test_product import run_product as ga_product
from tests.test_group_a.test_product_linking import run_product_linking as ga_product_linking
from tests.test_group_a.test_order import run_order as ga_order
from tests.test_group_a.test_order_status_change import run_order_status_change as ga_order_status

from tests.test_vazrat.test_vazrat import run_vazrat, run_vazrat_verify


def _vz_code(code) -> str:
    """Возврат bo'limi kod varianti — boshqa bo'limlar bilan to'qnashmaslik uchun {code}5."""
    return f"{code}5"


# ══════════════════════════════════════════════════════════════════════════════
# 0. LOGIN
# ══════════════════════════════════════════════════════════════════════════════
@allure.epic("Возврат")
@allure.feature("Runner — seans")
@allure.title("Login — admin bilan bir marta kirish (butun возврат runner uchun)")
def test_000_login_admin(session_page: Page) -> None:
    authorization(session_page)


# ══════════════════════════════════════════════════════════════════════════════
# I. SETUP — ma'lumotnomalar ({code}5)
# ══════════════════════════════════════════════════════════════════════════════
@allure.epic("Возврат")
@allure.feature("Setup")
@allure.title("Setup: Регион")
def test_100_region(session_page: Page, code) -> None:
    setup_region(session_page, _vz_code(code))


@allure.epic("Возврат")
@allure.feature("Setup")
@allure.title("Setup: Форма собственности")
def test_101_ownership(session_page: Page, code) -> None:
    setup_ownership(session_page, _vz_code(code))


@allure.epic("Возврат")
@allure.feature("Setup")
@allure.title("Setup: Отрасль")
def test_102_industry(session_page: Page, code) -> None:
    setup_industry(session_page, _vz_code(code))


@allure.epic("Возврат")
@allure.feature("Setup")
@allure.title("Setup: Производитель")
def test_103_manufacturer(session_page: Page, code) -> None:
    setup_manufacturer(session_page, _vz_code(code))


@allure.epic("Возврат")
@allure.feature("Setup")
@allure.title("Setup: Категория")
def test_104_category(session_page: Page, code) -> None:
    setup_category(session_page, _vz_code(code))


# ══════════════════════════════════════════════════════════════════════════════
# II. SETUP — supplier/client, userlar, hamkorlik, tovar
# ══════════════════════════════════════════════════════════════════════════════
@allure.epic("Возврат")
@allure.feature("Setup")
@allure.title("Setup: Поставщик")
def test_110_supplier(session_page: Page, code) -> None:
    vz = _vz_code(code)
    ga_supplier(session_page, vz, region=f"Region-{vz}", ownership=f"MCHJ-{vz}", industry=f"Industry-{vz}")


@allure.epic("Возврат")
@allure.feature("Setup")
@allure.title("Setup: Клиент")
def test_111_client(session_page: Page, code) -> None:
    vz = _vz_code(code)
    ga_client(session_page, vz, region=f"Region-{vz}", ownership=f"MCHJ-{vz}", industry=f"Industry-{vz}")


@allure.epic("Возврат")
@allure.feature("Setup")
@allure.title("Setup: Пользователь поставщика")
def test_112_supplier_user(session_page: Page, code) -> None:
    ga_supplier_user(session_page, _vz_code(code))


@allure.epic("Возврат")
@allure.feature("Setup")
@allure.title("Setup: Пользователь клиента")
def test_113_client_user(session_page: Page, code) -> None:
    ga_client_user(session_page, _vz_code(code))


@allure.epic("Возврат")
@allure.feature("Setup")
@allure.title("Setup: Запрос на сотрудничество")
def test_114_cooperation(session_page: Page, code) -> None:
    ga_cooperation(session_page, _vz_code(code))


@allure.epic("Возврат")
@allure.feature("Setup")
@allure.title("Setup: Продукт")
def test_115_product(session_page: Page, code, runner_state) -> None:
    vz = _vz_code(code)
    product_name = ga_product(
        session_page, vz,
        manufacturer=f"Manufacturer-{vz}", industry=f"Industry-{vz}", category=f"Category-{vz}",
    )
    runner_state["vz_product_name"] = product_name


@allure.epic("Возврат")
@allure.feature("Setup")
@allure.title("Setup: Прикрепление товара — narx + В наличие")
def test_116_product_linking(session_page: Page, code, runner_state) -> None:
    product_name = ga_product_linking(
        session_page, _vz_code(code), product_name=runner_state.get("vz_product_name"),
    )
    runner_state["vz_product_name"] = product_name


# ══════════════════════════════════════════════════════════════════════════════
# III. ZAKAZ → STATUS Завершен
# ══════════════════════════════════════════════════════════════════════════════
@allure.epic("Возврат")
@allure.feature("Заказ")
@allure.title("Заказ — klient foydalanuvchisi nomidan yaratish")
def test_120_order(session_page: Page, code, runner_state) -> None:
    vz = _vz_code(code)
    logout(session_page)
    authorization(session_page, email=f"client_user-{vz}@{COMPANY_CODE}", password="1")
    ga_order(session_page, vz, product_name=runner_state.get("vz_product_name"))


@allure.epic("Возврат")
@allure.feature("Заказ")
@allure.title("Статус заказа — postavshik nomidan Черновик → Завершен")
def test_121_order_status(session_page: Page, code) -> None:
    vz = _vz_code(code)
    logout(session_page)
    authorization(session_page, email=f"supplier_user-{vz}@{COMPANY_CODE}", password="1")
    ga_order_status(session_page, vz)


# ══════════════════════════════════════════════════════════════════════════════
# IV. ВОЗВРАТ — yaratish (klient) + tekshirish (admin)
# ══════════════════════════════════════════════════════════════════════════════
@allure.epic("Возврат")
@allure.feature("Возврат")
@allure.title("Возврат — klient nomidan завершен zakazdan qaytarish")
def test_130_vazrat(session_page: Page, code, runner_state) -> None:
    vz = _vz_code(code)
    logout(session_page)
    authorization(session_page, email=f"client_user-{vz}@{COMPANY_CODE}", password="1")
    run_vazrat(session_page, vz, product_name=runner_state.get("vz_product_name"))


@allure.epic("Возврат")
@allure.feature("Возврат")
@allure.title("Возврат tekshiruvi — admin nomidan Модератор → Возвраты")
def test_131_vazrat_verify(session_page: Page, code) -> None:
    vz = _vz_code(code)
    logout(session_page)
    authorization(session_page)
    run_vazrat_verify(session_page, vz)
