"""GROUP A bo'limi runneri — supplier/client, userlar, hamkorlik, tovar
biriktirish va order/status oqimi ALOHIDA Allure testlar bo'lib, bitta seansda
ketma-ket ishga tushadi.

NEGA ALOHIDA FAYL
-----------------
Ilgari setup + group_a + regression bitta ``tests/test_all_runner.py`` da edi.
Endi bo'limlar TURLI jadvalda ishlaydi (setup + group_a tez/kritik, regression
kamdan-kam) — shuning uchun har bo'lim o'z runner fayliga bo'lindi. Batafsil:
``tests/test_setup/test_all_setup.py`` docstring'iga qarang.

DIZAYN
------
- **Bitta seans.** session-scope ``session_page`` — butun fayl uchun yagona
  browser+page. ``test_000_login_admin`` admin bilan kiradi. Group A order/status
  bosqichlarida rol almashadi (klient/postavshik user), oxirida postavshik user
  seansida tugaydi.
- **Kod varianti.** Group A ``{code}2`` ishlatadi (setup ``code``, regression
  ``{code}3``) — bu fayllarni birga ishlatganda nom to'qnashuvi bo'lmaydi.
- **O'ZINI TA'MINLAYDI.** Group A o'z ma'lumotnomalarini (Region/MCHJ/Industry/
  Manufacturer/Category, hammasi ``{code}2``) test_200–204 da O'ZI yaratadi —
  setup bo'limiga bog'liq EMAS, alohida ham ishlaydi.
- **Testlararo ma'lumot.** Yaratilgan tovar nomi (linking → order) ``runner_state``
  (session lug'at, conftest) orqali uzatiladi.

BACKEND 500 (TARIX)
-------------------
Avval cooperation/order/order_status dev backend 500 (FAZO_QUERY Field not found
[supplier_pinfl]) sababli xfail edi. Backend tuzatilgach (2026-08-26) marker
olib tashlandi — bu testlar endi HAQIQATAN tekshiriladi.

ISHGA TUSHIRISH
---------------
    python -m pytest tests/test_group_a/test_all_group_a.py -v
"""
import allure
import pytest
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


def _ga_code(code) -> str:
    """Group A bo'limi kod varianti — setup (code) va regression ({code}3) bilan
    to'qnashmaslik uchun {code}2."""
    return f"{code}2"


# ══════════════════════════════════════════════════════════════════════════════
# 0. LOGIN — bir marta, butun seans uchun
# ══════════════════════════════════════════════════════════════════════════════
@allure.epic("Group A")
@allure.feature("Runner — seans")
@allure.title("Login — admin bilan bir marta kirish (butun group_a runner uchun)")
def test_000_login_admin(session_page: Page) -> None:
    """Butun runner uchun YAGONA login. Group A refs/supplier/... admin'da
    yaratiladi; order/status bosqichlarida rol almashadi."""
    authorization(session_page)


# ══════════════════════════════════════════════════════════════════════════════
# I. Ma'lumotnomalar — group_a O'ZI yaratadi ({code}2)
# ══════════════════════════════════════════════════════════════════════════════
@allure.epic("Group A")
@allure.feature("Ma'lumotnomalar")
@allure.title("Group A: Регион")
def test_200_ga_region(session_page: Page, code) -> None:
    setup_region(session_page, _ga_code(code))


@allure.epic("Group A")
@allure.feature("Ma'lumotnomalar")
@allure.title("Group A: Форма собственности")
def test_201_ga_ownership(session_page: Page, code) -> None:
    setup_ownership(session_page, _ga_code(code))


@allure.epic("Group A")
@allure.feature("Ma'lumotnomalar")
@allure.title("Group A: Отрасль")
def test_202_ga_industry(session_page: Page, code) -> None:
    setup_industry(session_page, _ga_code(code))


@allure.epic("Group A")
@allure.feature("Ma'lumotnomalar")
@allure.title("Group A: Производитель")
def test_203_ga_manufacturer(session_page: Page, code) -> None:
    setup_manufacturer(session_page, _ga_code(code))


@allure.epic("Group A")
@allure.feature("Ma'lumotnomalar")
@allure.title("Group A: Категория")
def test_204_ga_category(session_page: Page, code) -> None:
    setup_category(session_page, _ga_code(code))


# ══════════════════════════════════════════════════════════════════════════════
# II. Supplier/Client, userlar, hamkorlik, tovar, order
# ══════════════════════════════════════════════════════════════════════════════
@allure.epic("Group A")
@allure.feature("Поставщик/Клиент")
@allure.title("Group A: Поставщик — yangi yetkazib beruvchi")
def test_210_ga_supplier(session_page: Page, code) -> None:
    ga = _ga_code(code)
    ga_supplier(
        session_page, ga,
        region=f"Region-{ga}", ownership=f"MCHJ-{ga}", industry=f"Industry-{ga}",
    )


