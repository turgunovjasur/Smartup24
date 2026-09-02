"""Планирование визитов — recurrence variantlari + Web↔Mobile Visit API (bitta fayl).

Avval ikki fayl edi (test_visit_bridge.py + test_visit_recurrence.py) — ikkalasi ham
visitni tekshirgani uchun 2026-07-29 da BITTA faylga birlashtirildi. Ichida:
  - EMBEDDED Postman kolleksiyasi (newman bilan yuritiladi) + API helperlari
  - WEB helperlari: agent yaratish, Визиты/Лиды tekshiruvлари, agent tozalash
  - recurrence CRUD: har variant ALOHIDA run_/test_ juftligi
      run_weekly / run_every_2_weeks / ... / run_every_5_weeks / run_monthly
  - OXIRIDA test_recurrence_all — bitta login + bitta agent bilan HAMMASI:
      6 recurrence varianti + Postman mobil visit (begin→autosave→end→C) +
      web'da "Завершен"+Просмотр + lead "Подтвержден" + agent Неактивный.

Server rejalarni "Дата начала"dan ~1 OY (31 kun) oynada yaratadi (MCP 2026-07-28
dev/sm24). Hafta bo'limlari start haftasidan N-1, 2N-1, ... haftalarda tanlangan
kunga tushadi.

ALOHIDA testlar (har biri O'Z TOZA agenti bilan, BUGUNGI hafta kuni tanlanadi) —
kutilgan visitlar soni:
  Каждую неделю     → 5 ta (bugun, +7, +14, +21, +28 — KALIT talab)
  Каждую вторую     → 2 ta (+7, +21)
  Каждую третью     → 1 ta (+14)
  Каждую четвертую  → 1 ta (+21)
  Каждую пятую      → 1 ta (+28)
  Раз в месяц       → bugun (+ ehtimol keyingi oy shu kuni — chegara noaniq)
Agent toza bo'lgani uchun ro'yxatdagi BUTUN sanalar kutilganlarga teng tekshiriladi.

ZANJIRDA esa bitta agent — guruhlar aralashmasligi uchun har variant O'Z hafta
kunini oladi (N=1→bugun, N=2→bugun+1, ...): 5/2/1/1/0 (5-hafta sanasi +32 —
oynadan tashqarida qoladi).

API tomonda: base_url=/x24/b; session=agent JSESSIONID cookie
(HttpOnly); visit_user_id=Планы URL'idan; visit_person_id=exp_client_list avtomatik
(person_id STRING → "to be a number" testi soxta fail, KNOWN_QUIRKS'da e'tiborsiz).
Mobil visit faqat BUGUNGI rejaga ishlaydi (weekly/monthly beradi; har 2/3/4/5
hafta birinchi visiti kelajakda — exp_client_list ko'rmaydi).
Talab (faqat newman'li testlarga): `npm i -g newman`.
"""
import copy
import json
import os
import random
import re
import shutil
import subprocess
import time
from datetime import date, timedelta

import allure
import pytest
from playwright.sync_api import Page, expect

from flows.flow_authorization import authorization, COMPANY_CODE, LOGIN_URL
from flows.flow_navbar import flow_navigate
from utils.base_page import BasePage

# Agent login (cookie_from_context) va API backend (BASE_URL) muhitga qarab
# flow_authorization.LOGIN_URL dan olinadi — ilgari IKKALASI ham DEV'ga qattiq
# kodlangan edi, prod'da agent PROD'da yaratilib login DEV'ga borib timeout berardi
#. BASE_URL = login URL'idagi "/a2/auth/login" → "/b"
# (prod: app.smartup24.com/b ; dev: app2.greenwhite.uz/x24/b — /x24 prefiks saqlanadi).
BASE_URL = LOGIN_URL.replace("/a2/auth/login", "/b")
# Cookie domain filtri ham ENV'ga bog'liq (prod: smartup24.com, dev: greenwhite.uz) —
# LOGIN_URL host'idan registrable domain (oxirgi 2 label) olinadi. Ilgari
# "greenwhite.uz" qattiq kodlangan edi → prod cookie'lari (smartup24.com) filtrlanib
# chiqib ketib, cookie BO'SH qolar edi.
COOKIE_DOMAIN = ".".join(LOGIN_URL.split("//", 1)[1].split("/", 1)[0].split(".")[-2:])
MENU = "Планирование визитов"
# Jonli cookie'li — test-results/ (gitignored) ga yoziladi, repo'ga tushmaydi
REPORT = os.path.join("test-results", "newman_visit.json")
FILLED_COLLECTION = os.path.join("test-results", "visit_collection_filled.json")

NEWMAN_YOQ = shutil.which("newman") is None and shutil.which("newman.cmd") is None

# Kolleksiyaning o'zidagi ma'lum nuqson: exp_client_list testi person_id RAQAM
# bo'lishini kutadi, server STRING ("7193") qaytaradi — oqimga ta'siri yo'q.
KNOWN_QUIRKS = {"captured a person_id for the scenario folder"}

