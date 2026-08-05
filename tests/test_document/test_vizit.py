"""Визиты moduli tekshiruvlari (BasePage uslubida, codegen'дан qayta yozilgan).

CRUD konvensiyasi: har tekshiruv run_* (biznes logika, login kutadi) + test_*
(authorization + run_*) juftligi, OXIRIDA test_vizit_all — hammasi BITTA login
bilan zanjir (tartib muhim: check birinchi — vizitdan yangi lead paydo bo'lib,
led_shag'ga lead kafolatlanadi).

3 tekshiruv:
  test_vizit_check     — AVVAL vizit bajariladi (yangi agent + bugungi reja +
                         Postman/newman mobil vizit → C), KEYIN tekshiriladi:
                         Визиты'da "Завершен" → Просмотр (Дополнительная
                         информация / Результаты анализа) → Лиды → lead Просмотр
                         (Дополнительные поля / История) → lead "Подтвержден".
                         Oxirida agent Неактивный (tozalash). newman SHART.
  test_vizit_prichinya — Визиты → Причины to'liq CRUD: create → edit → Неактивный
                         (show_all bilan) → Активный → delete. Unikal nom (code).
  test_vizit_led_shag  — Визиты → Лиды ro'yxati (lead Просмотр + tablar) va
                         Шаги визита ro'yxati (qidiruv "лид").

Codegen'дагi qotirilgan qiymatlar OLIB TASHLANDI: eski agent nomlari
(agent-2206317...) o'rniga har run yangi agent; `#cdk-drop-list-N` va
`.cdk-drag > div:nth-child(4)` (dinamik/mo'rt selektorlar) o'rniga BasePage
grid_row + visit_id katagi. Причина formasida Название inputi smtid'siz
(id="null" — codegen'da real DOM'dan tasdiqlangan) — raw locator saqlanadi.
"""
import allure
import pytest
from playwright.sync_api import Page, expect

from flows.flow_authorization import authorization
from utils.base_page import BasePage
from tests.test_document.test_Plan_visit_recurrence import (
    NEWMAN_YOQ,
    _deactivate_agent,
    _goto_visits,
    run_create_agent,
    run_mobile_visit,
    run_monthly,
)


def _open_visit_row(page: Page, m: BasePage, agent: str, visit_id: str) -> None:
    """Визиты ro'yxatida agent vizitining qatorini tanlaydi (action panel chiqadi).

    Qatorda client/agent kataklari BUTTON (bosilsa boshqa sahifaga ketadi) —
    ID katagi (oddiy matn) bosiladi (exact: agent code'iga tushmasin)."""
    m.search(agent)
    m.grid_row(agent, "Завершен").get_by_text(visit_id, exact=True).click()
    m._settle()


# ======================================================================================
# run_* — biznes logika (login qilinganini kutadi); test_vizit_all zanjiri ham chaqiradi
# ======================================================================================

def run_vizit_check(page: Page) -> None:
    """Vizit KELIB TUSHGANDAN KEYIN ishlaydigan tekshiruvlar — shuning uchun avval
    o'zi vizit bajaradi (yangi agent + bugungi reja + newman)."""
    m = BasePage(page)

    # --- 1. Vizitni bajarish (busiz quyidagi tekshiruvlar ishlamaydi) ---
    with allure.step("Tayyorlov: yangi Агент + bugungi reja"):
        agent = run_create_agent(page)
        run_monthly(page, agent)  # bugungi kunga reja (tekshiruv bilan)

    summary = run_mobile_visit(page, agent)  # Postman/newman: begin→end→status C
    visit_id = summary["visit_id"]

    # --- 2. Визиты: vizit "Завершен" + Просмотр tablari ---
    with allure.step(f"Визиты: vizit (#{visit_id}) 'Завершен' + Просмотр tablari"):
        _goto_visits(page, m)
        _open_visit_row(page, m, agent, visit_id)
        m.click_button("Просмотр")
        m.expect_heading("Визит (Просмотр)")
        m.click_button("Дополнительная информация")
        m.click_button("Результаты анализа")
        m.click_button("Go back")

    # --- 3. Лиды: lead Просмотр (tablar) ---
    with allure.step("Лиды: lead Просмотр (Дополнительные поля / История)"):
        _open_visit_row(page, m, agent, visit_id)
        m.click_button("Лиды")
        m.expect_heading("Лиды")
        # Lead qatorida Пользователь=agent (plain matn) — click_grid_row xavfsiz
        m.click_grid_row(agent)
        m.click_button("Просмотр")
        m.expect_heading("Просмотр лида")
        m.click_button("Дополнительные поля")
        m.click_button("История")
        m.click_button("Go back")

    # --- 4. Lead'ni tasdiqlash ---
    with allure.step("Lead: Новый → Подтвержден"):
        m.click_grid_row(agent)
        m.click_button("Подтвержден")
        m.confirm("да")
        m.grid_row(agent, "Подтвержден")

    # --- 5. Tozalash ---
    with allure.step(f"Tozalash: '{agent}' agentini Неактивный qilish"):
        _deactivate_agent(page, m, agent)