@allure.epic("Group A")
@allure.feature("Поставщик/Клиент")
@allure.title("Group A: Клиент — yangi mijoz")
def test_211_ga_client(session_page: Page, code) -> None:
    ga = _ga_code(code)
    ga_client(
        session_page, ga,
        region=f"Region-{ga}", ownership=f"MCHJ-{ga}", industry=f"Industry-{ga}",
    )


@allure.epic("Group A")
@allure.feature("Пользователи")
@allure.title("Group A: Пользователь поставщика")
def test_212_ga_supplier_user(session_page: Page, code) -> None:
    ga_supplier_user(session_page, _ga_code(code))


@allure.epic("Group A")
@allure.feature("Пользователи")
@allure.title("Group A: Пользователь клиента")
def test_213_ga_client_user(session_page: Page, code) -> None:
    ga_client_user(session_page, _ga_code(code))


@allure.epic("Group A")
@allure.feature("Сотрудничество")
@allure.title("Group A: Запрос на сотрудничество — yuborish va tasdiqlash")
def test_214_ga_cooperation(session_page: Page, code) -> None:
    ga_cooperation(session_page, _ga_code(code))


@allure.epic("Group A")
@allure.feature("Товары")
@allure.title("Group A: Продукт — yangi tovar yaratish")
def test_215_ga_product(session_page: Page, code, runner_state) -> None:
    ga = _ga_code(code)
    product_name = ga_product(
        session_page, ga,
        manufacturer=f"Manufacturer-{ga}", industry=f"Industry-{ga}",
        category=f"Category-{ga}",
    )
    runner_state["ga_product_name"] = product_name


@allure.epic("Group A")
@allure.feature("Товары")
@allure.title("Group A: Прикрепление товара — biriktirish va narx o'rnatish")
def test_216_ga_product_linking(session_page: Page, code, runner_state) -> None:
    product_name = ga_product_linking(
        session_page, _ga_code(code),
        product_name=runner_state.get("ga_product_name"),
    )
    # linking haqiqatda biriktirgan nomni qaytaradi — order aynan shuni qidiradi
    runner_state["ga_product_name"] = product_name


# BACKEND BUG (2026-08-28): klient zakazini saqlashda server "Gmap:paid_delivery
# not found" Ошибка qaytaradi (URL /x24/b/sb/sbd/client/deal+add$save) — dev
# (sm24) backend'da `paid_delivery` Gmap konfiguratsiyasi yo'q. Bu test kodida
# HAL BO'LMAYDI; release'да tuzatiladi. Forma to'g'ri to'ldiriladi (screenshot
# tasdiqlagan), lekin save server-side yiqiladi → forma "Заказ (создание)"да
# qoladi. Tarixда bu order testlari backend 500 sabab xfail edi (2026-08-26 da
# backend tuzatilib olingan); backend YANA buzilgani uchun qayta xfail qilindi.
# Backend tuzalganда bu testlar XPASS bo'ladi → markerlarni olib tashlash SHART.
@pytest.mark.xfail(
    reason="backend bug: 'Gmap:paid_delivery not found' klient zakaz save'да (release'да tuzatiladi)",
    strict=False,
)
@allure.epic("Клиент")
@allure.feature("Group A")
@allure.title("Group A: Заказ — klient foydalanuvchisi nomidan yaratish")
def test_217_ga_order(session_page: Page, code, runner_state) -> None:
    """Order faqat klient rolida ko'rinadi — admin seansdan chiqib, group_a'da
    yaratilgan klient foydalanuvchisi bilan kiramiz."""
    ga = _ga_code(code)
    logout(session_page)
    authorization(session_page, email=f"client_user-{ga}@{COMPANY_CODE}", password="1")
    ga_order(session_page, ga, product_name=runner_state.get("ga_product_name"))


# ZANJIR (217 backend bug): status o'zgartirish MANTIG'I sog'lom (qo'lda mavjud
# zakazda postavshik status almashtira oladi — MCP/qo'lda tasdiqlangan), lekin
# 217 backend bug sabab zakaz UMUMAN yaratilmaydi → ro'yxat bo'sh ("Нет
# результатов"), o'zgartirishga zakaz yo'q. 217 tuzalsa bu ham avtomatik ishlaydi.
@pytest.mark.xfail(
    reason="217 zanjiri: zakaz backend bug ('Gmap:paid_delivery not found') sabab yaratilmaydi → status o'zgartirishga zakaz yo'q",
    strict=False,
)
@allure.epic("Поставщик")
@allure.feature("Group A")
@allure.title("Group A: Статус заказа — postavshik nomidan Новый → Завершен")
def test_218_ga_order_status(session_page: Page, code) -> None:
    """Status faqat postavshik rolida o'zgartiriladi — klient seansdan chiqib,
    group_a'da yaratilgan postavshik foydalanuvchisi bilan kiramiz."""
    ga = _ga_code(code)
    logout(session_page)
    authorization(session_page, email=f"supplier_user-{ga}@{COMPANY_CODE}", password="1")
    ga_order_status(session_page, ga)