# --- pre-request: har so'rovga session Cookie header'ini biriktiradi ---
_PREREQUEST = [
    "const headerName = pm.collectionVariables.get('session_header_name');",
    "const headerValue = pm.collectionVariables.get('session_header_value');",
    "if (headerName && headerValue) { pm.request.headers.upsert({ key: headerName, value: headerValue }); }",
    "pm.request.headers.upsert({ key: 'Content-Type', value: 'application/json' });",
]


def _req(name, body, test_exec):
    """Postman request item yasaydi (POST + raw JSON body + test skript)."""
    is_export = '"code": "c:exp' in body or '"code":"c:exp' in body
    route = "export" if is_export else "import"
    return {
        "name": name,
        "request": {
            "method": "POST",
            "header": [],
            "body": {"mode": "raw", "raw": body, "options": {"raw": {"language": "json"}}},
            "url": f"{{{{base_url}}}}/sb/external:{route}",
        },
        "event": [{"listen": "test", "script": {"type": "text/javascript", "exec": test_exec}}],
    }


# --- EMBEDDED kolleksiya (faqat kerakli so'rovlar; asl body/testlari) ---
COLLECTION = {
    "info": {
        "name": "Smartup24 — Mobile Visit API (Sbe_Moderator)",
        "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
    },
    "variable": [
        {"key": "base_url", "value": "https://REPLACE_WITH_YOUR_TEST_HOST"},
        {"key": "session_header_name", "value": "Cookie"},
        {"key": "session_header_value", "value": "REPLACE_WITH_REAL_SESSION_VALUE"},
        {"key": "visit_person_id", "value": ""},
        {"key": "visit_user_id", "value": ""},
        {"key": "visit_id", "value": ""},
        # Reference maydonlar — exp_client_list javobidan olinadi (default: bo'sh/null)
        {"key": "legal_form_id", "value": "null"},
        {"key": "step_ids", "value": "[]"},
    ],
    "event": [{"listen": "prerequest", "script": {"type": "text/javascript", "exec": _PREREQUEST}}],
    "item": [
        {
            "name": "2. Client Search & Info (EXPORT)",
            "item": [
                _req(
                    "Client list (today's plan/search) — c:exp_client_list",
                    '[\n  {\n    "code": "c:exp_client_list",\n    "filter": {\n      "search_value": "",\n      "region_ids": [],\n      "lob_group_ids": [],\n      "sort_by": "A",\n      "row_start": 1,\n      "rows_count": 50\n    }\n  }\n]',
                    [
                        "pm.test('HTTP 200', () => pm.response.to.have.status(200));",
                        "const body = pm.response.json();",
                        "pm.test('tape ok', () => body.forEach(r => pm.expect(r.status, r.error_text).to.eql('S')));",
                        "const d = body[0] && body[0].data;",
                        "const clients = d && d.clients;",
                        "if (clients && clients.length) {",
                        "    const c = clients[0];",
                        "    pm.collectionVariables.set('visit_person_id', c.person_id);",
                        "    pm.collectionVariables.set('legal_form_id', (c.legal_form && c.legal_form.form_id) ? c.legal_form.form_id : 'null');",
                        "    pm.collectionVariables.set('step_ids', '[]');  // prod visit_steps step_id'lari sbmv_steps FK'ida yo'q (ORA-20999) — step MAJBURIY emas, bo'sh yuboramiz",
                        "    pm.test('captured a person_id for the scenario folder', () => pm.expect(c.person_id).to.be.a('number'));",
                        "}",
                    ],
                ),
                _req(
                    "Client info — c:exp_client_info",
                    '[\n  {\n    "code": "c:exp_client_info",\n    "filter": {\n      "person_id": {{visit_person_id}},\n      "user_id": {{visit_user_id}}\n    }\n  }\n]',
                    [
                        "pm.test('HTTP 200', () => pm.response.to.have.status(200));",
                        "pm.test('tape ok', () => { const b = pm.response.json(); b.forEach(r => pm.expect(r.status, r.error_text).to.eql('S')); });",
                    ],
                ),
            ],
        },
        {
            "name": "5. Scenario: full visit flow (chained auto-test)",
            "item": [
                _req(
                    "Step 1 — begin visit",
                    '{\n  "code": "c:imp_visit_begin",\n  "data": {\n    "person_id": {{visit_person_id}},\n    "user_id": {{visit_user_id}},\n    "begin_latlng": "41.311081,69.240562"\n  }\n}',
                    [
                        "pm.test('HTTP 200', () => pm.response.to.have.status(200));",
                        "const body = pm.response.json();",
                        "pm.test('visit began', () => pm.expect(body.status, body.error_text).to.eql('S'));",
                        "if (body.status === 'S') { pm.collectionVariables.set('visit_id', body.data.visit_id); }",
                    ],
                ),
                _req(
                    "Step 2 — autosave draft mid-visit",
                    '{"code":"c:imp_temporary_visit_save","data":{"person_id":{{visit_person_id}},'
                    '"user_id":{{visit_user_id}},"visit_id":{{visit_id}},"data":{"leads":{'
                    '"legal_form_id":{{legal_form_id}},"name":"Avtotest Dokon","short_name":"AvtoDkn",'
                    '"latlng":"41.311081,69.240562","phone_number":"+998901112233",'
                    '"address":"Toshkent sh., Shayxontohur t.","area":"50","regions":[],'
                    '"lob_product_groups":[],"category_product_groups":[]},"fields":[],"photos":[],'
                    '"visit_audios":[],"quiz_results":[]}}}',
                    [
                        "pm.test('HTTP 200', () => pm.response.to.have.status(200));",
                        "const body = pm.response.json();",
                        "pm.test('draft saved', () => pm.expect(body.status, body.error_text).to.eql('S'));",
                        "pm.test('same visit_id echoed back', () => pm.expect(String(body.data.visit_id)).to.eql(pm.collectionVariables.get('visit_id')));",
                    ],
                ),
                _req(
                    "Step 3 — end visit (completed, no reason)",
                    '{"code":"c:imp_visit_end","data":{"person_id":{{visit_person_id}},'
                    '"visit_id":{{visit_id}},"end_latlng":"41.312500,69.241800","data":{'
                    '"reason_id":null,"leads":{"legal_form_id":{{legal_form_id}},'
                    '"name":"Avtotest Dokon","short_name":"AvtoDkn","latlng":"41.312500,69.241800",'
                    '"phone_number":"+998901112233","address":"Toshkent sh., Shayxontohur t.",'
                    '"area":"50","regions":[],"lob_product_groups":[],"category_product_groups":[]},'
                    '"fields":[],"photos":[],"visit_photos":[],"visit_audios":[],'
                    '"step_ids":{{step_ids}},"quiz_results":[]}}}',
                    [
                        "pm.test('HTTP 200', () => pm.response.to.have.status(200));",
                        "const body = pm.response.json();",
                        "pm.test('visit ended', () => pm.expect(body.status, body.error_text).to.eql('S'));",
                    ],
                ),
                _req(
                    "Step 4 — verify visit_status = C",
                    '[\n  {\n    "code": "c:exp_client_info",\n    "filter": {\n      "person_id": {{visit_person_id}},\n      "user_id": {{visit_user_id}}\n    }\n  }\n]',
                    [
                        "pm.test('HTTP 200', () => pm.response.to.have.status(200));",
                        "const body = pm.response.json();",
                        "pm.test('tape ok', () => body.forEach(r => pm.expect(r.status, r.error_text).to.eql('S')));",
                        "pm.test('visit is completed (status C)', () => {",
                        "    const data = body[0].data;",
                        "    pm.expect(String(data.visit_id)).to.eql(pm.collectionVariables.get('visit_id'));",
                        "    pm.expect(data.visit_status).to.eql('C');",
                        "});",
                    ],
                ),
            ],
        },
    ],
}


