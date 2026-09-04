"""Документы bo'limi uchun umumiy runner — test_document ичидаги barcha testlar
ALOHIDA Allure testlar bo'lib, bitta seansda (bitta admin login) ketma-ket ishga
tushadi. Root ``tests/test_all_runner.py`` bilan bir xil dizayn.

DIZAYN (test_all_runner.py bilan bir xil)
-----------------------------------------
- **Bitta seans / bitta login.** Barcha testlar session-scope ``session_page``
  fixture'ini oladi (conftest) — butun fayl uchun YAGONA browser+context+page.
  ``test_000_login_admin`` bir marta admin bilan kiradi; keyingi testlar shu
  ochiq seansdan foydalanadi. Barcha test_document testlari ADMIN rolida ishlaydi
  (rol almashish yo'q) — shuning uchun bitta login yetadi.
- **Tartib.** Testlar BITTA modulda joylashgani uchun pytest ularni DEFINITSIYA
  tartibida bajaradi. Raqamli prefiks (``test_010_...``) o'qishni osonlashtiradi.
- **Alohida run_* funksiyalari.** Har modul o'z ``run_...`` biznes logikasini
  eksport qiladi (login qilinganini kutadi) — runner ularni session_page bilan
  chaqiradi. Individual ``test_...`` fayllar (har biri o'z login bilan) DEBUG
  uchun qoladi.

MAXSUS HOLATLAR
---------------
- **Visit tartibi:** ``run_visit_check`` avval yuradi — u visit bajarib yangi lead
  hosil qiladi, shunda ``run_visit_led_shag`` uchun lead kafolatlanadi (manba
  ``test_visit_all`` bilan bir xil).
- **Recurrence / agent-tracking:** har biri O'Z agentini yaratadi va oxirida uni
  Неактивный qiladi (visitли agent o'chirilmaydi — child record). Bu ikki test
  manba fayllardagi ``test_recurrence_all`` / ``test_agent_visit_tracking`` zanjir
  tanasini AYNAN takrorlaydi (faqat ichki ``authorization`` olib tashlangan —
  seans allaqachon ochiq).
- **Mobil visit API:** ``run_visit_check`` va ``test_040_recurrence_full`` mobil
  visitni ``utils/base_api.py`` (VisitApi, ``requests``) orqali bajaradi — newman/
  Postman CLI bog'liqligi YO'Q, shuning uchun DOIM ishlaydi (avvalgi skip olib
  tashlangan).
- **route-analysis required_fields:** ilovada majburiy-sana validatsiyasi yo'q
  (bug) — ``run_required_fields`` ichida ``pytest.xfail`` chaqiriladi, shuning
  uchun bu test XFAIL bo'ladi (yiqilish EMAS; hujjatlashtirilgan holat).

ISHGA TUSHIRISH
---------------
    python -m pytest tests/test_document/test_all_document_runner.py -v \
        --alluredir=test-results/allure-results
    allure serve test-results/allure-results
"""
import allure
import pytest
from playwright.sync_api import Page

from flows.flow_authorization import authorization
from utils.base_page import BasePage

# --- Группа полей (CRUD + negativ) ---
from tests.test_document.test_field_group import (
    run_field_group, run_field_group_delete, run_field_group_duplicate,
    run_field_group_edit, run_field_group_required, run_field_group_status,
    run_field_group_subtypes,
)
# --- Анализ маршрутов (hisobot yuklab olish) ---
from tests.test_document.test_route_analysis import (
    REPORT_TYPES, run_download_success, run_plan_values, run_report_type,
    run_required_fields, run_structure,
)
# --- Визиты ---
from tests.test_document.test_visit import (
    run_visit_criteria_roundtrip, run_visit_functions_roundtrip,
    run_visit_roles_overview, run_visit_check, run_visit_leads, run_visit_reason,
)
# --- Планирование визитов (recurrence + mobil visit bridge) ---
from tests.test_document.test_Plan_visit_recurrence import (
    _deactivate_agent, confirm_visit_lead, run_create_agent,
    run_every_2_weeks, run_every_3_weeks, run_every_4_weeks, run_every_5_weeks,
    run_mobile_visit, run_monthly, run_weekly, verify_visit_completed_web,
)
# --- Отслеживание пользователей (E2E: agent → reja → API visit → трекинг) ---
from tests.test_document.test_agent_visit_tracking import (
    N_VISITS, create_weekly_plan_5_points, run_api_visits, verify_tracking,
)


