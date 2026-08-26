"""REGRESSION bo'limi runneri — barcha ma'lumotnoma modullarining to'liq CRUD
testlari ALOHIDA Allure testlar bo'lib, bitta seansda (bitta admin login)
ketma-ket ishga tushadi.

NEGA ALOHIDA FAYL
-----------------
Ilgari setup + group_a + regression bitta ``tests/test_all_runner.py`` da edi.
Endi bo'limlar TURLI jadvalda ishlaydi — regression og'ir va kamdan-kam
(masalan kuniga 2 marta). Batafsil: ``tests/test_setup/test_all_setup.py``.

DIZAYN
------
- **Bitta seans / admin login.** ``test_000_login_admin`` avval ``logout`` qiladi
  (oldingi bo'lim rol almashgan bo'lishi mumkin — kunlik "hammasi" run'da
  group_a postavshik user'da tugaydi), keyin admin bilan kiradi. Alohida
  ishlaganda logout guardlangan (jim o'tadi).
- **Kod varianti.** Regression ``{code}3`` ishlatadi — setup (code) va group_a
  ({code}2) bilan to'qnashmaydi.
- **O'ZINI TA'MINLAYDI.** Har modul o'z create testida ma'lumotnomalarni yaratadi
  (ensure_refs / ensure_product_refs / ensure_konkurs_region).

ISHGA TUSHIRISH
---------------
    python -m pytest tests/test_regression/test_all_regression.py -v
"""
import allure
import pytest
from playwright.sync_api import Page

from flows.flow_authorization import authorization, logout

from tests.test_setup.test_region import run_region as setup_region
from tests.test_setup.test_product import run_product as setup_product
from tests.test_setup.test_supplier import run_supplier as setup_supplier, ensure_refs
from tests.test_setup.test_client import run_client as setup_client
from tests.test_setup.test_legal_person import run_legal_person as setup_legal_person
from tests.test_setup.test_currency import run_currency as setup_currency
from tests.test_setup.test_konkurs import run_konkurs as setup_konkurs
from tests.test_setup.test_bonus import run_bonus as setup_bonus
from tests.test_setup.test_territory import run_territory as setup_territory
from tests.test_setup.test_vaprost import run_vaprost as setup_vaprost
from tests.test_setup.test_oprosniki import run_oprosniki as setup_oprosniki
from tests.test_setup.test_shablon import run_shablon as setup_shablon

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
from tests.test_regression.test_currency import (
    run_currency_delete, run_currency_duplicate, run_currency_edit,
    run_currency_full, run_currency_status, run_currency_view,
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


def _reg_code(code) -> str:
    """Regression bo'limi kod varianti — setup (code) va group_a ({code}2) bilan
    to'qnashmaslik uchun {code}3."""
    return f"{code}3"


# ══════════════════════════════════════════════════════════════════════════════
# 0. LOGIN — admin (oldingi bo'lim rol almashgan bo'lishi mumkin → avval logout)
# ══════════════════════════════════════════════════════════════════════════════
@allure.epic("Модератор")
@allure.feature("Runner — seans")
@allure.title("Login — admin bilan kirish (butun regression runner uchun)")
def test_000_login_admin(session_page: Page) -> None:
    """Regression admin talab qiladi. Kunlik "hammasi" run'da group_a postavshik
    user seansida tugaydi — shuning uchun avval logout, keyin admin login.
    Alohida ishlaganda logout guardlangan (jim o'tadi)."""
    logout(session_page)
    authorization(session_page)


# ── 1. Регион ─────────────────────────────────────────────────────────────────
@allure.epic("Модератор")
@allure.feature("Регион")
@allure.title("Регион: Создание")
def test_410_region_create(session_page: Page, code) -> None:
    reg = _reg_code(code)
    # Default Region-{reg} nomi ensure_refs bilan to'qnashadi — basic create
    # alohida nom oladi
    setup_region(session_page, reg, name=f"Region-basic-{reg}")


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
def test_460_currency_create(session_page: Page, code) -> None:
    setup_currency(session_page, _reg_code(code))


_VALYUTA_CRUD = [
    ("full",      "Создание — barcha maydonlar bilan", run_currency_full),
    ("edit",      "Редактирование",                    run_currency_edit),
    ("view",      "Просмотр",                          run_currency_view),
    ("delete",    "Удаление",                          run_currency_delete),
    ("status",    "Статус — Неактивный/Активный",      run_currency_status),
    ("duplicate", "Дубликат — Код bilan xatolik",      run_currency_duplicate),
]


@allure.epic("Модератор")
@allure.feature("Валюта")
@pytest.mark.parametrize(
    "title, run",
    [(c[1], c[2]) for c in _VALYUTA_CRUD],
    ids=[c[0] for c in _VALYUTA_CRUD],
)
def test_461_currency_crud(session_page: Page, code, title, run) -> None:
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
    ("edit",   "Редактирование",                          run_konkurs_edit),
    ("view",   "Просмотр",                                run_konkurs_view),
    ("delete", "Удаление",                                run_konkurs_delete),
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
    ("full",      "Создание — barcha maydonlar bilan",            run_oprosniki_full),
    ("edit",      "Редактирование",                               run_oprosniki_edit),
    ("view",      "Просмотр",                                     run_oprosniki_view),
    ("delete",    "Удаление",                                     run_oprosniki_delete),
    ("status",    "Статус — Неактивный/Активный",                 run_oprosniki_status),
    ("duplicate", "Дубликат — nom bilan xatolik",                 run_oprosniki_duplicate),
    ("attach",    "Прикрепление вопросов — biriktirish/ajratish", run_oprosniki_attach),
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