# ======================================================================================
# API helperlari — agent cookie, kolleksiyani to'ldirish, newman, natija
# ======================================================================================

def cookie_from_context(ctx, agent_login: str, password: str) -> str:
    """Berilgan Playwright context'ida AGENT sifatida login qilib greenwhite.uz
    cookie'larini "k=v; ..." ko'rinishida qaytaradi (JSESSIONID — HttpOnly bo'lsa
    ham). Context tashqaridan beriladi — pytest'ning `page` fixture'i (ishlab
    turgan sync Playwright) ichida ham chaqirsa bo'ladi (nested sync_playwright YO'Q)."""
    p = ctx.new_page()
    # Default goto timeout 30s — dev-server sekin javob berganda login sahifasi
    # yuklanmay 040 broken bo'lardi; loyiha navigatsiya timeout'i (60s) beriladi.
    p.goto(LOGIN_URL, timeout=60_000)
    p.get_by_role("textbox", name="Логин").fill(agent_login)
    p.get_by_role("textbox", name="Введите пароль").fill(password)
    p.get_by_role("button", name="Войти").click()
    p.wait_for_url(lambda u: "/auth/login" not in u, timeout=60_000)
    p.wait_for_timeout(1_500)
    cookies = ctx.cookies()
    p.close()
    return "; ".join(f"{c['name']}={c['value']}" for c in cookies if COOKIE_DOMAIN in c["domain"])