# ══════════════════════════════════════════════════════════════════════════════
# Umumiy zanjir tanalari — test_040/test_050 VA test_all_document ular orqali (DRY)
# ══════════════════════════════════════════════════════════════════════════════
def _recurrence_full(page: Page) -> None:
    """Recurrence to'liq zanjiri: bitta agent → barcha variantlar (chained) →
    monthly → mobil visit (C) → web'da Завершен + lead Подтвержден → agent Неактивный."""
    agent = run_create_agent(page)
    run_weekly(page, agent, chained=True)
    run_every_2_weeks(page, agent, chained=True)
    run_every_3_weeks(page, agent, chained=True)
    run_every_4_weeks(page, agent, chained=True)
    run_every_5_weeks(page, agent, chained=True)
    run_monthly(page, agent)

    summary = run_mobile_visit(page, agent)
    m = BasePage(page)
    visit_id = summary["visit_id"]
    with allure.step(f"Web: Визиты'da visit (#{visit_id}) 'Завершен' + Просмотр"):
        verify_visit_completed_web(page, m, agent, visit_id)
    with allure.step("Web: Лиды — visit lead'ini tasdiqlash (Подтвержден)"):
        confirm_visit_lead(page, m, agent, visit_id)
    with allure.step(f"Tozalash: '{agent}' agentini Неактивный qilish"):
        _deactivate_agent(page, m, agent)


def _agent_tracking(page: Page) -> None:
    """Отслеживание E2E: rol=Агент yangi user → haftalik reja (5 chana) → API orqali
    N_VISITS visit → Отслеживание xaritasida bajarilgan visitlar → agent Неактивный."""
    with allure.step("1-qadam: rol=Агент yangi Пользователь yaratish"):
        agent = run_create_agent(page)
    with allure.step("2-qadam: haftalik reja + 5 chana"):
        user_id = create_weekly_plan_5_points(page, agent)
    with allure.step(f"3-qadam: API orqali {N_VISITS} ta visit"):
        visit_ids = run_api_visits(page, agent, user_id, count=N_VISITS)
        assert len(visit_ids) == N_VISITS, f"{N_VISITS} visit kutilgan, olindi {visit_ids}"
    with allure.step(f"4-qadam: Отслеживание — {len(visit_ids)} visit ko'rinishi"):
        verify_tracking(page, agent, expected_visits=len(visit_ids))
    with allure.step(f"Tozalash: '{agent}' agentini Неактивный qilish"):
        _deactivate_agent(page, BasePage(page), agent)


# ══════════════════════════════════════════════════════════════════════════════
# 0. LOGIN — bir marta, butun seans uchun
# ══════════════════════════════════════════════════════════════════════════════
@allure.epic("Документы")
@allure.feature("Runner — seans")
@allure.title("Login — admin bilan bir marta kirish (butun document runner uchun)")
def test_000_login_admin(session_page: Page) -> None:
    """Butun runner uchun YAGONA login. Keyingi barcha testlar shu ochiq
    session_page seansidan foydalanadi — qayta login qilinmaydi."""
    authorization(session_page)


# ══════════════════════════════════════════════════════════════════════════════
# I. ГРУППА ПОЛЕЙ — to'liq CRUD + negativ
# ══════════════════════════════════════════════════════════════════════════════
@allure.epic("Документы")
@allure.feature("Группа полей")
@allure.title("Группа полей: Создание")
def test_010_field_group_create(session_page: Page, code) -> None:
    run_field_group(session_page, code)


@allure.epic("Документы")
@allure.feature("Группа полей")
@allure.title("Группа полей: Редактирование")
def test_011_field_group_edit(session_page: Page, code) -> None:
    run_field_group_edit(session_page, code)


@allure.epic("Документы")
@allure.feature("Группа полей")
@allure.title("Группа полей: Статус — Неактивный/Активный")
def test_012_field_group_status(session_page: Page, code) -> None:
    run_field_group_status(session_page, code)


@allure.epic("Документы")
@allure.feature("Группа полей")
@allure.title("Группа полей: Подтипы — Поле qo'shish")
def test_013_field_group_subtypes(session_page: Page, code) -> None:
    run_field_group_subtypes(session_page, code)


@allure.epic("Документы")
@allure.feature("Группа полей")
@allure.title("Группа полей: Удаление")
def test_014_field_group_delete(session_page: Page, code) -> None:
    run_field_group_delete(session_page, code)


@allure.epic("Документы")
@allure.feature("Группа полей")
@allure.title("Группа полей: Негатив — majburiy 'Название' bo'sh")
def test_015_field_group_required(session_page: Page, code) -> None:
    run_field_group_required(session_page, code)


@allure.epic("Документы")
@allure.feature("Группа полей")
@allure.title("Группа полей: Дубликат — nom bilan xatolik")
def test_016_field_group_duplicate(session_page: Page, code) -> None:
    run_field_group_duplicate(session_page, code)


# ══════════════════════════════════════════════════════════════════════════════
# II. АНАЛИЗ МАРШРУТОВ — hisobot yuklab olish
# ══════════════════════════════════════════════════════════════════════════════
@allure.epic("Документы")
@allure.feature("Анализ маршрутов")
@allure.title("Анализ маршрутов: .xlsx muvaffaqiyatli yuklanadi")
def test_020_route_download(session_page: Page, tmp_path) -> None:
    run_download_success(session_page, str(tmp_path))


