"""Umumiy runner — setup, group_a va regression zanjirlari ALOHIDA testlar bo'lib,
bitta seansda (bitta login) ketma-ket ishga tushadi.

NEGA QAYTA YOZILDI (2026-07-31)
------------------------------
Ilgari bu fayl bitta ``test_all_runner`` funksiyasi edi va barcha ``run_...``
larni ``allure.step`` ichida chaqirar edi. Pytest bitta funksiyani BITTA test
sifatida yig'gani uchun Allure hisobotida 20+ mantiqiy test FAQAT 1 ta test
bo'lib (ko'plab step bilan) ko'rinardi — har birining alohida PASSED/FAILED
statusi yo'q edi. Xuddi shu muammo ``test_all_setup`` / ``test_all_group_a`` /
``test_all_regression`` va har modulning ``test_..._all`` aggregatorida ham bor.

Yechim: har bir ``run_...`` mantig'i shu faylda ALOHIDA ``test_...`` funksiyasiga
aylantirildi. Endi Allure har birini alohida test sifatida (o'z nomi, statusi,
step'lari bilan) ko'rsatadi.

DIZAYN
------
- **Bitta seans / bitta login.** Barcha testlar session-scope ``session_page``
  fixture'ini oladi (conftest) — butun fayl uchun YAGONA browser+context+page.
  ``test_000_login_admin`` bir marta admin bilan kiradi; keyingi testlar shu
  ochiq seansdan foydalanadi. Group A oxirida rol almashadi (klient/postavshik
  user), regression boshida yana admin'ga qaytiladi — bu login almashishlar
  aynan eski aggregatordagi kabi.
- **Tartib.** Testlar BITTA modulda joylashgani uchun pytest ularni
  DEFINITSIYA tartibida bajaradi — pytest-order plagini shart emas. Raqamli
  prefiks (``test_010_...``) o'qishni osonlashtiradi.
- **Kod to'qnashuvi.** Setup / group_a / regression bir xil "Region-{code}"
  nomlarini yaratadi — shuning uchun har bo'lim session ``code`` dan yasalgan
  ALOHIDA deterministik variant ishlatadi: setup=``code``, group_a=``{code}2``,
  regression=``{code}3``.
- **Testlararo ma'lumot.** Group A'da yaratilgan tovar nomi (linking → zakaz)
  va konkurs regioni testlar orasida ``runner_state`` fixture (session lug'at,
  conftest) orqali uzatiladi — eski lokal o'zgaruvchilar o'rniga.

ISHGA TUSHIRISH
---------------
    python -m pytest tests/test_all_runner.py --alluredir=test-results/allure-results
    allure serve test-results/allure-results

Bu fayl SETUP + GROUP A + REGRESSION bo'limlarini o'z ichiga oladi. MAIN
("Главное") va DOCUMENT bo'limlari ALOHIDA fayllarda (takror bo'lmasligi uchun) —
``tests/test_main/test_all_main.py`` va ``tests/test_document/test_all_document_runner.py``.
Hammasini bitta seansda (bitta login) ketma-ket ishlatish uchun uch faylni bitta
``pytest`` chaqiruvida bering — ``session_page`` session-scope bo'lgani uchun
yagona browser/login bo'ladi:

    python -m pytest tests/test_all_runner.py \
        tests/test_main/test_all_main.py \
        tests/test_document/test_all_document_runner.py \
        --alluredir=test-results/allure-results

Bare ``pytest`` (butun repo) individual ``test_...`` fayllarni ham yig'adi — ular
DEBUG uchun qoladi (har biri o'z login bilan).
"""
import allure
import pytest
from playwright.sync_api import Page

from flows.flow_authorization import COMPANY_CODE, authorization, logout

# --- Setup: basic create funksiyalari (group_a refs va regression create uchun ham) ---
from tests.test_setup.test_manufacturer import run_manufacturer as setup_manufacturer
from tests.test_setup.test_industry import run_industry as setup_industry
from tests.test_setup.test_category import run_category as setup_category
from tests.test_setup.test_region import run_region as setup_region
from tests.test_setup.test_product import run_product as setup_product
from tests.test_setup.test_form_of_ownership import run_form_of_ownership as setup_ownership
from tests.test_setup.test_supplier import run_supplier as setup_supplier, ensure_refs
from tests.test_setup.test_client import run_client as setup_client
from tests.test_setup.test_legal_person import run_legal_person as setup_legal_person
from tests.test_setup.test_valyuta import run_valyuta as setup_valyuta
from tests.test_setup.test_konkurs import run_konkurs as setup_konkurs
from tests.test_setup.test_bonus import run_bonus as setup_bonus
from tests.test_setup.test_territory import run_territory as setup_territory
from tests.test_setup.test_vaprost import run_vaprost as setup_vaprost
from tests.test_setup.test_oprosniki import run_oprosniki as setup_oprosniki
from tests.test_setup.test_shablon import run_shablon as setup_shablon