def fill_collection(cookie: str, user_id: str) -> str:
    """EMBEDDED kolleksiyani haqiqiy qiymatlar bilan to'ldirib vaqtinchalik JSON'ga
    yozadi va yo'lini qaytaradi. Cookie kolleksiya `variable` blokiga yoziladi
    (pre-request skript `pm.collectionVariables.get` o'qiydi — environment EMAS)."""
    col = copy.deepcopy(COLLECTION)
    overrides = {
        "base_url": BASE_URL,
        "session_header_name": "Cookie",
        "session_header_value": cookie,
        "visit_user_id": str(user_id),
    }
    for v in col["variable"]:
        if v["key"] in overrides:
            v["value"] = overrides[v["key"]]
    os.makedirs("test-results", exist_ok=True)
    with open(FILLED_COLLECTION, "w", encoding="utf-8") as f:
        json.dump(col, f, ensure_ascii=False, indent=2)
    return FILLED_COLLECTION


def run_newman(collection_path: str) -> subprocess.CompletedProcess:
    os.makedirs("test-results", exist_ok=True)
    cmd = (
        f'newman run "{collection_path}" '
        f'--reporters cli,json --reporter-json-export "{REPORT}"'
    )
    return subprocess.run(cmd, shell=True, capture_output=True, text=True, encoding="utf-8")


def summarize(report_path: str) -> dict:
    """Newman JSON hisobotidan xulosa. bridge_ok: KNOWN_QUIRKS'dan tashqari xato
    yo'q VA visit status=C ga yetgan."""
    with open(report_path, encoding="utf-8") as f:
        rep = json.load(f)
    steps, real_failures, visit_completed, visit_id = [], [], False, None
    for e in rep["run"]["executions"]:
        assertions = e.get("assertions", [])
        failed = [a["assertion"] for a in assertions if a.get("error")]
        real = [a for a in failed if a not in KNOWN_QUIRKS]
        real_failures.extend(real)
        if "visit is completed (status C)" in [a["assertion"] for a in assertions if not a.get("error")]:
            visit_completed = True
        # visit_id — Step 3 (end) so'rov body'sidagi resolvлаган {{visit_id}} dan
        if "end visit" in e["item"]["name"]:
            mm = re.search(r'"visit_id":(\d+)', e.get("request", {}).get("body", {}).get("raw", ""))
            if mm:
                visit_id = mm.group(1)
        steps.append({
            "step": e["item"]["name"],
            "http": e.get("response", {}).get("code"),
            "failed": failed,
            "ok": not real,
        })
    stats = rep["run"]["stats"]["assertions"]
    return {
        "steps": steps,
        "assertions_total": stats["total"],
        "assertions_failed": stats["failed"],
        "real_failures": real_failures,
        "visit_completed_status_C": visit_completed,
        "visit_id": visit_id,
        "bridge_ok": not real_failures and visit_completed,
    }


# ======================================================================================
# WEB helperlari — agent yaratish, Визиты tekshiruvlari, tozalash
# ======================================================================================

def _goto_person_users(page: Page, m: BasePage) -> None:
    """Модератор → Пользователи (person/user_list) — GUARD-SIZ.

    flow_navigate ISHLATILMAYDI: person moduli sekin yuklanadi, URL
    "intro/dashboard"да kechikib turadi va flow_navigate'ning dashboard-guard'i
    qayta bosib navigatsiyani buzadi. Tabni ochib menuitem bosamiz."""
    tab = page.get_by_role("button", name="Модератор")
    if tab.get_attribute("aria-expanded") != "true":
        tab.click()
    page.get_by_role("menuitem", name="Пользователи", exact=True).click()
    # sbmv sahifalaridan (Планы/Визиты) o'tganда title outlet eski nomda ("Планы")
    # qolib ketadi — expect_heading ISHONCHSIZ. URL + person ro'yxatiga XOS "Создать"
    # tugmasi kutiladi (sbmv user_list'da bu tugma yo'q — ishonchli belgi).
    page.wait_for_url(lambda u: "person" in u, timeout=60_000)
    expect(page.get_by_role("button", name="Создать")).to_be_visible(timeout=60_000)
    m.settle()


def run_create_agent(page: Page) -> str:
    """Модератор → Пользователи: Агент rolli yangi user yaratadi va ФИО ni
    qaytaradi. Har chaqiruvда unikal nom+telefon (vaqt+random)."""
    m = BasePage(page)
    code = f"{str(int(time.time()))[-6:]}{random.randint(0, 9)}"
    name = f"agent-{code}"

    with allure.step("Навигация: Модератор → Пользователи"):
        _goto_person_users(page, m)

    with allure.step(f"Создать: Агент rolli Пользователь ({name})"):
        m.open_create()
        m.expect_heading("Пользователь (Создание)")
        m.input(label="ФИО", value=name)
        # Логин/Пароль readonly — BasePage.input avval click (focus) qiladi
        m.input(label="Логин", value=name)
        m.input(label="Пароль", value="1")  # yaratilgan sub-userlar paroli "1" (group_a bilan bir xil)
        # Роли multi-select: "Агент" birinchi 10 tada emas, m.select filtr yozib topadi
        m.select("Агент", label="Роли")
        m.input(label="Код", value=code)
        phone = f"+998(93)-{code[0:3]}-{code[3:5]}-{code[5:7]}"
        m.input(label="Номер телефона", value=phone)

    with allure.step("Сохранить"):
        m.save()
        # Saqlangach redirect BARQAROR EMAS: ba'zан person ro'yxatiga, ba'zан
        # biruni/intro/dashboard'ga o'tadi (uzoq zanjirda kuzatilgan, 2026-08-05
        # test_050). expect_heading("Пользователи") shu sabab flaky yiqilar edi —
        # ro'yxatga ISHONCHLI qayta kiramiz (run_field_group ham save'дан keyin
        # flow_navigate bilan qaytadi). Agent baribir yaratilgan (save o'tgan).
        _goto_person_users(page, m)
    return name