@allure.epic("Документы")
@allure.feature("Анализ маршрутов")
@allure.title("Анализ маршрутов: fayl tuzilishi (sheet, 13 ustun, >=1 qator)")
def test_021_route_structure(session_page: Page, tmp_path) -> None:
    run_structure(session_page, str(tmp_path))


@allure.epic("Документы")
@allure.feature("Анализ маршрутов")
@allure.title("Анализ маршрутов: План qiymatlari faylda aks etadi")
def test_022_route_plan_values(session_page: Page, tmp_path) -> None:
    run_plan_values(session_page, str(tmp_path))


@allure.epic("Документы")
@allure.feature("Анализ маршрутов")
@allure.title("Анализ маршрутов: 'Тип отчёта' = {report_type} yuklab olish")
@pytest.mark.parametrize("report_type", REPORT_TYPES)
def test_023_route_report_type(session_page: Page, tmp_path, report_type: str) -> None:
    run_report_type(session_page, str(tmp_path), report_type)


@allure.epic("Документы")
@allure.feature("Анализ маршрутов")
@allure.title("Анализ маршрутов: Негатив — bo'sh sanalar (required validatsiya bug'i, xfail)")
def test_024_route_required_fields(session_page: Page) -> None:
    # run_required_fields ichida pytest.xfail chaqiriladi (ilova majburiy sanani
    # tekshirmaydi) — bu test XFAIL bo'ladi, yiqilish emas.
    run_required_fields(session_page)


# ══════════════════════════════════════════════════════════════════════════════
# III. ВИЗИТЫ — check (newman) → Причины CRUD → Лиды/Шаги
#     Tartib MUHIM: check avval — visit bajarib lead hosil qiladi, led_shag shunga
#     tayanadi (manba test_visit_all bilan bir xil).
# ══════════════════════════════════════════════════════════════════════════════
@allure.epic("Документы")
@allure.feature("Визиты")
@allure.title("Визиты: visit bajarilgach Просмотр tablari + lead Подтвержден")
def test_030_visit_check(session_page: Page) -> None:
    run_visit_check(session_page)


@allure.epic("Документы")
@allure.feature("Визиты")
@allure.title("Визиты: Причины CRUD — create → edit → view → status → delete")
def test_031_visit_reason(session_page: Page, code: str) -> None:
    run_visit_reason(session_page, code)


@allure.epic("Документы")
@allure.feature("Визиты")
@allure.title("Визиты: Лиды ro'yxati (lead Просмотр tablari)")
def test_032_visit_leads(session_page: Page) -> None:
    run_visit_leads(session_page)


@allure.epic("Документы")
@allure.feature("Визиты")
@allure.title("Визиты: Роли визитов — 2 rol, Критерии+Bизит, Критерии render")
def test_033_visit_roles_overview(session_page: Page) -> None:
    run_visit_roles_overview(session_page)


@allure.epic("Документы")
@allure.feature("Визиты")
@allure.title("Визиты: Функции визита round-trip (3 funksiya saqlash↔o'qish)")
def test_034_visit_role_functions(session_page: Page) -> None:
    run_visit_functions_roundtrip(session_page, 3)


@allure.epic("Документы")
@allure.feature("Визиты")
@allure.title("Визиты: Критерии функций визита CRUD (kriteriy + требование round-trip)")
def test_035_visit_role_criteria(session_page: Page, code: str) -> None:
    run_visit_criteria_roundtrip(session_page, code)


# ══════════════════════════════════════════════════════════════════════════════
# IV. ПЛАНИРОВАНИЕ ВИЗИТОВ — recurrence + Postman mobil visit (o'z agenti bilan)
# ══════════════════════════════════════════════════════════════════════════════
@allure.epic("Документы")
@allure.feature("Планирование визитов")
@allure.title("Recurrence: barcha variantlar + Postman mobil visit (bitta agent)")
def test_040_recurrence_full(session_page: Page) -> None:
    """Manba test_recurrence_all zanjir tanasi (ichki authorization'siz):
    bitta agent → recurrence variantlari (chained) → monthly → mobil visit (C) →
    web'da Завершен tekshiruvi + lead Подтвержден → agentni Неактивный."""
    _recurrence_full(session_page)


# ══════════════════════════════════════════════════════════════════════════════
# V. ОТСЛЕЖИВАНИЕ ПОЛЬЗОВАТЕЛЕЙ — E2E: agent → reja → API visit → трекинг
# ══════════════════════════════════════════════════════════════════════════════
@allure.epic("Документы")
@allure.feature("Отслеживание пользователей")
@allure.title("E2E: agent → 5 chanali reja → API {N} visit → трекинг".format(N=N_VISITS))
def test_050_agent_visit_tracking(session_page: Page) -> None:
    """Manba test_agent_visit_tracking zanjir tanasi (ichki authorization'siz):
    rol=Агент yangi user → haftalik reja (5 chana) → API orqali N_VISITS visit →
    Отслеживание xaritasida bajarilgan visitlar soni → agentni Неактивный."""
    _agent_tracking(session_page)
