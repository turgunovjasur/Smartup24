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

Faqat shu faylni bersangiz duplikat bo'lmaydi. Bare ``pytest`` (butun repo)
individual ``test_...`` va ``test_..._all`` aggregatorlarni ham yig'adi —
ular DEBUG uchun qoladi, runner esa yagona "hammasini bir seansda" kirish nuqtasi.
"""
import time

import allure
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
    run_valyuta_full, run_valyuta_status, run_valyuta_view,
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


@allure.epic("Модератор")
@allure.feature("Регион")
@allure.title("Регион: Создание — barcha maydonlar bilan")
def test_411_region_full(session_page: Page, code) -> None:
    run_region_full(session_page, _reg_code(code))


@allure.epic("Модератор")
@allure.feature("Регион")
@allure.title("Регион: Редактирование")
def test_412_region_edit(session_page: Page, code) -> None:
    run_region_edit(session_page, _reg_code(code))


@allure.epic("Модератор")
@allure.feature("Регион")
@allure.title("Регион: Просмотр")
def test_413_region_view(session_page: Page, code) -> None:
    run_region_view(session_page, _reg_code(code))


@allure.epic("Модератор")
@allure.feature("Регион")
@allure.title("Регион: Удаление")
def test_414_region_delete(session_page: Page, code) -> None:
    run_region_delete(session_page, _reg_code(code))


@allure.epic("Модератор")
@allure.feature("Регион")
@allure.title("Регион: Статус — Неактивный/Активный")
def test_415_region_status(session_page: Page, code) -> None:
    run_region_status(session_page, _reg_code(code))


@allure.epic("Модератор")
@allure.feature("Регион")
@allure.title("Регион: Дубликат — nom bilan xatolik")
def test_416_region_duplicate(session_page: Page, code) -> None:
    run_region_duplicate(session_page, _reg_code(code))


# ── 2. Продукт ────────────────────────────────────────────────────────────────
@allure.epic("Модератор")
@allure.feature("Продукт")
@allure.title("Продукт: Создание (+ ma'lumotnomalar)")
def test_420_product_create(session_page: Page, code) -> None:
    reg = _reg_code(code)
    ensure_product_refs(session_page, reg)  # Region/MCHJ/Industry/Category/Manufacturer
    setup_product(session_page, reg)


@allure.epic("Модератор")
@allure.feature("Продукт")
@allure.title("Продукт: Создание — barcha maydonlar bilan")
def test_421_product_full(session_page: Page, code) -> None:
    run_product_full(session_page, _reg_code(code))


@allure.epic("Модератор")
@allure.feature("Продукт")
@allure.title("Продукт: Редактирование")
def test_422_product_edit(session_page: Page, code) -> None:
    run_product_edit(session_page, _reg_code(code))


@allure.epic("Модератор")
@allure.feature("Продукт")
@allure.title("Продукт: Просмотр")
def test_423_product_view(session_page: Page, code) -> None:
    run_product_view(session_page, _reg_code(code))


@allure.epic("Модератор")
@allure.feature("Продукт")
@allure.title("Продукт: Удаление")
def test_424_product_delete(session_page: Page, code) -> None:
    run_product_delete(session_page, _reg_code(code))


@allure.epic("Модератор")
@allure.feature("Продукт")
@allure.title("Продукт: Статус — Пассивный/Активный")
def test_425_product_status(session_page: Page, code) -> None:
    run_product_status(session_page, _reg_code(code))


# ── 3. Поставщик ──────────────────────────────────────────────────────────────
@allure.epic("Модератор")
@allure.feature("Поставщик")
@allure.title("Поставщик: Создание (+ ma'lumotnomalar)")
def test_430_supplier_create(session_page: Page, code) -> None:
    reg = _reg_code(code)
    ensure_refs(session_page, reg)  # Region/MCHJ/Industry/Category
    setup_supplier(session_page, reg)


@allure.epic("Модератор")
@allure.feature("Поставщик")
@allure.title("Поставщик: Создание — barcha maydonlar bilan")
def test_431_supplier_full(session_page: Page, code) -> None:
    run_supplier_full(session_page, _reg_code(code))


@allure.epic("Модератор")
@allure.feature("Поставщик")
@allure.title("Поставщик: Редактирование")
def test_432_supplier_edit(session_page: Page, code) -> None:
    run_supplier_edit(session_page, _reg_code(code))


@allure.epic("Модератор")
@allure.feature("Поставщик")
@allure.title("Поставщик: Просмотр")
def test_433_supplier_view(session_page: Page, code) -> None:
    run_supplier_view(session_page, _reg_code(code))


@allure.epic("Модератор")
@allure.feature("Поставщик")
@allure.title("Поставщик: Удаление")
def test_434_supplier_delete(session_page: Page, code) -> None:
    run_supplier_delete(session_page, _reg_code(code))


@allure.epic("Модератор")
@allure.feature("Поставщик")
@allure.title("Поставщик: Статус — Пассивный/Активный")
def test_435_supplier_status(session_page: Page, code) -> None:
    run_supplier_status(session_page, _reg_code(code))


@allure.epic("Модератор")
@allure.feature("Поставщик")
@allure.title("Поставщик: Дубликат — nom/ИНН bilan xatolik")
def test_436_supplier_duplicate(session_page: Page, code) -> None:
    run_supplier_duplicate(session_page, _reg_code(code))


# ── 4. Клиент ─────────────────────────────────────────────────────────────────
@allure.epic("Модератор")
@allure.feature("Клиент")
@allure.title("Клиент: Создание")
def test_440_client_create(session_page: Page, code) -> None:
    setup_client(session_page, _reg_code(code))


@allure.epic("Модератор")
@allure.feature("Клиент")
@allure.title("Клиент: Создание — barcha maydonlar bilan")
def test_441_client_full(session_page: Page, code) -> None:
    run_client_full(session_page, _reg_code(code))


@allure.epic("Модератор")
@allure.feature("Клиент")
@allure.title("Клиент: Редактирование")
def test_442_client_edit(session_page: Page, code) -> None:
    run_client_edit(session_page, _reg_code(code))


@allure.epic("Модератор")
@allure.feature("Клиент")
@allure.title("Клиент: Просмотр")
def test_443_client_view(session_page: Page, code) -> None:
    run_client_view(session_page, _reg_code(code))


@allure.epic("Модератор")
@allure.feature("Клиент")
@allure.title("Клиент: Удаление")
def test_444_client_delete(session_page: Page, code) -> None:
    run_client_delete(session_page, _reg_code(code))


@allure.epic("Модератор")
@allure.feature("Клиент")
@allure.title("Клиент: Статус — Пассивный/Активный")
def test_445_client_status(session_page: Page, code) -> None:
    run_client_status(session_page, _reg_code(code))


@allure.epic("Модератор")
@allure.feature("Клиент")
@allure.title("Клиент: Дубликат — nom/ИНН bilan xatolik")
def test_446_client_duplicate(session_page: Page, code) -> None:
    run_client_duplicate(session_page, _reg_code(code))


# ── 5. Юридическое лицо ───────────────────────────────────────────────────────
@allure.epic("Модератор")
@allure.feature("Юридическое лицо")
@allure.title("Юр.лицо: Создание")
def test_450_legal_person_create(session_page: Page, code) -> None:
    setup_legal_person(session_page, _reg_code(code))


@allure.epic("Модератор")
@allure.feature("Юридическое лицо")
@allure.title("Юр.лицо: Создание — barcha maydonlar bilan")
def test_451_legal_person_full(session_page: Page, code) -> None:
    run_legal_person_full(session_page, _reg_code(code))


@allure.epic("Модератор")
@allure.feature("Юридическое лицо")
@allure.title("Юр.лицо: Редактирование")
def test_452_legal_person_edit(session_page: Page, code) -> None:
    run_legal_person_edit(session_page, _reg_code(code))


@allure.epic("Модератор")
@allure.feature("Юридическое лицо")
@allure.title("Юр.лицо: Просмотр")
def test_453_legal_person_view(session_page: Page, code) -> None:
    run_legal_person_view(session_page, _reg_code(code))


@allure.epic("Модератор")
@allure.feature("Юридическое лицо")
@allure.title("Юр.лицо: Удаление")
def test_454_legal_person_delete(session_page: Page, code) -> None:
    run_legal_person_delete(session_page, _reg_code(code))


@allure.epic("Модератор")
@allure.feature("Юридическое лицо")
@allure.title("Юр.лицо: Статус — Пассивный/Активный")
def test_455_legal_person_status(session_page: Page, code) -> None:
    run_legal_person_status(session_page, _reg_code(code))


@allure.epic("Модератор")
@allure.feature("Юридическое лицо")
@allure.title("Юр.лицо: Дубликат — nom/ИНН bilan xatolik")
def test_456_legal_person_duplicate(session_page: Page, code) -> None:
    run_legal_person_duplicate(session_page, _reg_code(code))


# ── 6. Валюта ─────────────────────────────────────────────────────────────────
@allure.epic("Модератор")
@allure.feature("Валюта")
@allure.title("Валюта: Создание")
def test_460_valyuta_create(session_page: Page, code) -> None:
    setup_valyuta(session_page, _reg_code(code))


@allure.epic("Модератор")
@allure.feature("Валюта")
@allure.title("Валюта: Создание — barcha maydonlar bilan")
def test_461_valyuta_full(session_page: Page, code) -> None:
    run_valyuta_full(session_page, _reg_code(code))


@allure.epic("Модератор")
@allure.feature("Валюта")
@allure.title("Валюта: Редактирование")
def test_462_valyuta_edit(session_page: Page, code) -> None:
    run_valyuta_edit(session_page, _reg_code(code))


@allure.epic("Модератор")
@allure.feature("Валюта")
@allure.title("Валюта: Просмотр")
def test_463_valyuta_view(session_page: Page, code) -> None:
    run_valyuta_view(session_page, _reg_code(code))


@allure.epic("Модератор")
@allure.feature("Валюта")
@allure.title("Валюта: Удаление")
def test_464_valyuta_delete(session_page: Page, code) -> None:
    run_valyuta_delete(session_page, _reg_code(code))


@allure.epic("Модератор")
@allure.feature("Валюта")
@allure.title("Валюта: Статус — Неактивный/Активный")
def test_465_valyuta_status(session_page: Page, code) -> None:
    run_valyuta_status(session_page, _reg_code(code))


@allure.epic("Модератор")
@allure.feature("Валюта")
@allure.title("Валюта: Дубликат — Код bilan xatolik")
def test_466_valyuta_duplicate(session_page: Page, code) -> None:
    run_valyuta_duplicate(session_page, _reg_code(code))


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


@allure.epic("Модератор")
@allure.feature("Конкурс")
@allure.title("Конкурс: Редактирование")
def test_472_konkurs_edit(session_page: Page, code) -> None:
    run_konkurs_edit(session_page, _reg_code(code))


@allure.epic("Модератор")
@allure.feature("Конкурс")
@allure.title("Конкурс: Просмотр")
def test_473_konkurs_view(session_page: Page, code) -> None:
    run_konkurs_view(session_page, _reg_code(code))


@allure.epic("Модератор")
@allure.feature("Конкурс")
@allure.title("Конкурс: Удаление")
def test_474_konkurs_delete(session_page: Page, code) -> None:
    run_konkurs_delete(session_page, _reg_code(code))


@allure.epic("Модератор")
@allure.feature("Конкурс")
@allure.title("Конкурс: Статус — Черновик → Активный → Завершен")
def test_475_konkurs_status(session_page: Page, code) -> None:
    run_konkurs_status(session_page, _reg_code(code))


# ── 8. Бонусная система ───────────────────────────────────────────────────────
@allure.epic("Модератор")
@allure.feature("Бонусная система")
@allure.title("Бонус: Создание")
def test_480_bonus_create(session_page: Page, code) -> None:
    setup_bonus(session_page, _reg_code(code))


@allure.epic("Модератор")
@allure.feature("Бонусная система")
@allure.title("Бонус: Создание — barcha maydonlar bilan")
def test_481_bonus_full(session_page: Page, code) -> None:
    run_bonus_full(session_page, _reg_code(code))


@allure.epic("Модератор")
@allure.feature("Бонусная система")
@allure.title("Бонус: Редактирование")
def test_482_bonus_edit(session_page: Page, code) -> None:
    run_bonus_edit(session_page, _reg_code(code))


@allure.epic("Модератор")
@allure.feature("Бонусная система")
@allure.title("Бонус: Просмотр")
def test_483_bonus_view(session_page: Page, code) -> None:
    run_bonus_view(session_page, _reg_code(code))


@allure.epic("Модератор")
@allure.feature("Бонусная система")
@allure.title("Бонус: Удаление")
def test_484_bonus_delete(session_page: Page, code) -> None:
    run_bonus_delete(session_page, _reg_code(code))


@allure.epic("Модератор")
@allure.feature("Бонусная система")
@allure.title("Бонус: Статус — Неактивный/Активный")
def test_485_bonus_status(session_page: Page, code) -> None:
    run_bonus_status(session_page, _reg_code(code))


# ── 9. Территория ─────────────────────────────────────────────────────────────
@allure.epic("Модератор")
@allure.feature("Территория")
@allure.title("Территория: Создание")
def test_490_territory_create(session_page: Page, code) -> None:
    setup_territory(session_page, _reg_code(code))


@allure.epic("Модератор")
@allure.feature("Территория")
@allure.title("Территория: Редактирование")
def test_491_territory_edit(session_page: Page, code) -> None:
    run_territory_edit(session_page, _reg_code(code))


@allure.epic("Модератор")
@allure.feature("Территория")
@allure.title("Территория: Просмотр")
def test_492_territory_view(session_page: Page, code) -> None:
    run_territory_view(session_page, _reg_code(code))


@allure.epic("Модератор")
@allure.feature("Территория")
@allure.title("Территория: Удаление")
def test_493_territory_delete(session_page: Page, code) -> None:
    run_territory_delete(session_page, _reg_code(code))


@allure.epic("Модератор")
@allure.feature("Территория")
@allure.title("Территория: Статус — Неактивный/Активный")
def test_494_territory_status(session_page: Page, code) -> None:
    run_territory_status(session_page, _reg_code(code))


# ── 10. Вопрос ────────────────────────────────────────────────────────────────
@allure.epic("Модератор")
@allure.feature("Вопрос")
@allure.title("Вопрос: Создание")
def test_500_vaprost_create(session_page: Page, code) -> None:
    setup_vaprost(session_page, _reg_code(code))


@allure.epic("Модератор")
@allure.feature("Вопрос")
@allure.title("Вопрос: Создание — barcha maydonlar bilan")
def test_501_vaprost_full(session_page: Page, code) -> None:
    run_vaprost_full(session_page, _reg_code(code))


@allure.epic("Модератор")
@allure.feature("Вопрос")
@allure.title("Вопрос: Редактирование")
def test_502_vaprost_edit(session_page: Page, code) -> None:
    run_vaprost_edit(session_page, _reg_code(code))


@allure.epic("Модератор")
@allure.feature("Вопрос")
@allure.title("Вопрос: Просмотр")
def test_503_vaprost_view(session_page: Page, code) -> None:
    run_vaprost_view(session_page, _reg_code(code))


@allure.epic("Модератор")
@allure.feature("Вопрос")
@allure.title("Вопрос: Удаление")
def test_504_vaprost_delete(session_page: Page, code) -> None:
    run_vaprost_delete(session_page, _reg_code(code))


@allure.epic("Модератор")
@allure.feature("Вопрос")
@allure.title("Вопрос: Статус — Неактивный/Активный")
def test_505_vaprost_status(session_page: Page, code) -> None:
    run_vaprost_status(session_page, _reg_code(code))


@allure.epic("Модератор")
@allure.feature("Вопрос")
@allure.title("Вопрос: Дубликат — nom bilan xatolik")
def test_506_vaprost_duplicate(session_page: Page, code) -> None:
    run_vaprost_duplicate(session_page, _reg_code(code))


# ── 11. Опросник ──────────────────────────────────────────────────────────────
@allure.epic("Модератор")
@allure.feature("Опросник")
@allure.title("Опросник: Создание")
def test_510_oprosniki_create(session_page: Page, code) -> None:
    setup_oprosniki(session_page, _reg_code(code))


@allure.epic("Модератор")
@allure.feature("Опросник")
@allure.title("Опросник: Создание — barcha maydonlar bilan")
def test_511_oprosniki_full(session_page: Page, code) -> None:
    run_oprosniki_full(session_page, _reg_code(code))


@allure.epic("Модератор")
@allure.feature("Опросник")
@allure.title("Опросник: Редактирование")
def test_512_oprosniki_edit(session_page: Page, code) -> None:
    run_oprosniki_edit(session_page, _reg_code(code))


@allure.epic("Модератор")
@allure.feature("Опросник")
@allure.title("Опросник: Просмотр")
def test_513_oprosniki_view(session_page: Page, code) -> None:
    run_oprosniki_view(session_page, _reg_code(code))


@allure.epic("Модератор")
@allure.feature("Опросник")
@allure.title("Опросник: Удаление")
def test_514_oprosniki_delete(session_page: Page, code) -> None:
    run_oprosniki_delete(session_page, _reg_code(code))


@allure.epic("Модератор")
@allure.feature("Опросник")
@allure.title("Опросник: Статус — Неактивный/Активный")
def test_515_oprosniki_status(session_page: Page, code) -> None:
    run_oprosniki_status(session_page, _reg_code(code))


@allure.epic("Модератор")
@allure.feature("Опросник")
@allure.title("Опросник: Дубликат — nom bilan xatolik")
def test_516_oprosniki_duplicate(session_page: Page, code) -> None:
    run_oprosniki_duplicate(session_page, _reg_code(code))


@allure.epic("Модератор")
@allure.feature("Опросник")
@allure.title("Опросник: Прикрепление вопросов — biriktirish/ajratish")
def test_517_oprosniki_attach(session_page: Page, code) -> None:
    run_oprosniki_attach(session_page, _reg_code(code))


# ── 12. Шаблон отчета ─────────────────────────────────────────────────────────
@allure.epic("Модератор")
@allure.feature("Шаблон отчета")
@allure.title("Шаблон: Создание")
def test_520_shablon_create(session_page: Page, code) -> None:
    setup_shablon(session_page, _reg_code(code))


@allure.epic("Модератор")
@allure.feature("Шаблон отчета")
@allure.title("Шаблон: Создание — barcha maydonlar bilan")
def test_521_shablon_full(session_page: Page, code) -> None:
    run_shablon_full(session_page, _reg_code(code))


@allure.epic("Модератор")
@allure.feature("Шаблон отчета")
@allure.title("Шаблон: Редактирование")
def test_522_shablon_edit(session_page: Page, code) -> None:
    run_shablon_edit(session_page, _reg_code(code))


@allure.epic("Модератор")
@allure.feature("Шаблон отчета")
@allure.title("Шаблон: Просмотр")
def test_523_shablon_view(session_page: Page, code) -> None:
    run_shablon_view(session_page, _reg_code(code))


@allure.epic("Модератор")
@allure.feature("Шаблон отчета")
@allure.title("Шаблон: Отчет — 'Открыть' sahifasi")
def test_524_shablon_report(session_page: Page, code) -> None:
    run_shablon_report(session_page, _reg_code(code))


@allure.epic("Модератор")
@allure.feature("Шаблон отчета")
@allure.title("Шаблон: Удаление")
def test_525_shablon_delete(session_page: Page, code) -> None:
    run_shablon_delete(session_page, _reg_code(code))


@allure.epic("Модератор")
@allure.feature("Шаблон отчета")
@allure.title("Шаблон: Статус — Неактивный/Активный")
def test_526_shablon_status(session_page: Page, code) -> None:
    run_shablon_status(session_page, _reg_code(code))