def _goto_visits(page: Page, m: BasePage) -> None:
    """Модератор → Визиты. Plan/visit_view'dan o'tganда sbmv title outlet'i "Планы"да
    qolishi mumkin — expect_heading ISHONCHSIZ, shuning uchun URL (visit_list) kutamiz."""
    flow_navigate(page, tab="Модератор", name="Визиты")
    page.wait_for_url(lambda u: "visit_list" in u, timeout=30_000)
    m.settle()


def _deactivate_agent(page: Page, m: BasePage, agent: str) -> None:
    """Test agentini Неактивный qiladi (tozalash — agentlar ko'payib ketmasin).

    Visit/lead'li agentni O'CHIRIB bo'lmaydi ("child record found"); Роли →
    Пользователи (biruni/md) ro'yxatida ham ko'rinmaydi — shuning uchun person
    ro'yxatida (yaratilgan joy) Изменить → Статус switch OFF → Сохранить: agent
    Неактивный bo'lib default ro'yxatдан yo'qoladi."""
    _goto_person_users(page, m)
    m.search(agent)
    m.click_grid_row(agent)
    m.click_button("Изменить")
    m.expect_heading("Пользователь (Редактирования)")
    # "Статус: Активный" label anchored mos EMAS — formadagi yagona smt-switch'ni
    # to'g'ridan-to'g'ri Неактивный (OFF) qilamiz
    m.checkbox(locator="smt-switch", checked=False)
    m.save()
    # Save redirect BARQAROR EMAS (ba'zан dashboard'ga o'tadi — run_create_agent'да
    # qayd etilgan); expect_heading("Пользователи") shu sabab flaky yiqilardi.
    # Deaktivatsiya save() bilan tasdiqlandi (forma yopildi) — ro'yxatga ISHONCHLI
    # qaytamiz (heading assert emas).
    _goto_person_users(page, m)


def verify_visit_completed_web(page: Page, m: BasePage, agent: str, visit_id: str) -> None:
    """Визиты ro'yxatida visit "Завершен" ekanini + Просмотр ochilishini tekshiradi.
    Agent nomi UNIKAL (har run) — aynan shu run visitini topadi (Завершен = C)."""
    _goto_visits(page, m)
    m.search(agent)
    row = m.grid_row(agent, "Завершен")
    # Visit qatorida client/agent kataklari BUTTON (bosilsa boshqa joyga ketadi) —
    # ID katagini (matn) bosib qatorni tanlaymiz (exact: agent code'iga tushmasin)
    row.get_by_text(visit_id, exact=True).click()
    m.settle()
    m.click_button("Просмотр")
    m.expect_heading("Визит (Просмотр)")
    m.click_button("Результаты анализа")  # sub-bo'lim ochiladi


def confirm_visit_lead(page: Page, m: BasePage, agent: str, visit_id: str) -> None:
    """Visit lead'ini "Подтвержден" qiladi (Новый → Подтвержден)."""
    _goto_visits(page, m)
    m.search(agent)
    m.grid_row(agent, "Завершен").get_by_text(visit_id, exact=True).click()
    m.settle()
    m.click_button("Лиды")
    m.expect_heading("Лиды")
    # Lead qatorida Пользователь=agent (plain matn, BUTTON emas) — click_grid_row xavfsiz
    m.click_grid_row(agent)
    m.click_button("Подтвержден")
    m.confirm("да")  # "Изменить на Подтвержден?" cdk-overlay dialogi
    m.grid_row(agent, "Подтвержден")


# ======================================================================================
# Recurrence helperlari
# ======================================================================================

# date.weekday(): Пн=0 ... Вс=6
WEEKDAY_LABELS = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
WEEK_SECTIONS = {
    1: "Каждую неделю",
    2: "Каждую вторую неделю",
    3: "Каждую третью неделю",
    4: "Каждую четвертую неделю",
    5: "Каждую пятую неделю",
}
MONTH_SECTION = "Раз в месяц"
WINDOW_DAYS = 31  # server oynasi ~1 oy (25.08=+28 kirdi, 29.08=+32 kirmadi)


