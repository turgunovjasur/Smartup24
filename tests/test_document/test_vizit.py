"""Визиты moduli E2E testlari — noldan qayta yozilgan (MCP bilan prod'da o'rganib).

Muhit: PRODUCTION (app.smartup24.com, kompaniya `test`). Barcha selektorlar 2026-08-05
da Playwright MCP orqali jonli DOM'da tasdiqlangan.

Qamrov (run_* biznes logika + test_* login+run juftligi, oxirida test_vizit_all zanjir):

  1. run_vizit_check      — Vizit KELIB TUSHGANDAN keyingi tekshiruv. Avval o'zi
                            vizit bajaradi (yangi Агент + bugungi reja + newman mobil
                            vizit → C), keyin: Визиты'da "Завершен" → Просмотр tablari
                            → vizit ichidan Лиды → lead Просмотр → lead "Подтвержден";
                            oxirida agent Неактивный. newman SHART.
  2. run_vizit_leads      — Лиды sub-bo'limi: 1 lidni Просмотр + tablari (Go back).
  3. run_vizit_prichina   — Причины to'liq CRUD: create → edit → view/verify (read-back)
                            → status Активный↔Неактивный → delete. Unikal nom `code`.
  4. run_visit_roles_overview      — Роли визитов read-only: 2 rol (Агент/Модератор),
                            har ikkisi "Критерии"+"Bизит" tugmalariga ega; Критерии
                            ekrani yoqilgan funksiya bo'yicha render bo'ladi.
  5. run_visit_functions_roundtrip — Функции визита config round-trip (0-userli
                            "Модератор (визит)" rolida, prod xavfsiz): N funksiya
                            (1/2/3) belgila → Сохранить → qayta ochib aynan N tasi
                            belgilanganini assert → asl holatga qaytar. parametrize.
  6. run_visit_form_default        — "Форма визита" default'da YOQILGAN (asosiy
                            funksiya) ekanini tasdiqlaydi.

MCP topilmalari (2026-08-05, prod) — TASK PREMISASIDAN FARQLAR:
  * "Роли визитов" sub-nav'da (Шаги визита OLIB TASHLANGAN): Лиды / Причины / Роли визитов.
  * Rol qatorini bosganда inline panel: "Критерии" + "Bизит" (B — LOTIN harfi!).
    IKKALA rol (Агент/Модератор) ham ikkала tugmaga ega — task'dagi "Moderator faqat
    ko'radi" farqi prod'da YO'Q. Bizit tugmasi izit-regex bilan bosiladi (Lotin B).
  * "Bизит" → "Функции визита": 3 checkbox (Форма визита / Опросник / Фотоотчет),
    Сохранить saqlab biruni dashboard'ga redirect qiladi.
  * "Критерии" → "Критерии функций визита": har YOQILGAN funksiya uchun bitta
    "Добавить критерий" bo'limi.
  * "Форма визита" bu ekranда QULFLANMAGAN — uni yechib all-off saqlash MUMKIN
    (server bloklamaydi). Shu sabab "o'chirib bo'lmaydi" NEGATIVE test YOZILMADI;
    o'rniga run_visit_form_default default-yoqilgan haqiqiy holatni hujjatlashtiradi.
  * Vizit mobil API (newman) orqali bajariladi — "N funksiya vizitda ko'rindi"ni
    web UI'da tekshirib bo'lmaydi, shuning uchun config round-trip (saqlash↔o'qish)
    tekshiriladi. Round-trip 0-userli Модератор rolida (28 userli Агент'ga tegilmaydi).
  * Причина create: "Название *" inputi smtid'siz, id="null" (`#null`); list status
    "active"/"passive" (inglizcha, _STATUS_SYNONYMS qoplaydi); qator paneli
    Изменить + status toggle ("Неактивный"/"Активный").
"""
import re

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

# Функции визита checkboxlari (tartib: N ta uchun birinchi N tasi olinadi —
# "Форма визита" har doim asosiy/birinchi funksiya).
VISIT_FUNCTIONS = ["Форма визита", "Опросник", "Фотоотчет"]

# 0-userli, prod'da xavfsiz o'zgartiriladigan rol (28 userli "Агент (визит)"ga tegmaymiz).
SAFE_ROLE = "Модератор (визит)"
# Rol qatoridagi "Bизит" tugmasi: B — LOTIN harfi (U+0042), matn "изит" bilan tugaydi.
# Lotin/Kiril B chalkashligidan qochish uchun regex bilan bosiladi.
_VISIT_TAB_RE = re.compile(r"изит$")


