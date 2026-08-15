"""Main ("Главное") bo'limi uchun umumiy runner — test_main ичидаги barcha testlar
ALOHIDA Allure testlar bo'lib, bitta seansda (bitta admin login) ketma-ket ishga
tushadi. test_all_document_runner.py / test_all_runner.py bilan bir xil dizayn
(2026-08-10 da mega-testdan alohida test_* larga bo'lindi).

DIZAYN
------
- **Bitta seans / bitta login.** Barcha testlar session-scope ``session_page``
  fixture'ini oladi — butun fayl uchun YAGONA browser+context+page. ``test_000``
  bir marta admin bilan kiradi; keyingi testlar shu ochiq seansdan foydalanadi.
  Main modullar ADMIN rolida ishlaydi (rol almashish yo'q) — bitta login yetadi.
- **Tartib.** Testlar BITTA modulda joylashgani uchun pytest ularni DEFINITSIYA
  tartibida bajaradi. Raqamli prefiks (``test_010_...``) o'qishni osonlashtiradi.
- **Alohida run_* funksiyalari.** Har modul o'z ``run_...`` biznes logikasini
  eksport qiladi (login qilinganini kutadi) — runner ularni session_page bilan
  chaqiradi. Individual ``test_...`` fayllar (har biri o'z login bilan) DEBUG uchun.
- **Kod.** Session ``code`` to'g'ridan-to'g'ri ishlatiladi — har modul o'z prefiksi
  bilan (org-*, Role-*, User-*, ...) nom yasagani uchun bir seansda to'qnashmaydi.

ISHGA TUSHIRISH
---------------
    python -m pytest tests/test_main/test_all_main.py -v \
        --alluredir=test-results/allure-results
"""
import allure
from playwright.sync_api import Page

from flows.flow_authorization import authorization

# --- Организации ---
from tests.test_main.test_organization import (
    run_organization, run_organization_delete, run_organization_duplicate,
    run_organization_edit, run_organization_minimal, run_organization_status,
    run_organization_view,
)
# --- Роли ---
from tests.test_main.test_role import (
    run_role, run_role_delete, run_role_duplicate, run_role_edit,
    run_role_minimal, run_role_status, run_role_view,
)
# --- Пользователи ---
from tests.test_main.test_polzovatel import (
    run_user, run_user_delete, run_user_edit, run_user_full,
    run_user_status, run_user_view,
)
# --- Объявления ---
from tests.test_main.test_announcement import (
    run_announcement, run_announcement_delete, run_announcement_edit,
    run_announcement_full, run_announcement_publish, run_announcement_view,
)
# --- Клиенты OAuth2 ---
from tests.test_main.test_company_client import (
    run_company_client, run_company_client_delete, run_company_client_edit,
    run_company_client_full,
)
# --- Шаблоны отчетов ---
from tests.test_main.test_report_template import (
    run_report_template, run_report_template_delete, run_report_template_edit,
    run_report_template_negative, run_report_template_status,
)
# --- Перевод строки таблицы ---
from tests.test_main.test_table_translate import run_table_translate
# --- Настройка ---
from tests.test_main.test_settings import run_settings


# ══════════════════════════════════════════════════════════════════════════════
# 0. LOGIN — bir marta, butun seans uchun
# ══════════════════════════════════════════════════════════════════════════════
@allure.epic("Модератор")
@allure.feature("Runner — seans")
@allure.title("Login — admin bilan bir marta kirish (butun main runner uchun)")
def test_000_login_admin(session_page: Page) -> None:
    """Butun runner uchun YAGONA login. Keyingi barcha testlar shu ochiq
    session_page seansidan foydalanadi — qayta login qilinmaydi."""
    authorization(session_page)


# ══════════════════════════════════════════════════════════════════════════════
# I. ОРГАНИЗАЦИИ — to'liq CRUD + dubl
# ══════════════════════════════════════════════════════════════════════════════
@allure.epic("Модератор")
@allure.feature("Организации")
@allure.title("Организации: Создание")
def test_010_organization_create(session_page: Page, code) -> None:
    run_organization(session_page, code)


@allure.epic("Модератор")
@allure.feature("Организации")
@allure.title("Организации: Создание — minimal maydonlar")
def test_011_organization_minimal(session_page: Page, code) -> None:
    run_organization_minimal(session_page, code)


@allure.epic("Модератор")
@allure.feature("Организации")
@allure.title("Организации: Просмотр")
def test_012_organization_view(session_page: Page, code) -> None:
    run_organization_view(session_page, code)