def _open_agent_plans(page: Page, m: BasePage, agent: str) -> None:
    """Планирование визитов → agent qatori → "Планы" ro'yxati.

    DIQQAT: plan_list'dan qaytganда sbmv title outlet'i "Планы"да qolib ketadi —
    expect_heading(MENU) ISHONCHSIZ (_goto_visits'dagi muammo), URL kutiladi."""
    flow_navigate(page, tab="Модератор", name=MENU)
    page.wait_for_url(lambda u: "sbmv/user_list" in u, timeout=30_000)
    m.settle()
    page.get_by_text(agent, exact=True).first.click()
    page.get_by_role("button", name="Планы").first.click()
    m.settle()
    m.expect_heading(f"Сотрудник: {agent}")


def _open_plan_form(page: Page, m: BasePage) -> None:
    """Планы ro'yxatida: Добавить → Сегодня → Получить (recurrence panel chiqadi)."""
    m.click_button("Добавить", exact=True)
    page.get_by_role("textbox", name="Выберите дату").click()
    page.get_by_role("button", name="Сегодня").click()
    m.click_button("Получить")


def _pick_in_section(page: Page, section_title: str, button_label: str) -> None:
    """Recurrence panelida bo'lim sarlavhasi orqali scope'lab tugma bosadi
    (hafta kuni nomlari 5 bo'limda takror — sarlavha scope SHART)."""
    section = page.get_by_text(section_title, exact=True).locator("xpath=..")
    section.get_by_role("button", name=button_label, exact=True).click()


def _add_point_and_save(page: Page, m: BasePage, agent: str) -> None:
    """Birinchi mavjud nuqtani qo'shib saqlaydi (header tugmalari nth 0-1,
    birinchi qator nth 2) va Планы ro'yxatiga qaytishни kutadi."""
    page.get_by_role("button", name="Добавить").nth(2).click()
    m.wait_for_loader()
    m.save()
    m.expect_heading(f"Сотрудник: {agent}")


def _plan_dates(page: Page) -> list[date]:
    """Планы ro'yxatidagi barcha "Дата визита" (dd.mm.yyyy) → saralangan list."""
    raw = page.evaluate(
        """() => {
            const cells = [...document.querySelectorAll('*')].filter(
                e => e.children.length === 0
                     && /^\\d{2}\\.\\d{2}\\.\\d{4}$/.test(e.textContent.trim()));
            return [...new Set(cells.map(c => c.textContent.trim()))];
        }"""
    )
    out = []
    for s in raw:
        d, mo, y = (int(x) for x in s.split("."))
        out.append(date(y, mo, d))
    return sorted(out)


def _expected_week_dates(n: int, start: date, offset: int) -> list[date]:
    """Har N-hafta modeli: tanlangan hafta kuni start HAFTASIDAN (dushanba-anchored)
    (N-1)-haftada, keyin har N-hafta; oynadan (31 kun) chiqqani kesiladi.

    DIQQAT: oldingi model `start + (N-1)*7 + offset` — offset
    hafta kunini KEYINGA suradi deb faraz qilardi. Aslida ilova tanlangan hafta kunini
    o'sha rekurrens HAFTASINING kuniga joylaydi; agar tanlangan kun start kunidan hafta
    ichida OLDINROQ bo'lsa (offset 7 dan oshib WRAP qilsa), sana 7 kun OLDINGA tushadi.
    Bu 2026-08-06 (Пайшанба) da every_5_weeks chained (Пн tanlanib, sana Sep 7 emas
    Aug 31 bo'lgan) da noto'g'ri 0 kutib yiqilgan edi. Endi start haftasining
    dushanbasidan + (N-1)*7 + wd bilan aniq kalendar sanaga bog'lanadi (offset=0
    standalone testlarga ta'sir yo'q — wrap faqat chained variantlarda bo'ladi)."""
    wd = (start.weekday() + offset) % 7
    week0_monday = start - timedelta(days=start.weekday())
    out, d = [], week0_monday + timedelta(days=(n - 1) * 7 + wd)
    while (d - start).days < 0:            # tanlangan kun start'dan oldin qolsa keyingi tsiklga
        d += timedelta(days=n * 7)
    while (d - start).days <= WINDOW_DAYS:
        out.append(d)
        d += timedelta(days=n * 7)
    return out