# --- Group A: rol/oqim testlari ---
from tests.test_group_a.test_supplier import run_supplier as ga_supplier
from tests.test_group_a.test_client import run_client as ga_client
from tests.test_group_a.test_supplier_user import run_supplier_user as ga_supplier_user
from tests.test_group_a.test_client_user import run_client_user as ga_client_user
from tests.test_group_a.test_cooperation import run_cooperation as ga_cooperation
from tests.test_group_a.test_product import run_product as ga_product
from tests.test_group_a.test_product_linking import run_product_linking as ga_product_linking
from tests.test_group_a.test_zakaz import run_zakaz as ga_zakaz
from tests.test_group_a.test_zakaz_status_change import run_zakaz_status_change as ga_zakaz_status

# --- Regression: to'liq CRUD funksiyalari ---
from tests.test_regression.test_region import (
    run_region_delete, run_region_duplicate, run_region_edit,
    run_region_full, run_region_status, run_region_view,
)
from tests.test_regression.test_product import (
    ensure_product_refs, run_product_delete, run_product_edit,
    run_product_full, run_product_status, run_product_view,
)
from tests.test_regression.test_supplier import (
    run_supplier_delete, run_supplier_duplicate, run_supplier_edit,
    run_supplier_full, run_supplier_status, run_supplier_view,
)
from tests.test_regression.test_client import (
    run_client_delete, run_client_duplicate, run_client_edit,
    run_client_full, run_client_status, run_client_view,
)
from tests.test_regression.test_legal_person import (
    run_legal_person_delete, run_legal_person_duplicate, run_legal_person_edit,
    run_legal_person_full, run_legal_person_status, run_legal_person_view,
)
from tests.test_regression.test_valyuta import (
    run_valyuta_delete, run_valyuta_duplicate, run_valyuta_edit,
    run_valyuta_full, run_valyuta_status_activate, run_valyuta_status_deactivate,
    run_valyuta_view,
)
from tests.test_regression.test_konkurs import (
    ensure_konkurs_region, run_konkurs_delete, run_konkurs_edit,
    run_konkurs_full, run_konkurs_status, run_konkurs_view,
)
from tests.test_regression.test_bonus import (
    run_bonus_delete, run_bonus_edit, run_bonus_full,
    run_bonus_status, run_bonus_view,
)
from tests.test_regression.test_territory import (
    run_territory_delete, run_territory_edit, run_territory_status, run_territory_view,
)
from tests.test_regression.test_vaprost import (
    run_vaprost_delete, run_vaprost_duplicate, run_vaprost_edit,
    run_vaprost_full, run_vaprost_status, run_vaprost_view,
)
from tests.test_regression.test_oprosniki import (
    run_oprosniki_attach, run_oprosniki_delete, run_oprosniki_duplicate,
    run_oprosniki_edit, run_oprosniki_full, run_oprosniki_status, run_oprosniki_view,
)
from tests.test_regression.test_shablon import (
    run_shablon_delete, run_shablon_edit, run_shablon_full,
    run_shablon_report, run_shablon_status, run_shablon_view,
)


# ── Bo'lim kodlari — session ``code`` dan deterministik variantlar ────────────
def _setup_code(code) -> str:
    return code


def _ga_code(code) -> str:
    return f"{code}2"


def _reg_code(code) -> str:
    return f"{code}3"


# ══════════════════════════════════════════════════════════════════════════════
# 0. LOGIN — bir marta, butun seans uchun
# ══════════════════════════════════════════════════════════════════════════════
@allure.epic("Модератор")
@allure.feature("Runner — seans")
@allure.title("Login — admin bilan bir marta kirish (butun runner uchun)")
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
@allure.title("Setup: Валюта — yangi valyuta")
def test_019_setup_valyuta(session_page: Page, code) -> None:
    setup_valyuta(session_page, _setup_code(code))


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