# ======================================================================================
# Navigatsiya / rol-funksiya helperlari
# ======================================================================================

def _goto_visit_section(page: Page, m: BasePage, link: str) -> None:
    """Визиты → sub-nav bo'limiga (Лиды / Причины / Роли визитов) o'tadi."""
    _goto_visits(page, m)
    m.click_link(link)


def _functions_root(page: Page):
    """"Функции визита" sahifasidagi yagona <article> (rol heading + 3 checkbox)."""
    return page.locator("article").first


def _open_role_functions(page: Page, m: BasePage, role: str = SAFE_ROLE):
    """Роли визитов → rol qatori → "Bизит" → "Функции визита" ekranini ochadi.

    Har chaqiruvда serverdan YANGI o'qiladi (save'dan keyin dashboard'ga redirect
    bo'lgani uchun UI orqali qayta ochamiz — qattiq kodlangan role_id ishlatmasdan)."""
    _goto_visit_section(page, m, "Роли визитов")
    m.expect_heading("Роли визитов")
    m.click_grid_row(role)
    # "Bизит" (Lotin B) — regex bilan; panel'да faqat shu tugma "изит" bilan tugaydi.
    m._close_overlay()
    page.get_by_role("button", name=_VISIT_TAB_RE).first.click()
    m._settle()
    m.expect_heading("Функции визита")
    return _functions_root(page)


def _set_functions(m: BasePage, root, wanted: set) -> None:
    """Har bir funksiyani wanted'ga qarab yoqadi/o'chiradi (idempotent)."""
    for func in VISIT_FUNCTIONS:
        m.checkbox(label=func, checked=func in wanted, root=root)


def _assert_functions(m: BasePage, root, wanted: set) -> None:
    """Har bir funksiya holati wanted'ga mos ekanini tasdiqlaydi."""
    for func in VISIT_FUNCTIONS:
        m.checkbox(label=func, expect_checked=func in wanted, root=root)


def _save_functions(page: Page, m: BasePage) -> None:
    """"Функции визита"ni saqlaydi va saqlanganini (ekrandan chiqib ketish bilan)
    tasdiqlaydi — muvaffaqiyatли save biruni dashboard'ga redirect qiladi."""
    m.click_button("Сохранить")
    page.wait_for_url(lambda u: "role_functions" not in u, timeout=30_000)
    m._settle()


def _open_visit_row(page: Page, m: BasePage, agent: str, visit_id: str) -> None:
    """Визиты ro'yxatida agent vizitini tanlaydi (action panel chiqadi).

    Qatorda client/agent kataklari BUTTON (bosilsa boshqa sahifaga ketadi) — ID
    katagi (oddiy matn) exact bosiladi (agent code'iga tushmasin)."""
    m.search(agent)
    m.grid_row(agent, "Завершен").get_by_text(visit_id, exact=True).click()
    m._settle()


# ======================================================================================
# run_* — biznes logika (login qilinganini kutadi)
# ======================================================================================

def run_vizit_check(page: Page) -> None:
    """Vizit kelib tushgach ishlaydigan tekshiruvlar — avval o'zi vizit bajaradi
    (yangi agent + bugungi reja + newman), keyin Визиты/Лиды'da tekshiradi."""
    m = BasePage(page)

    with allure.step("Tayyorlov: yangi Агент + bugungi reja + mobil vizit (newman → C)"):
        agent = run_create_agent(page)
        run_monthly(page, agent)
        summary = run_mobile_visit(page, agent)
        visit_id = summary["visit_id"]

    with allure.step(f"Визиты: vizit #{visit_id} 'Завершен' + Просмотр tablari"):
        _goto_visits(page, m)
        _open_visit_row(page, m, agent, visit_id)
        m.click_button("Просмотр")
        m.expect_heading("Визит (Просмотр)")
        m.click_button("Дополнительная информация")
        m.click_button("Результаты анализа")
        m.click_button("Go back")

    with allure.step("Лиды (vizit ichidan): lead Просмотр (Дополнительные поля / История)"):
        _open_visit_row(page, m, agent, visit_id)
        m.click_button("Лиды")
        m.expect_heading("Лиды")
        m.click_grid_row(agent)
        m.click_button("Просмотр")
        m.expect_heading("Просмотр лида")
        m.click_button("Дополнительные поля")
        m.click_button("История")
        m.click_button("Go back")

    with allure.step("Lead: Новый → Подтвержден"):
        m.click_grid_row(agent)
        m.click_button("Подтвержден")
        m.confirm("да")
        m.grid_row(agent, "Подтвержден")

    with allure.step(f"Tozalash: '{agent}' agentini Неактивный qilish"):
        _deactivate_agent(page, m, agent)