def _run_week_interval(page: Page, agent: str, n: int, *,
                       offset: int = 0, whole_list: bool = True) -> None:
    """Umumiy oqim: N-hafta bo'limida hafta kunini tanlab reja yaratadi va tekshiradi.

    offset=0, whole_list=True (ALOHIDA test, TOZA yangi agent): BUGUNGI hafta kuni
      tanlanadi — kutilgan visitlar soni 5/2/1/1/1 (N=1..5) va ro'yxatdagi BUTUN
      sanalar aynan kutilganlarga teng bo'lishi tekshiriladi (agent toza!).
    offset=N-1, whole_list=False (ZANJIR, bitta agent): har variant o'z hafta
      kunida — faqat shu hafta kuni guruhi tekshiriladi (5/2/1/1/0 — zanjirda
      5-hafta sanasi +32 kun, oynadan tashqarida)."""
    m = BasePage(page)
    today = date.today()
    wd = (today.weekday() + offset) % 7
    label = WEEKDAY_LABELS[wd]
    section = WEEK_SECTIONS[n]

    with allure.step(f"{section} → {label}: reja yaratish"):
        _open_agent_plans(page, m, agent)
        _open_plan_form(page, m)
        _pick_in_section(page, section, label)
        _add_point_and_save(page, m, agent)

    with allure.step(f"{section}: sanalarni tekshirish"):
        horizon = today + timedelta(days=WINDOW_DAYS)
        expected = _expected_week_dates(n, today, offset)

        def _current_group() -> list[date]:
            if whole_list:
                # yangi (toza) agent — ro'yxatdagi BARCHA sanalar aynan kutilganlar
                return [d for d in _plan_dates(page) if today <= d]
            return [d for d in _plan_dates(page)
                    if d.weekday() == wd and today <= d <= horizon]

        # Plan grid save'дан keyin ASINXRON renderlanadi — bir martalik o'qishда
        # _plan_dates bo'sh/chala qaytishi mumkin (plan-dates-async-grid-flaky).
        # Kutilgan holat kelguncha (yoki deadline) qayta o'qiymiz; kelsa darhol
        # chiqamiz, haqiqiy nomuvofiqlikда esa oldingidek aniq xato beramiz.
        deadline = time.monotonic() + 15
        group = _current_group()
        while group != expected and time.monotonic() < deadline:
            page.wait_for_timeout(1_000)
            group = _current_group()

        assert group == expected, (
            f"{section} ({label}): kutilgan {len(expected)} ta visit {expected}, "
            f"olindi {len(group)} ta {group}"
        )
        allure.attach(f"{section} ({label}): {group}", name="visit_dates",
                      attachment_type=allure.attachment_type.TEXT)


# ======================================================================================
# run_* — biznes logika (login qilinganini va agent mavjudligini kutadi)
# ======================================================================================

def run_weekly(page: Page, agent: str, *, chained: bool = False) -> None:
    """Каждую неделю: bugungi hafta kunida aynan 5 ta ketma-ket visit."""
    _run_week_interval(page, agent, 1, offset=0, whole_list=not chained)


def run_every_2_weeks(page: Page, agent: str, *, chained: bool = False) -> None:
    """Har 2 hafta: toza agentда bugungi hafta kunida 2 ta visit (+7, +21)."""
    _run_week_interval(page, agent, 2, offset=1 if chained else 0,
                       whole_list=not chained)


def run_every_3_weeks(page: Page, agent: str, *, chained: bool = False) -> None:
    """Har 3 hafta: toza agentда 1 ta visit (+14)."""
    _run_week_interval(page, agent, 3, offset=2 if chained else 0,
                       whole_list=not chained)


def run_every_4_weeks(page: Page, agent: str, *, chained: bool = False) -> None:
    """Har 4 hafta: toza agentда 1 ta visit (+21)."""
    _run_week_interval(page, agent, 4, offset=3 if chained else 0,
                       whole_list=not chained)


def run_every_5_weeks(page: Page, agent: str, *, chained: bool = False) -> None:
    """Har 5 hafta: toza agentда (bugungi kun) 1 ta visit (+28). Zanjirda esa
    hafta kuni +4 surilgani uchun sana +32 — oynadan tashqarida, 0 visit."""
    _run_week_interval(page, agent, 5, offset=4 if chained else 0,
                       whole_list=not chained)


def run_monthly(page: Page, agent: str) -> None:
    """Раз в месяц: bugungi kun raqami — bugungi visit yaratiladi (keyingi oy
    sanasi oyna chegarasida, serverga bog'liq — subset tekshiruvi)."""
    m = BasePage(page)
    today = date.today()

    with allure.step(f"{MONTH_SECTION} → {today.day}: reja yaratish"):
        _open_agent_plans(page, m, agent)
        _open_plan_form(page, m)
        _pick_in_section(page, MONTH_SECTION, str(today.day))
        _add_point_and_save(page, m, agent)

    with allure.step(f"{MONTH_SECTION}: sanalarni tekshirish"):
        horizon = today + timedelta(days=WINDOW_DAYS)

        def _current_group() -> list[date]:
            return [d for d in _plan_dates(page)
                    if d.day == today.day and today <= d <= horizon]

        # Plan grid save'дан keyin ASINXRON renderlanadi — bir martalik o'qishда
        # _plan_dates bo'sh qaytib, bugungi visit "yaratilmadi" bo'lib xato berardi
        # (plan-dates-async-grid-flaky; _run_week_interval'dagi kabi). Bugungi kun
        # guruhda paydo bo'lguncha (yoki deadline) qayta o'qiymiz.
        deadline = time.monotonic() + 15
        group = _current_group()
        while today not in group and time.monotonic() < deadline:
            page.wait_for_timeout(1_000)
            group = _current_group()

        assert today in group, f"{MONTH_SECTION}: bugungi visit yaratilmadi ({group})"
        # keyingi oy shu kuni (31 kunlik oyna chegarasida) — bo'lsa ham xato emas
        ny, nm = (today.year + (today.month == 12), today.month % 12 + 1)
        try:
            allowed = {today, date(ny, nm, today.day)}
        except ValueError:  # masalan 31-yanvar → fevralda yo'q
            allowed = {today}
        extra = set(group) - allowed
        assert not extra, f"{MONTH_SECTION}: kutilmagan sanalar {sorted(extra)}"
        allure.attach(f"{MONTH_SECTION} ({today.day}): {group}", name="visit_dates",
                      attachment_type=allure.attachment_type.TEXT)