# ══════════════════════════════════════════════════════════════════════════════
# II. GROUP A — supplier/client, userlar, hamkorlik, tovar biriktirish, zakaz
#     Setup bo'limi admin bilan tugadi — Group A refs/supplier/... admin'da davom
#     etadi (o'z {code}2 kodi bilan). Faqat zakaz/status bosqichlarida rol almashadi.
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
    # linking haqiqatda biriktirgan nomni qaytaradi — zakaz aynan shuni qidiradi
    runner_state["ga_product_name"] = product_name


@allure.epic("Клиент")
@allure.feature("Group A")
@allure.title("Group A: Заказ — klient foydalanuvchisi nomidan yaratish")
def test_217_ga_zakaz(session_page: Page, code, runner_state) -> None:
    """Zakaz faqat klient rolida ko'rinadi — admin seansdan chiqib, group_a'da
    yaratilgan klient foydalanuvchisi bilan kiramiz."""
    ga = _ga_code(code)
    logout(session_page)
    authorization(session_page, email=f"client_user-{ga}@{COMPANY_CODE}", password="1")
    ga_zakaz(session_page, ga, product_name=runner_state.get("ga_product_name"))


@allure.epic("Поставщик")
@allure.feature("Group A")
@allure.title("Group A: Статус заказа — postavshik nomidan Новый → Завершен")
def test_218_ga_zakaz_status(session_page: Page, code) -> None:
    """Status faqat postavshik rolida o'zgartiriladi — klient seansdan chiqib,
    group_a'da yaratilgan postavshik foydalanuvchisi bilan kiramiz."""
    ga = _ga_code(code)
    logout(session_page)
    authorization(session_page, email=f"supplier_user-{ga}@{COMPANY_CODE}", password="1")
    ga_zakaz_status(session_page, ga)


# ══════════════════════════════════════════════════════════════════════════════
# III. REGRESSION — barcha modullar to'liq CRUD
#      Group A postavshik user seansida tugadi — admin'ga qaytamiz.
# ══════════════════════════════════════════════════════════════════════════════
@allure.epic("Модератор")
@allure.feature("Runner — seans")
@allure.title("Regression oldidan — admin'ga qayta kirish")
def test_400_login_admin_for_regression(session_page: Page) -> None:
    """Group A rol almashgan seansda tugadi — regression admin talab qiladi."""
    logout(session_page)
    authorization(session_page)


# ── 1. Регион ─────────────────────────────────────────────────────────────────
@allure.epic("Модератор")
@allure.feature("Регион")
@allure.title("Регион: Создание")
def test_410_region_create(session_page: Page, code) -> None:
    reg = _reg_code(code)
    # Default Region-{reg} nomi 2-bo'limdagi ensure_refs bilan to'qnashadi —
    # basic create alohida nom oladi
    setup_region(session_page, reg, name=f"Region-basic-{reg}")


# 411-416: bir xil imzoli CRUD amallari — parametrize bilan bitta testga siqilgan.
# Har biri baribir ALOHIDA Allure test bo'lib qoladi; TARTIB o'zgarmaydi (ro'yxat
# tartibi = avvalgi test_411..416): full → edit → view → delete → status → duplicate.
_REGION_CRUD = [
    ("full",      "Создание — barcha maydonlar bilan", run_region_full),
    ("edit",      "Редактирование",                    run_region_edit),
    ("view",      "Просмотр",                          run_region_view),
    ("delete",    "Удаление",                          run_region_delete),
    ("status",    "Статус — Неактивный/Активный",      run_region_status),
    ("duplicate", "Дубликат — nom bilan xatolik",      run_region_duplicate),
]


@allure.epic("Модератор")
@allure.feature("Регион")
@pytest.mark.parametrize(
    "title, run",
    [(c[1], c[2]) for c in _REGION_CRUD],
    ids=[c[0] for c in _REGION_CRUD],
)
def test_411_region_crud(session_page: Page, code, title, run) -> None:
    allure.dynamic.title(f"Регион: {title}")
    run(session_page, _reg_code(code))


# ── 2. Продукт ────────────────────────────────────────────────────────────────
@allure.epic("Модератор")
@allure.feature("Продукт")
@allure.title("Продукт: Создание (+ ma'lumotnomalar)")
def test_420_product_create(session_page: Page, code) -> None:
    reg = _reg_code(code)
    ensure_product_refs(session_page, reg)  # Region/MCHJ/Industry/Category/Manufacturer
    setup_product(session_page, reg)


