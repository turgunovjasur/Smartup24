"""SETUP bo'limi runneri — barcha formalarning basic create testlari ALOHIDA
Allure testlar bo'lib, bitta seansda (bitta admin login) ketma-ket ishga tushadi.

NEGA ALOHIDA FAYL
-----------------
Ilgari setup + group_a + regression bitta ``tests/test_all_runner.py`` da edi va
har 3 soatda BIRGA ishlardi. Endi bo'limlar TURLI jadvalda ishlashi kerak
(setup + group_a — tez/kritik; regression — kamdan-kam). Shuning uchun har bo'lim
o'z runner fayliga bo'lindi (main/document allaqachon shunday):

    tests/test_setup/test_all_setup.py          — SHU FAYL
    tests/test_group_a/test_all_group_a.py      — group_a
    tests/test_regression/test_all_regression.py — regression
    tests/test_main/test_all_main.py            — main
    tests/test_document/test_all_document_runner.py — document

DIZAYN (test_all_main.py bilan bir xil)
---------------------------------------
- **Bitta seans / bitta login.** Barcha testlar session-scope ``session_page``
  fixture'ini oladi — butun fayl uchun YAGONA browser+context+page.
  ``test_000_login_admin`` bir marta admin bilan kiradi.
- **Kod varianti.** Setup ``code`` ni TO'G'RIDAN-TO'G'RI ishlatadi. group_a
  ``{code}2``, regression ``{code}3`` ishlatadi — shuning uchun bu fayllarni
  BITTA pytest chaqiruvida birga ishlatganda (kunlik "hammasi" run) nom
  to'qnashuvi bo'lmaydi.

ISHGA TUSHIRISH
---------------
    python -m pytest tests/test_setup/test_all_setup.py -v
    # setup + group_a birga (bitta login):
    python -m pytest tests/test_setup/test_all_setup.py tests/test_group_a/test_all_group_a.py -v
"""
import allure
from playwright.sync_api import Page

from flows.flow_authorization import authorization

from tests.test_setup.test_manufacturer import run_manufacturer as setup_manufacturer
from tests.test_setup.test_industry import run_industry as setup_industry
from tests.test_setup.test_category import run_category as setup_category
from tests.test_setup.test_region import run_region as setup_region
from tests.test_setup.test_product import run_product as setup_product
from tests.test_setup.test_form_of_ownership import run_form_of_ownership as setup_ownership
from tests.test_setup.test_supplier import run_supplier as setup_supplier
from tests.test_setup.test_client import run_client as setup_client
from tests.test_setup.test_legal_person import run_legal_person as setup_legal_person
from tests.test_setup.test_currency import run_currency as setup_currency
from tests.test_setup.test_konkurs import run_konkurs as setup_konkurs
from tests.test_setup.test_bonus import run_bonus as setup_bonus
from tests.test_setup.test_territory import run_territory as setup_territory
from tests.test_setup.test_vaprost import run_vaprost as setup_vaprost
from tests.test_setup.test_oprosniki import run_oprosniki as setup_oprosniki
from tests.test_setup.test_shablon import run_shablon as setup_shablon
from tests.test_setup.test_person_group import run_person_group as setup_person_group
from tests.test_setup.test_box_type import run_box_type as setup_box_type
from tests.test_setup.test_measure import run_measure as setup_measure
from tests.test_setup.test_service import run_service as setup_service
from tests.test_setup.test_quiz_type import run_quiz_type as setup_quiz_type
from tests.test_setup.test_outlet import run_outlet as setup_outlet


def _setup_code(code) -> str:
    """Setup bo'limi kod varianti — session ``code`` to'g'ridan-to'g'ri."""
    return code


# ══════════════════════════════════════════════════════════════════════════════
# 0. LOGIN — bir marta, butun seans uchun
# ══════════════════════════════════════════════════════════════════════════════
@allure.epic("Модератор")
@allure.feature("Runner — seans")
@allure.title("Login — admin bilan bir marta kirish (butun setup runner uchun)")
def test_000_login_admin(session_page: Page) -> None:
    """Butun runner uchun YAGONA login. Keyingi barcha testlar shu ochiq
    session_page seansidan foydalanadi — qayta login qilinmaydi."""
    authorization(session_page)


# ══════════════════════════════════════════════════════════════════════════════
# I. SETUP — barcha formalarning basic create testlari
# ══════════════════════════════════════════════════════════════════════════════
@allure.epic("Модератор")
@allure.feature("Setup — basic create")
@allure.title("Setup: Производитель — yangi ishlab chiqaruvchi")
def test_010_setup_manufacturer(session_page: Page, code) -> None:
    setup_manufacturer(session_page, _setup_code(code))


@allure.epic("Модератор")
@allure.feature("Setup — basic create")
@allure.title("Setup: Отрасль — yangi sanoat turi")
def test_011_setup_industry(session_page: Page, code) -> None:
    setup_industry(session_page, _setup_code(code))


@allure.epic("Модератор")
@allure.feature("Setup — basic create")
@allure.title("Setup: Категория — yangi tovar kategoriyasi")
def test_012_setup_category(session_page: Page, code) -> None:
    setup_category(session_page, _setup_code(code))