def run_mobile_visit(page: Page, agent: str) -> dict:
    """Agent sifatida cookie olib Postman (newman) scenariosini yurgizadi:
    exp_client_list → begin → autosave → end → status C, xulosani qaytaradi.

    Faqat BUGUNGI rejasi bor agent uchun ishlaydi (weekly/monthly bugunni beradi;
    har 2/3/4/5 hafta birinchi visiti kelajakda — exp_client_list ko'rmaydi).
    Планы ro'yxatida (plan_list URL) chaqirilishi kerak — user_id URL'dan olinadi."""
    user_id = re.search(r"user_id=(\d+)", page.url).group(1)
    agent_login = f"{agent}@{COMPANY_CODE}"

    with allure.step(f"API: agent sifatida login ({agent_login}) va cookie olish"):
        agent_ctx = page.context.browser.new_context()
        try:
            cookie = cookie_from_context(agent_ctx, agent_login, "1")
        finally:
            agent_ctx.close()
        assert "JSESSIONID" in cookie, f"session cookie olinmadi: {cookie[:80]}"

    with allure.step("API: newman — exp_client_list + begin → autosave → end → status C"):
        run_newman(fill_collection(cookie, user_id))
        summary = summarize(REPORT)
        allure.attach(str(summary), name="newman_summary",
                      attachment_type=allure.attachment_type.TEXT)
        assert summary["visit_completed_status_C"], (
            f"Visit 'C' (yakunlangan) holatiga yetmadi: {summary}"
        )
        assert not summary["real_failures"], (
            f"Newman'da haqiqiy xatolar bor: {summary['real_failures']}"
        )
    return summary


# ======================================================================================
# test_* — har biri alohida (o'z agenti bilan), oxirida zanjir
# ======================================================================================

def _standalone(page: Page, runner) -> None:
    """Alohida test skeleti: login → yangi agent → runner → agentni Неактивный."""
    authorization(page)
    agent = run_create_agent(page)
    runner(page, agent)
    with allure.step(f"Tozalash: '{agent}' agentini Неактивный qilish"):
        _deactivate_agent(page, BasePage(page), agent)


@allure.epic("Документы")
@allure.feature("Планирование визитов")
@allure.story("Такрорланиш (recurrence)")
@allure.title("Каждую неделю — 5 ta ketma-ket visit")
def test_weekly(page: Page) -> None:
    _standalone(page, run_weekly)


@allure.epic("Документы")
@allure.feature("Планирование визитов")
@allure.story("Такрорланиш (recurrence)")
@allure.title("Каждую вторую неделю — toza agentда 2 ta visit (orasi 14 kun)")
def test_every_2_weeks(page: Page) -> None:
    _standalone(page, run_every_2_weeks)


@allure.epic("Документы")
@allure.feature("Планирование визитов")
@allure.story("Такрорланиш (recurrence)")
@allure.title("Каждую третью неделю — toza agentда 1 ta visit (+14 kun)")
def test_every_3_weeks(page: Page) -> None:
    _standalone(page, run_every_3_weeks)


@allure.epic("Документы")
@allure.feature("Планирование визитов")
@allure.story("Такрорланиш (recurrence)")
@allure.title("Каждую четвертую неделю — toza agentда 1 ta visit (+21 kun)")
def test_every_4_weeks(page: Page) -> None:
    _standalone(page, run_every_4_weeks)


@allure.epic("Документы")
@allure.feature("Планирование визитов")
@allure.story("Такрорланиш (recurrence)")
@allure.title("Каждую пятую неделю — toza agentда 1 ta visit (+28 kun)")
def test_every_5_weeks(page: Page) -> None:
    _standalone(page, run_every_5_weeks)


@allure.epic("Документы")
@allure.feature("Планирование визитов")
@allure.story("Такрорланиш (recurrence)")
@allure.title("Раз в месяц — bugungi kunga visit")
def test_monthly(page: Page) -> None:
    _standalone(page, run_monthly)