_PRODUCT_CRUD = [
    ("full",   "Создание — barcha maydonlar bilan", run_product_full),
    ("edit",   "Редактирование",                    run_product_edit),
    ("view",   "Просмотр",                          run_product_view),
    ("delete", "Удаление",                          run_product_delete),
    ("status", "Статус — Пассивный/Активный",       run_product_status),
]


@allure.epic("Модератор")
@allure.feature("Продукт")
@pytest.mark.parametrize(
    "title, run",
    [(c[1], c[2]) for c in _PRODUCT_CRUD],
    ids=[c[0] for c in _PRODUCT_CRUD],
)
def test_421_product_crud(session_page: Page, code, title, run) -> None:
    allure.dynamic.title(f"Продукт: {title}")
    run(session_page, _reg_code(code))


# ── 3. Поставщик ──────────────────────────────────────────────────────────────
@allure.epic("Модератор")
@allure.feature("Поставщик")
@allure.title("Поставщик: Создание (+ ma'lumotnomalar)")
def test_430_supplier_create(session_page: Page, code) -> None:
    reg = _reg_code(code)
    ensure_refs(session_page, reg)  # Region/MCHJ/Industry/Category
    setup_supplier(session_page, reg)


_SUPPLIER_CRUD = [
    ("full",      "Создание — barcha maydonlar bilan", run_supplier_full),
    ("edit",      "Редактирование",                    run_supplier_edit),
    ("view",      "Просмотр",                          run_supplier_view),
    ("delete",    "Удаление",                          run_supplier_delete),
    ("status",    "Статус — Пассивный/Активный",       run_supplier_status),
    ("duplicate", "Дубликат — nom/ИНН bilan xatolik",  run_supplier_duplicate),
]


@allure.epic("Модератор")
@allure.feature("Поставщик")
@pytest.mark.parametrize(
    "title, run",
    [(c[1], c[2]) for c in _SUPPLIER_CRUD],
    ids=[c[0] for c in _SUPPLIER_CRUD],
)
def test_431_supplier_crud(session_page: Page, code, title, run) -> None:
    allure.dynamic.title(f"Поставщик: {title}")
    run(session_page, _reg_code(code))


# ── 4. Клиент ─────────────────────────────────────────────────────────────────
@allure.epic("Модератор")
@allure.feature("Клиент")
@allure.title("Клиент: Создание")
def test_440_client_create(session_page: Page, code) -> None:
    setup_client(session_page, _reg_code(code))


_CLIENT_CRUD = [
    ("full",      "Создание — barcha maydonlar bilan", run_client_full),
    ("edit",      "Редактирование",                    run_client_edit),
    ("view",      "Просмотр",                          run_client_view),
    ("delete",    "Удаление",                          run_client_delete),
    ("status",    "Статус — Пассивный/Активный",       run_client_status),
    ("duplicate", "Дубликат — nom/ИНН bilan xatolik",  run_client_duplicate),
]


@allure.epic("Модератор")
@allure.feature("Клиент")
@pytest.mark.parametrize(
    "title, run",
    [(c[1], c[2]) for c in _CLIENT_CRUD],
    ids=[c[0] for c in _CLIENT_CRUD],
)
def test_441_client_crud(session_page: Page, code, title, run) -> None:
    allure.dynamic.title(f"Клиент: {title}")
    run(session_page, _reg_code(code))


# ── 5. Юридическое лицо ───────────────────────────────────────────────────────
@allure.epic("Модератор")
@allure.feature("Юридическое лицо")
@allure.title("Юр.лицо: Создание")
def test_450_legal_person_create(session_page: Page, code) -> None:
    setup_legal_person(session_page, _reg_code(code))


_LEGAL_PERSON_CRUD = [
    ("full",      "Создание — barcha maydonlar bilan", run_legal_person_full),
    ("edit",      "Редактирование",                    run_legal_person_edit),
    ("view",      "Просмотр",                          run_legal_person_view),
    ("delete",    "Удаление",                          run_legal_person_delete),
    ("status",    "Статус — Пассивный/Активный",       run_legal_person_status),
    ("duplicate", "Дубликат — nom/ИНН bilan xatolik",  run_legal_person_duplicate),
]


@allure.epic("Модератор")
@allure.feature("Юридическое лицо")
@pytest.mark.parametrize(
    "title, run",
    [(c[1], c[2]) for c in _LEGAL_PERSON_CRUD],
    ids=[c[0] for c in _LEGAL_PERSON_CRUD],
)
def test_451_legal_person_crud(session_page: Page, code, title, run) -> None:
    allure.dynamic.title(f"Юр.лицо: {title}")
    run(session_page, _reg_code(code))