@allure.epic("Модератор")
@allure.feature("Setup — basic create")
@allure.title("Setup: Регион — yangi hudud")
def test_013_setup_region(session_page: Page, code) -> None:
    setup_region(session_page, _setup_code(code))


@allure.epic("Модератор")
@allure.feature("Setup — basic create")
@allure.title("Setup: Продукт — yangi mahsulot")
def test_014_setup_product(session_page: Page, code) -> None:
    setup_product(session_page, _setup_code(code))


@allure.epic("Модератор")
@allure.feature("Setup — basic create")
@allure.title("Setup: Форма собственности — yangi tashkiliy-huquqiy shakl")
def test_015_setup_ownership(session_page: Page, code) -> None:
    setup_ownership(session_page, _setup_code(code))


@allure.epic("Модератор")
@allure.feature("Setup — basic create")
@allure.title("Setup: Поставщик — yangi yetkazib beruvchi")
def test_016_setup_supplier(session_page: Page, code) -> None:
    setup_supplier(session_page, _setup_code(code))


@allure.epic("Модератор")
@allure.feature("Setup — basic create")
@allure.title("Setup: Клиент — yangi mijoz")
def test_017_setup_client(session_page: Page, code) -> None:
    setup_client(session_page, _setup_code(code))


@allure.epic("Модератор")
@allure.feature("Setup — basic create")
@allure.title("Setup: Юридическое лицо — yangi yuridik shaxs")
def test_018_setup_legal_person(session_page: Page, code) -> None:
    setup_legal_person(session_page, _setup_code(code))


@allure.epic("Модератор")
@allure.feature("Setup — basic create")
@allure.title("Setup: Валюта — yangi currency")
def test_019_setup_currency(session_page: Page, code) -> None:
    setup_currency(session_page, _setup_code(code))


@allure.epic("Модератор")
@allure.feature("Setup — basic create")
@allure.title("Setup: Конкурс — yangi konkurs")
def test_020_setup_konkurs(session_page: Page, code) -> None:
    setup_konkurs(session_page, _setup_code(code))


@allure.epic("Модератор")
@allure.feature("Setup — basic create")
@allure.title("Setup: Бонусная система — yangi bonus tizimi")
def test_021_setup_bonus(session_page: Page, code) -> None:
    setup_bonus(session_page, _setup_code(code))


@allure.epic("Модератор")
@allure.feature("Setup — basic create")
@allure.title("Setup: Территория — yangi hudud")
def test_022_setup_territory(session_page: Page, code) -> None:
    setup_territory(session_page, _setup_code(code))


@allure.epic("Модератор")
@allure.feature("Setup — basic create")
@allure.title("Setup: Вопрос — yangi savol")
def test_023_setup_vaprost(session_page: Page, code) -> None:
    setup_vaprost(session_page, _setup_code(code))


@allure.epic("Модератор")
@allure.feature("Setup — basic create")
@allure.title("Setup: Опросник — yangi so'rovnoma")
def test_024_setup_oprosniki(session_page: Page, code) -> None:
    setup_oprosniki(session_page, _setup_code(code))


@allure.epic("Модератор")
@allure.feature("Setup — basic create")
@allure.title("Setup: Шаблон отчета — yangi shablon")
def test_025_setup_shablon(session_page: Page, code) -> None:
    setup_shablon(session_page, _setup_code(code))


# ── Sub-nav справочniklar (list sarlavhasidagi bo'limlar) ─────────────────────
@allure.epic("Модератор")
@allure.feature("Setup — basic create")
@allure.title("Setup: Характеристики (Юр. лица) — Юр.лицо sub-nav")
def test_026_setup_person_group(session_page: Page, code) -> None:
    setup_person_group(session_page, _setup_code(code))


@allure.epic("Модератор")
@allure.feature("Setup — basic create")
@allure.title("Setup: Типы упаковок — Товары sub-nav")
def test_027_setup_box_type(session_page: Page, code) -> None:
    setup_box_type(session_page, _setup_code(code))


@allure.epic("Модератор")
@allure.feature("Setup — basic create")
@allure.title("Setup: Единицы измерения — Товары sub-nav")
def test_028_setup_measure(session_page: Page, code) -> None:
    setup_measure(session_page, _setup_code(code))


@allure.epic("Модератор")
@allure.feature("Setup — basic create")
@allure.title("Setup: Услуги — Товары sub-nav (Ед. изм. = кг, global)")
def test_029_setup_service(session_page: Page, code) -> None:
    setup_service(session_page, _setup_code(code))


@allure.epic("Модератор")
@allure.feature("Setup — basic create")
@allure.title("Setup: Тип вопроса — Вопросы sub-nav")
def test_030_setup_quiz_type(session_page: Page, code) -> None:
    setup_quiz_type(session_page, _setup_code(code))


@allure.epic("Модератор")
@allure.feature("Setup — basic create")
@allure.title("Setup: Торговые точки — Клиенты sub-nav (test_017 client'ini ishlatadi)")
def test_031_setup_outlet(session_page: Page, code) -> None:
    # Majburiy "Клиент" uchun test_017 da yaratilgan client-{code} qayta ishlatiladi
    setup_outlet(session_page, _setup_code(code), client_name=f"client-{_setup_code(code)}")
