"""Планирование визитов — recurrence variantlari + Web↔Mobile Visit API (bitta fayl).

Avval ikki fayl edi (test_visit_bridge.py + test_visit_recurrence.py) — ikkalasi ham
visitni tekshirgani uchun 2026-07-29 da BITTA faylga birlashtirildi. Ichida:
  - Mobil visit API: `run_mobile_visit` — `utils/base_api.py` (VisitApi, `requests`)
    orqali exp_client_list→begin→autosave→end→status C (newman/Postman CLI YO'Q)
  - WEB helperlari: agent yaratish, Визиты/Лиды tekshiruvлари, agent tozalash
  - recurrence CRUD: har variant ALOHIDA run_/test_ juftligi
      run_weekly / run_every_2_weeks / ... / run_every_5_weeks / run_monthly
  - OXIRIDA test_recurrence_all — bitta login + bitta agent bilan HAMMASI:
      6 recurrence varianti + mobil visit (begin→autosave→end→C) +
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
(HttpOnly); visit_user_id=Планы URL'idan; visit_person_id=exp_client_list avtomatik.
Mobil visit faqat BUGUNGI rejaga ishlaydi (weekly/monthly beradi; har 2/3/4/5
hafta birinchi visiti kelajakda — exp_client_list ko'rmaydi).
"""
import random
import re
import time
from datetime import date, timedelta

import allure
from playwright.sync_api import Page, expect

from flows.flow_authorization import authorization, COMPANY_CODE
from flows.flow_navbar import flow_navigate
from utils.base_page import BasePage
from utils.base_api import VisitApi, login_cookie

MENU = "Планирование визитов"


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
    """Agent sifatida cookie olib mobil visit API scenariosini bajaradi (requests,
    ``VisitApi``): exp_client_list → begin → autosave → end → exp_client_info (status
    'C'). ``{"visit_id", "visit_completed_status_C"}`` xulosasini qaytaradi.

    Faqat BUGUNGI rejasi bor agent uchun ishlaydi (weekly/monthly bugunni beradi;
    har 2/3/4/5 hafta birinchi visiti kelajakda — exp_client_list ko'rmaydi).
    Планы ro'yxatida (plan_list URL) chaqirilishi kerak — user_id URL'dan olinadi."""
    user_id = re.search(r"user_id=(\d+)", page.url).group(1)
    agent_login = f"{agent}@{COMPANY_CODE}"

    with allure.step(f"API: agent sifatida login ({agent_login}) va cookie olish"):
        agent_ctx = page.context.browser.new_context()
        try:
            cookie = login_cookie(agent_ctx, agent_login, "1")
        finally:
            agent_ctx.close()

    with allure.step("API: exp_client_list → begin → autosave → end → status C"):
        api = VisitApi(cookie)
        clients, _ = api.client_list()
        assert clients, "bugungi rejada chana topilmadi (exp_client_list bo'sh)"
        c = clients[0]
        person_id = VisitApi.person_id(c)
        visit_id = api.run_visit(person_id, user_id, VisitApi.legal_form_id(c))
        data = api.client_info(person_id, user_id)
        assert str(data.get("visit_id")) == visit_id and data.get("visit_status") == "C", (
            f"Visit 'C' (yakunlangan) holatiga yetmadi: "
            f"visit_id={data.get('visit_id')} status={data.get('visit_status')}"
        )
        summary = {"visit_id": visit_id, "visit_completed_status_C": True}
        allure.attach(str(summary), name="visit_api_summary",
                      attachment_type=allure.attachment_type.TEXT)
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