@allure.epic("Модератор")
@allure.feature("Организации")
@allure.title("Организации: Редактирование")
def test_013_organization_edit(session_page: Page, code) -> None:
    run_organization_edit(session_page, code)


@allure.epic("Модератор")
@allure.feature("Организации")
@allure.title("Организации: Статус — Неактивный/Активный")
def test_014_organization_status(session_page: Page, code) -> None:
    run_organization_status(session_page, code)


@allure.epic("Модератор")
@allure.feature("Организации")
@allure.title("Организации: Удаление")
def test_015_organization_delete(session_page: Page, code) -> None:
    run_organization_delete(session_page, code)


@allure.epic("Модератор")
@allure.feature("Организации")
@allure.title("Организации: Дубликат — nom bilan xatolik")
def test_016_organization_duplicate(session_page: Page, code) -> None:
    run_organization_duplicate(session_page, code)


# ══════════════════════════════════════════════════════════════════════════════
# II. РОЛИ — to'liq CRUD + dubl
# ══════════════════════════════════════════════════════════════════════════════
@allure.epic("Модератор")
@allure.feature("Роли")
@allure.title("Роли: Создание")
def test_020_role_create(session_page: Page, code) -> None:
    run_role(session_page, code)


@allure.epic("Модератор")
@allure.feature("Роли")
@allure.title("Роли: Создание — minimal maydonlar")
def test_021_role_minimal(session_page: Page, code) -> None:
    run_role_minimal(session_page, code)


@allure.epic("Модератор")
@allure.feature("Роли")
@allure.title("Роли: Просмотр")
def test_022_role_view(session_page: Page, code) -> None:
    run_role_view(session_page, code)


@allure.epic("Модератор")
@allure.feature("Роли")
@allure.title("Роли: Редактирование")
def test_023_role_edit(session_page: Page, code) -> None:
    run_role_edit(session_page, code)


@allure.epic("Модератор")
@allure.feature("Роли")
@allure.title("Роли: Статус — Неактивный/Активный")
def test_024_role_status(session_page: Page, code) -> None:
    run_role_status(session_page, code)


@allure.epic("Модератор")
@allure.feature("Роли")
@allure.title("Роли: Удаление")
def test_025_role_delete(session_page: Page, code) -> None:
    run_role_delete(session_page, code)


@allure.epic("Модератор")
@allure.feature("Роли")
@allure.title("Роли: Дубликат — nom bilan xatolik")
def test_026_role_duplicate(session_page: Page, code) -> None:
    run_role_duplicate(session_page, code)


# ══════════════════════════════════════════════════════════════════════════════
# III. ПОЛЬЗОВАТЕЛИ — to'liq CRUD
# ══════════════════════════════════════════════════════════════════════════════
@allure.epic("Модератор")
@allure.feature("Пользователи")
@allure.title("Пользователи: Создание")
def test_030_user_create(session_page: Page, code) -> None:
    run_user(session_page, code)


@allure.epic("Модератор")
@allure.feature("Пользователи")
@allure.title("Пользователи: Создание — barcha maydonlar")
def test_031_user_full(session_page: Page, code) -> None:
    run_user_full(session_page, code)


@allure.epic("Модератор")
@allure.feature("Пользователи")
@allure.title("Пользователи: Просмотр")
def test_032_user_view(session_page: Page, code) -> None:
    run_user_view(session_page, code)


@allure.epic("Модератор")
@allure.feature("Пользователи")
@allure.title("Пользователи: Редактирование")
def test_033_user_edit(session_page: Page, code) -> None:
    run_user_edit(session_page, code)


@allure.epic("Модератор")
@allure.feature("Пользователи")
@allure.title("Пользователи: Статус — Неактивный")
def test_034_user_status(session_page: Page, code) -> None:
    run_user_status(session_page, code)


@allure.epic("Модератор")
@allure.feature("Пользователи")
@allure.title("Пользователи: Удаление")
def test_035_user_delete(session_page: Page, code) -> None:
    run_user_delete(session_page, code)


# ══════════════════════════════════════════════════════════════════════════════
# IV. ОБЪЯВЛЕНИЯ — Черновик CRUD + публикация
# ══════════════════════════════════════════════════════════════════════════════
@allure.epic("Модератор")
@allure.feature("Объявления")
@allure.title("Объявления: Создание (Черновик)")
def test_040_announcement_create(session_page: Page, code) -> None:
    run_announcement(session_page, code)