# ── 6. Валюта ─────────────────────────────────────────────────────────────────
@allure.epic("Модератор")
@allure.feature("Валюта")
@allure.title("Валюта: Создание")
def test_460_valyuta_create(session_page: Page, code) -> None:
    setup_valyuta(session_page, _reg_code(code))


_VALYUTA_CRUD = [
    ("full",              "Создание — barcha maydonlar bilan", run_valyuta_full),
    ("edit",              "Редактирование",                    run_valyuta_edit),
    ("view",              "Просмотр",                          run_valyuta_view),
    ("delete",            "Удаление",                          run_valyuta_delete),
    ("status_deactivate", "Статус — деактивация",              run_valyuta_status_deactivate),
    ("status_activate",   "Статус — активация",                run_valyuta_status_activate),
    ("duplicate",         "Дубликат — Код bilan xatolik",      run_valyuta_duplicate),
]


@allure.epic("Модератор")
@allure.feature("Валюта")
@pytest.mark.parametrize(
    "title, run",
    [(c[1], c[2]) for c in _VALYUTA_CRUD],
    ids=[c[0] for c in _VALYUTA_CRUD],
)
def test_461_valyuta_crud(session_page: Page, code, title, run) -> None:
    allure.dynamic.title(f"Валюта: {title}")
    run(session_page, _reg_code(code))


# ── 7. Конкурс ────────────────────────────────────────────────────────────────
@allure.epic("Модератор")
@allure.feature("Конкурс")
@allure.title("Конкурс: Создание (region bilan)")
def test_470_konkurs_create(session_page: Page, code, runner_state) -> None:
    reg = _reg_code(code)
    region = ensure_konkurs_region(session_page, reg)
    runner_state["konkurs_region"] = region
    setup_konkurs(session_page, reg, region=region)


@allure.epic("Модератор")
@allure.feature("Конкурс")
@allure.title("Конкурс: Создание — barcha maydonlar bilan")
def test_471_konkurs_full(session_page: Page, code, runner_state) -> None:
    run_konkurs_full(session_page, _reg_code(code), region=runner_state.get("konkurs_region"))


_KONKURS_CRUD = [
    ("edit",   "Редактирование",                      run_konkurs_edit),
    ("view",   "Просмотр",                            run_konkurs_view),
    ("delete", "Удаление",                            run_konkurs_delete),
    ("status", "Статус — Черновик → Активный → Завершен", run_konkurs_status),
]


@allure.epic("Модератор")
@allure.feature("Конкурс")
@pytest.mark.parametrize(
    "title, run",
    [(c[1], c[2]) for c in _KONKURS_CRUD],
    ids=[c[0] for c in _KONKURS_CRUD],
)
def test_472_konkurs_crud(session_page: Page, code, title, run) -> None:
    allure.dynamic.title(f"Конкурс: {title}")
    run(session_page, _reg_code(code))


# ── 8. Бонусная система ───────────────────────────────────────────────────────
@allure.epic("Модератор")
@allure.feature("Бонусная система")
@allure.title("Бонус: Создание")
def test_480_bonus_create(session_page: Page, code) -> None:
    setup_bonus(session_page, _reg_code(code))


_BONUS_CRUD = [
    ("full",   "Создание — barcha maydonlar bilan", run_bonus_full),
    ("edit",   "Редактирование",                    run_bonus_edit),
    ("view",   "Просмотр",                          run_bonus_view),
    ("delete", "Удаление",                          run_bonus_delete),
    ("status", "Статус — Неактивный/Активный",      run_bonus_status),
]


@allure.epic("Модератор")
@allure.feature("Бонусная система")
@pytest.mark.parametrize(
    "title, run",
    [(c[1], c[2]) for c in _BONUS_CRUD],
    ids=[c[0] for c in _BONUS_CRUD],
)
def test_481_bonus_crud(session_page: Page, code, title, run) -> None:
    allure.dynamic.title(f"Бонус: {title}")
    run(session_page, _reg_code(code))


# ── 9. Территория ─────────────────────────────────────────────────────────────
@allure.epic("Модератор")
@allure.feature("Территория")
@allure.title("Территория: Создание")
def test_490_territory_create(session_page: Page, code) -> None:
    setup_territory(session_page, _reg_code(code))