def run_vizit_leads(page: Page) -> None:
    """Лиды sub-bo'limi: mavjud lead'ni Просмотр qilib tablarини ochadi.

    Link orqali ochilgan Лиды — YUQORI sahifa (vizit ichidan emas), "Go back" bitta.
    Avvalgi run'lardan 'agent-' prefiksli lead'lar bor — birinchisini olamiz."""
    m = BasePage(page)

    with allure.step("Навигация: Визиты → Лиды"):
        _goto_visit_section(page, m, "Лиды")
        m.expect_heading("Лиды")

    with allure.step("Lead Просмотр: Дополнительные поля / История"):
        m.click_grid_row("agent-")
        m.click_button("Просмотр")
        m.expect_heading("Просмотр лида")
        m.click_button("Дополнительные поля")
        m.click_button("История")
        m.click_button("Go back")
        m.expect_heading("Лиды")


def run_vizit_prichina(page: Page, code: str) -> None:
    """Визиты → Причины to'liq CRUD (unikal nom `code`).

    create → edit → view/verify (Изменить orqali qiymatni read-back qilib tasdiqlash;
    alohida "Просмотр" tugmasi YO'Q) → status Активный↔Неактивный → delete."""
    m = BasePage(page)
    name = f"prichina-{code}"
    edited = f"{name}-edit"

    with allure.step("Навигация: Визиты → Причины"):
        _goto_visit_section(page, m, "Причины")
        m.expect_heading("Причины")

    with allure.step(f"Создать: {name}"):
        m.open_create()
        m.expect_heading("Причина (Создание)")
        # "Название *" inputi smtid'siz/label'siz — id="null" (MCP real DOM'дан)
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

    with allure.step(f"Просмотр/tekshirish: qiymat '{edited}' saqlanganini read-back"):
        m.search(edited)
        m.click_grid_row(edited)
        m.click_button("Изменить")
        m.expect_heading("Причина (Редактирование)")
        expect(page.locator("#null")).to_have_value(edited)
        m.click_button("Go back")
        m.expect_heading("Причины")

    with allure.step("Status: Активный → Неактивный (show_all) → Активный"):
        m.search(edited)
        m.click_grid_row(edited)
        m.click_button("Неактивный")
        m.confirm("да")
        m.show_all()  # passiv qator default yashirin
        m.grid_row(edited, "Неактивный")
        m.click_grid_row(edited)
        m.click_button("Активный")
        m.confirm("да")
        m.grid_row(edited, "Активный")

    with allure.step("Удалить + ro'yxatда yo'qligini tekshirish"):
        m.click_grid_row(edited)
        m.click_button("Удалить")
        m.confirm("да")
        expect(page.get_by_text("Нет результатов")).to_be_visible()


def run_visit_roles_overview(page: Page) -> None:
    """Роли визитов read-only: 2 rol bor va Активный; har ikki rol "Критерии"+"Bизит"
    tugmalariga ega; "Критерии" ekrani yoqilgan funksiya(lar) bo'yicha render bo'ladi.

    (Task'dagi "Agent/Moderator UI farqi" prod'da YO'Q — ikkаласi bir xil; shu
    haqiqiy holat tekshiriladi.)"""
    m = BasePage(page)

    with allure.step("Навигация: Визиты → Роли визитов"):
        _goto_visit_section(page, m, "Роли визитов")
        m.expect_heading("Роли визитов")

    with allure.step("Har ikki rol mavjud va Активный"):
        m.grid_row("Агент (визит)", "Активный")
        m.grid_row(SAFE_ROLE, "Активный")

    with allure.step(f"'{SAFE_ROLE}' → panel'да 'Критерии' + 'Bизит' tugmalari"):
        m.click_grid_row(SAFE_ROLE)
        expect(page.get_by_role("button", name="Критерии").first).to_be_visible()
        expect(page.get_by_role("button", name=_VISIT_TAB_RE).first).to_be_visible()

    with allure.step("'Критерии' → yoqilgan funksiya bo'yicha render (Форма визита)"):
        m.click_button("Критерии")
        m.expect_heading("Критерии функций визита")
        # Модератор'да faqat "Форма визита" yoqilgan → shu nomли bo'lim bo'lishi shart
        expect(page.get_by_role("heading", name="Форма визита").first).to_be_visible()
        m.click_button("Go back")
        m.expect_heading("Роли визитов")