def run_vizit_prichinya(page: Page, code: str) -> None:
    """Визиты → Причины to'liq CRUD (unikal nom `code` bilan)."""
    m = BasePage(page)
    name = f"prichina-{code}"
    edited = f"{name}-edit"

    with allure.step("Навигация: Визиты → Причины"):
        _goto_visits(page, m)
        m.click_link("Причины")
        m.expect_heading("Причины")

    with allure.step(f"Создать: {name}"):
        m.open_create()
        m.expect_heading("Причина (Создание)")
        # Название inputi smtid'siz, id="null" (codegen real DOM'dan) — raw locator
        page.locator("#null").fill(name)
        m.save()
        m.expect_heading("Причины")

    with allure.step(f"Изменить: {name} → {edited}"):
        m.search(name)
        m.click_grid_row(name)
        m.click_button("Изменить")
        m.expect_heading("Причина (Редактирование)")
        page.locator("#null").fill(edited)
        m.save()
        m.expect_heading("Причины")

    with allure.step("Status: Активный → Неактивный (show_all) → Активный"):
        m.search(edited)
        m.click_grid_row(edited)
        m.click_button("Неактивный")
        m.confirm("да")
        m.show_all()  # passiv qator default yashirin — filtr "Показать все"
        m.grid_row(edited, "Неактивный")
        m.click_grid_row(edited)
        m.click_button("Активный")
        m.confirm("да")
        m.grid_row(edited, "Активный")

    with allure.step("Удалить + ro'yxatda yo'qligini tekshirish"):
        m.click_grid_row(edited)
        m.click_button("Удалить")
        m.confirm("да")
        expect(page.get_by_text("Нет результатов")).to_be_visible()


def run_vizit_led_shag(page: Page) -> None:
    """Визиты → Лиды (lead Просмотр tablari) va Шаги визита ro'yxati."""
    m = BasePage(page)

    with allure.step("Навигация: Визиты → Лиды"):
        _goto_visits(page, m)
        m.click_link("Лиды")
        m.expect_heading("Лиды")

    with allure.step("Lead Просмотр: Дополнительные поля / История"):
        # Avvalgi test run'laridan lead'lar bor (agent- prefiksli) — birinchisini olamiz
        m.click_grid_row("agent-")
        m.click_button("Просмотр")
        m.expect_heading("Просмотр лида")
        m.click_button("Дополнительные поля")
        m.click_button("История")
        m.click_button("Go back")
        m.expect_heading("Лиды")

    with allure.step("Шаги визита: ro'yxat + qidiruv"):
        # Link orqali ochilgan Лиды — yuqori darajali sahifa, "Go back" YO'Q;
        # sub-nav linklari esa faqat Визиты sahifasida — flow_navigate bilan qaytamiz
        _goto_visits(page, m)
        m.click_link("Шаги визита")
        m.expect_heading("Шаги визита")
        m.search("лид")
        m.grid_row("Лид")


# ======================================================================================
# test_* — har biri alohida (o'z login'i bilan), oxirida zanjir
# ======================================================================================

@pytest.mark.skipif(NEWMAN_YOQ, reason="newman (Postman CLI) o'rnatilmagan — `npm i -g newman`")
@allure.epic("Документы")
@allure.feature("Визиты")
@allure.story("Визит tekshiruvi")
@allure.title("Vizit bajarilgach: Просмотр tablari + lead Просмотр + Подтвержден")
def test_vizit_check(page: Page) -> None:
    authorization(page)
    run_vizit_check(page)


@allure.epic("Документы")
@allure.feature("Визиты")
@allure.story("Причины")
@allure.title("Причины CRUD: create → edit → status → delete")
def test_vizit_prichinya(page: Page, code: str) -> None:
    authorization(page)
    run_vizit_prichinya(page, code)


@allure.epic("Документы")
@allure.feature("Визиты")
@allure.story("Лиды / Шаги визита")
@allure.title("Лиды ro'yxati (lead Просмотр) va Шаги визита ro'yxati")
def test_vizit_led_shag(page: Page) -> None:
    authorization(page)
    run_vizit_led_shag(page)


@pytest.mark.skipif(NEWMAN_YOQ, reason="newman (Postman CLI) o'rnatilmagan — `npm i -g newman`")
@allure.epic("Документы")
@allure.feature("Визиты")
@allure.story("Визит tekshiruvi")
@allure.title("Zanjir: vizit check + Причины CRUD + Лиды/Шаги — bitta login bilan")
def test_vizit_all(page: Page, code: str) -> None:
    """Barcha vizit tekshiruvlari BITTA login bilan (test_all uslubi).

    Tartib muhim: avval run_vizit_check — vizit bajarilib yangi lead paydo
    bo'ladi, shunda run_vizit_led_shag'ga lead kafolatlangan."""
    authorization(page)
    run_vizit_check(page)
    run_vizit_prichinya(page, code)
    run_vizit_led_shag(page)