_TERRITORY_CRUD = [
    ("edit",   "Редактирование",               run_territory_edit),
    ("view",   "Просмотр",                     run_territory_view),
    ("delete", "Удаление",                     run_territory_delete),
    ("status", "Статус — Неактивный/Активный", run_territory_status),
]


@allure.epic("Модератор")
@allure.feature("Территория")
@pytest.mark.parametrize(
    "title, run",
    [(c[1], c[2]) for c in _TERRITORY_CRUD],
    ids=[c[0] for c in _TERRITORY_CRUD],
)
def test_491_territory_crud(session_page: Page, code, title, run) -> None:
    allure.dynamic.title(f"Территория: {title}")
    run(session_page, _reg_code(code))


# ── 10. Вопрос ────────────────────────────────────────────────────────────────
@allure.epic("Модератор")
@allure.feature("Вопрос")
@allure.title("Вопрос: Создание")
def test_500_vaprost_create(session_page: Page, code) -> None:
    setup_vaprost(session_page, _reg_code(code))


_VAPROST_CRUD = [
    ("full",      "Создание — barcha maydonlar bilan", run_vaprost_full),
    ("edit",      "Редактирование",                    run_vaprost_edit),
    ("view",      "Просмотр",                          run_vaprost_view),
    ("delete",    "Удаление",                          run_vaprost_delete),
    ("status",    "Статус — Неактивный/Активный",      run_vaprost_status),
    ("duplicate", "Дубликат — nom bilan xatolik",      run_vaprost_duplicate),
]


@allure.epic("Модератор")
@allure.feature("Вопрос")
@pytest.mark.parametrize(
    "title, run",
    [(c[1], c[2]) for c in _VAPROST_CRUD],
    ids=[c[0] for c in _VAPROST_CRUD],
)
def test_501_vaprost_crud(session_page: Page, code, title, run) -> None:
    allure.dynamic.title(f"Вопрос: {title}")
    run(session_page, _reg_code(code))


# ── 11. Опросник ──────────────────────────────────────────────────────────────
@allure.epic("Модератор")
@allure.feature("Опросник")
@allure.title("Опросник: Создание")
def test_510_oprosniki_create(session_page: Page, code) -> None:
    setup_oprosniki(session_page, _reg_code(code))


_OPROSNIKI_CRUD = [
    ("full",      "Создание — barcha maydonlar bilan",                run_oprosniki_full),
    ("edit",      "Редактирование",                                   run_oprosniki_edit),
    ("view",      "Просмотр",                                         run_oprosniki_view),
    ("delete",    "Удаление",                                         run_oprosniki_delete),
    ("status",    "Статус — Неактивный/Активный",                     run_oprosniki_status),
    ("duplicate", "Дубликат — nom bilan xatolik",                     run_oprosniki_duplicate),
    ("attach",    "Прикрепление вопросов — biriktirish/ajratish",     run_oprosniki_attach),
]


@allure.epic("Модератор")
@allure.feature("Опросник")
@pytest.mark.parametrize(
    "title, run",
    [(c[1], c[2]) for c in _OPROSNIKI_CRUD],
    ids=[c[0] for c in _OPROSNIKI_CRUD],
)
def test_511_oprosniki_crud(session_page: Page, code, title, run) -> None:
    allure.dynamic.title(f"Опросник: {title}")
    run(session_page, _reg_code(code))


# ── 12. Шаблон отчета ─────────────────────────────────────────────────────────
@allure.epic("Модератор")
@allure.feature("Шаблон отчета")
@allure.title("Шаблон: Создание")
def test_520_shablon_create(session_page: Page, code) -> None:
    setup_shablon(session_page, _reg_code(code))


_SHABLON_CRUD = [
    ("full",   "Создание — barcha maydonlar bilan", run_shablon_full),
    ("edit",   "Редактирование",                    run_shablon_edit),
    ("view",   "Просмотр",                          run_shablon_view),
    ("report", "Отчет — 'Открыть' sahifasi",        run_shablon_report),
    ("delete", "Удаление",                          run_shablon_delete),
    ("status", "Статус — Неактивный/Активный",      run_shablon_status),
]


@allure.epic("Модератор")
@allure.feature("Шаблон отчета")
@pytest.mark.parametrize(
    "title, run",
    [(c[1], c[2]) for c in _SHABLON_CRUD],
    ids=[c[0] for c in _SHABLON_CRUD],
)
def test_521_shablon_crud(session_page: Page, code, title, run) -> None:
    allure.dynamic.title(f"Шаблон: {title}")
    run(session_page, _reg_code(code))