def run_visit_functions_roundtrip(page: Page, count: int) -> None:
    """Функции визита config round-trip (xavfsiz SAFE_ROLE rolida).

    `count` (1/2/3) ta funksiya belgilanadi ("Форма визита" har doim ichida) →
    Сохранить → qayta ochib aynan o'sha funksiyalar belgilanganini assert → asl
    holatga (faqat "Форма визита") qaytariladi.

    Vizit API orqali bajarilgani uchun "vizitда N funksiya ko'rindi"ni web'да
    tekshirib bo'lmaydi — bu yerda SAQLASH↔O'QISH mutanosibligi tekshiriladi."""
    m = BasePage(page)
    wanted = set(VISIT_FUNCTIONS[:count])

    try:
        with allure.step(f"'{SAFE_ROLE}': {count} funksiya belgilash {sorted(wanted)}"):
            root = _open_role_functions(page, m)
            _set_functions(m, root, wanted)
            _save_functions(page, m)

        with allure.step(f"Qayta ochib aynan {count} funksiya belgilanganini tekshirish"):
            root = _open_role_functions(page, m)
            _assert_functions(m, root, wanted)
            allure.attach(f"{SAFE_ROLE}: {sorted(wanted)}", name="saved_functions",
                          attachment_type=allure.attachment_type.TEXT)
    finally:
        with allure.step("Asl holatga qaytarish: faqat 'Форма визита'"):
            root = _open_role_functions(page, m)
            _set_functions(m, root, {"Форма визита"})
            _save_functions(page, m)


def run_visit_form_default(page: Page) -> None:
    """"Форма визита" — asosiy funksiya, default'da YOQILGAN bo'lishini tasdiqlaydi.

    DIQQAT: bu ekranда "Форма визита"ni yechib all-off saqlash TEXNIK jihatdan
    mumkin (server bloklamaydi — MCP prod 2026-08-05); shuning uchun "o'chirib
    bo'lmaydi" degan negative test o'rniga default-yoqilgan HAQIQIY holat
    hujjatlashtiriladi."""
    m = BasePage(page)
    with allure.step(f"'{SAFE_ROLE}' → Функции визита: 'Форма визита' default yoqilgan"):
        root = _open_role_functions(page, m)
        m.checkbox(label="Форма визита", expect_checked=True, root=root)


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
@allure.story("Лиды")
@allure.title("Лиды: lead Просмотр (Дополнительные поля / История)")
def test_vizit_leads(page: Page) -> None:
    authorization(page)
    run_vizit_leads(page)


@allure.epic("Документы")
@allure.feature("Визиты")
@allure.story("Причины")
@allure.title("Причины CRUD: create → edit → view → status → delete")
def test_vizit_prichina(page: Page, code: str) -> None:
    authorization(page)
    run_vizit_prichina(page, code)


@allure.epic("Документы")
@allure.feature("Визиты")
@allure.story("Роли визитов")
@allure.title("Роли визитов: 2 rol, Критерии+Bизит tugmalari, Критерии render")
def test_visit_roles_overview(page: Page) -> None:
    authorization(page)
    run_visit_roles_overview(page)


@allure.epic("Документы")
@allure.feature("Визиты")
@allure.story("Роли визитов / Функции визита")
@allure.title("Функции визита round-trip: {count} funksiya saqlash↔o'qish")
@pytest.mark.parametrize("count", [1, 2, 3])
def test_visit_role_functions_count(page: Page, count: int) -> None:
    authorization(page)
    run_visit_functions_roundtrip(page, count)


@allure.epic("Документы")
@allure.feature("Визиты")
@allure.story("Роли визитов / Функции визита")
@allure.title("Форма визита — asosiy funksiya default'да yoqilgan (regression)")
def test_visit_form_default(page: Page) -> None:
    authorization(page)
    run_visit_form_default(page)


@pytest.mark.skipif(NEWMAN_YOQ, reason="newman (Postman CLI) o'rnatilmagan — `npm i -g newman`")
@allure.epic("Документы")
@allure.feature("Визиты")
@allure.story("Визит tekshiruvi")
@allure.title("Zanjir: vizit check + Лиды + Причины + Роли/Функции — bitta login bilan")
def test_vizit_all(page: Page, code: str) -> None:
    """Barcha vizit tekshiruvlari BITTA login bilan (tartib muhim: check BIRINCHI —
    vizitdan yangi lead paydo bo'lib, run_vizit_leads'ga lead kafolatlanadi)."""
    authorization(page)
    run_vizit_check(page)
    run_vizit_leads(page)
    run_vizit_prichina(page, code)
    run_visit_roles_overview(page)
    run_visit_functions_roundtrip(page, 3)