@allure.epic("Модератор")
@allure.feature("Объявления")
@allure.title("Объявления: Создание — Отрасли bilan")
def test_041_announcement_full(session_page: Page, code) -> None:
    run_announcement_full(session_page, code)


@allure.epic("Модератор")
@allure.feature("Объявления")
@allure.title("Объявления: Просмотр")
def test_042_announcement_view(session_page: Page, code) -> None:
    run_announcement_view(session_page, code)


@allure.epic("Модератор")
@allure.feature("Объявления")
@allure.title("Объявления: Редактирование")
def test_043_announcement_edit(session_page: Page, code) -> None:
    run_announcement_edit(session_page, code)


@allure.epic("Модератор")
@allure.feature("Объявления")
@allure.title("Объявления: Публикация — статус Опубликовано")
def test_044_announcement_publish(session_page: Page, code) -> None:
    run_announcement_publish(session_page, code)


@allure.epic("Модератор")
@allure.feature("Объявления")
@allure.title("Объявления: Удаление")
def test_045_announcement_delete(session_page: Page, code) -> None:
    run_announcement_delete(session_page, code)


# ══════════════════════════════════════════════════════════════════════════════
# V. КЛИЕНТЫ OAuth2 — CRUD
# ══════════════════════════════════════════════════════════════════════════════
@allure.epic("Модератор")
@allure.feature("Клиенты OAuth2")
@allure.title("OAuth2: Создание")
def test_050_company_client_create(session_page: Page, code) -> None:
    run_company_client(session_page, code)


@allure.epic("Модератор")
@allure.feature("Клиенты OAuth2")
@allure.title("OAuth2: Создание — оба доступа (Read/Write)")
def test_051_company_client_full(session_page: Page, code) -> None:
    run_company_client_full(session_page, code)


@allure.epic("Модератор")
@allure.feature("Клиенты OAuth2")
@allure.title("OAuth2: Редактирование")
def test_052_company_client_edit(session_page: Page, code) -> None:
    run_company_client_edit(session_page, code)


@allure.epic("Модератор")
@allure.feature("Клиенты OAuth2")
@allure.title("OAuth2: Удаление")
def test_053_company_client_delete(session_page: Page, code) -> None:
    run_company_client_delete(session_page, code)


# ══════════════════════════════════════════════════════════════════════════════
# VI. ШАБЛОНЫ ОТЧЕТОВ — CRUD + status + negativ
# ══════════════════════════════════════════════════════════════════════════════
@allure.epic("Модератор")
@allure.feature("Шаблоны отчетов")
@allure.title("Шаблоны отчетов: Создание (.xlsx fayl bilan)")
def test_060_report_template_create(session_page: Page, code) -> None:
    run_report_template(session_page, code)


@allure.epic("Модератор")
@allure.feature("Шаблоны отчетов")
@allure.title("Шаблоны отчетов: Редактирование")
def test_061_report_template_edit(session_page: Page, code) -> None:
    run_report_template_edit(session_page, code)


@allure.epic("Модератор")
@allure.feature("Шаблоны отчетов")
@allure.title("Шаблоны отчетов: Статус — Неактивный/Активный")
def test_062_report_template_status(session_page: Page, code) -> None:
    run_report_template_status(session_page, code)


@allure.epic("Модератор")
@allure.feature("Шаблоны отчетов")
@allure.title("Шаблоны отчетов: Удаление")
def test_063_report_template_delete(session_page: Page, code) -> None:
    run_report_template_delete(session_page, code)


@allure.epic("Модератор")
@allure.feature("Шаблоны отчетов")
@allure.title("Шаблоны отчетов: Негатив — bo'sh forma bloklanadi")
def test_064_report_template_negative(session_page: Page) -> None:
    run_report_template_negative(session_page)


# ══════════════════════════════════════════════════════════════════════════════
# VII. ПЕРЕВОД СТРОКИ ТАБЛИЦЫ + НАСТРОЙКА
# ══════════════════════════════════════════════════════════════════════════════
@allure.epic("Модератор")
@allure.feature("Перевод строки таблицы")
@allure.title("Перевод строки таблицы: uz tarjima round-trip")
def test_070_table_translate(session_page: Page, code) -> None:
    run_table_translate(session_page, code)


@allure.epic("Модератор")
@allure.feature("Настройка")
@allure.title("Настройка: sozlamalar sahifasi (smoke, non-destructive)")
def test_080_settings(session_page: Page, code) -> None:
    run_settings(session_page, code)
