"""E2E: Агент yaratish → haftalik reja (5 chana) → API orqali 2 visit → Треking.

TEST CASE (4 qadam)
-------------------
1) UI  — Модератор → Пользователи: rol=Агент yangi user (uniq nom+parol).
2) UI  — Модератор → Планирование визитов: agentга "Каждую неделю" (BUGUNGI
         hafta kuni) reja, 5 ta chana biriktirib saqlash.
3) API — mavjud "plan visit API test" (test_Plan_visit_recurrence.py) endpoint
         va payloadlari asosida, AUTENTIFIKATSIYA yangi agentга almashtirilgan
         holda, kamida 2 ta chana uchun visit bajariladi (begin→autosave→end).
4) UI  — Модератор → Отслеживание пользователей: sana avtomatik bugungi, agent
         tanlanadi, 2 ta visit ("Визиты (2)") ko'rinishi tekshiriladi.

3-QADAM — MOBIL VISIT API (utils/base_api.py)
--------------------------------------------------------------------------------
- API so'rovlari `utils/base_api.py` (VisitApi, `requests`) da — endpointlar
  (/…/b/sb/external:export | :import) va begin→save→end payloadlari BITTA joyda
  (newman/Postman CLI bog'liqligi YO'Q). Bu fayl faqat ORKESTRATSIYA qiladi:
  (a) AUTH — `login_cookie(ctx, agent_login, "1")` yangi agent sifatida login qilib
  JSESSIONID cookie oladi; (b) `VisitApi.client_list()` bilan bugungi rejadagi
  chanalarni olib, birinchi ``N_VISITS`` ta chana bo'yicha `api.run_visit(...)`
  (begin→temporary_save→end) chaqiradi (spec: kamida 2 visit).

TRACKING METKALARI
------------------
Xarita — Leaflet+Yandex; "Завершённый визит" (yashil) markerlari Leaflet pane'da
`img.leaflet-marker-icon` bo'lib render bo'ladi, ammo yashil-faqat filtrlash
ikonka src'iga bog'liq (2 visitli agent bilan aniqlanishi kerak — `_count_map_markers`
da TODO). ISHONCHLI hard-assert — o'ng paneldagi "Визиты (N)" hisoblagichi:
u REJANI emas, bajarilgan VIZITNI sanaydi (rejasi bor, visiti yo'q agent "Визиты (0)"
ko'rsatadi — MCP tasdiqlangan) — 2 API visiti uchun aynan "Визиты (2)".
"""
import re
from datetime import date

import allure
from playwright.sync_api import Page, expect

from flows.flow_authorization import COMPANY_CODE, authorization
from flows.flow_navbar import flow_navigate
from utils.base_page import BasePage
from utils.base_api import VisitApi, login_cookie

# UI helperlari (agent yaratish / reja formasi) plan-visit test faylida — QAYTA
# ISHLATILADI. API so'rovlari endi utils/base_api.py da (yuqorida import qilingan) —
# begin/save/end payloadlari BITTA joyda, bu fayl faqat CHAQIRADI.
from tests.test_document.test_Plan_visit_recurrence import (
    WEEKDAY_LABELS,
    run_create_agent,
    _deactivate_agent,
    _open_agent_plans,
    _open_plan_form,
    _pick_in_section,
)

WEEKLY_SECTION = "Каждую неделю"
N_POINTS = 5           # rejaga biriktiriladigan chana soni (precondition: >=5 chana)
N_VISITS = 2           # API orqali bajariladigan visit soni (spec: kamida 2)
PASSWORD = "1"  # yaratilgan agent paroli "1" (run_create_agent bilan bir xil, group_a uslubi)


# ══════════════════════════════════════════════════════════════════════════════
# 2-QADAM — haftalik reja + 5 chana (UI)
# ══════════════════════════════════════════════════════════════════════════════
def create_weekly_plan_5_points(page: Page, agent: str) -> str:
    """Agentга "Каждую неделю" (BUGUNGI hafta kuni) reja yaratib, ``N_POINTS`` ta
    chanani biriktiradi va saqlaydi. Agentning user_id (Планы URL'idan) ni
    qaytaradi — 3-qadam API visitlari uchun kerak.

    Chana qo'shish: har "Доступные" qatorining o'z "Добавить" tugmasi bor; bosilgач
    qator "Выбранные"ga o'tadi va ro'yxat QAYTA INDEKSLANADI — shuning uchun birinchi
    ma'lumot qatorining "Добавить"i (get_by_role nth(2): nth 0-1 sarlavha tugmalari,
    nth 2 birinchi qator) ``N_POINTS`` marta bosiladi."""
    m = BasePage(page)
    label = WEEKDAY_LABELS[date.today().weekday()]

    with allure.step(f"Планирование визитов → '{agent}' → Планы"):
        _open_agent_plans(page, m, agent)
        user_id = re.search(r"user_id=(\d+)", page.url).group(1)

    with allure.step(f"Добавить → Дата начала = сегодня → Получить"):
        _open_plan_form(page, m)

    with allure.step(f"{WEEKLY_SECTION} → {label} (bugungi hafta kuni)"):
        _pick_in_section(page, WEEKLY_SECTION, label)

    with allure.step(f"{N_POINTS} ta chanani '+'(Добавить) orqali biriktirish"):
        add_btn = page.get_by_role("button", name="Добавить")
        for _ in range(N_POINTS):
            add_btn.nth(2).click()   # birinchi ma'lumot qatori (qayta indekslanadi)
            m.wait_for_loader()

    with allure.step(f"Выбранные'да {N_POINTS} ta ekanini tekshirib Сохранить"):
        # "Выбранные N" tab ikki DOM elementга mos (smt-tab-button + ichki button) — .first
        expect(page.get_by_role("button", name=f"Выбранные {N_POINTS}").first).to_be_visible(timeout=15_000)
        m.save()
        m.expect_heading(f"Сотрудник: {agent}")

    return user_id


# ══════════════════════════════════════════════════════════════════════════════
# 3-QADAM — API orqali visit (VisitApi/requests; auth = yangi agent)
# ══════════════════════════════════════════════════════════════════════════════
def run_api_visits(page: Page, agent: str, user_id: str, count: int = N_VISITS) -> list:
    """Yangi agent sifatida cookie olib (auth ALMASHTIRILGAN), bugungi rejadagi
    birinchi ``count`` ta chana uchun visitni API orqali bajaradi:
    exp_client_list → (har chana: begin → temporary_save → end). Bajarilgan
    visit_id'lar ro'yxatini qaytaradi.

    Endpoint/payloadlar utils/base_api.py (VisitApi) da — bu funksiya faqat
    ORKESTRATSIYA qiladi (auth almashtirish + count marta chana bo'yicha aylanish)."""
    agent_login = f"{agent}@{COMPANY_CODE}"

    with allure.step(f"API auth: '{agent_login}' sifatida login → JSESSIONID cookie"):
        ctx = page.context.browser.new_context()
        try:
            cookie = login_cookie(ctx, agent_login, PASSWORD)
        finally:
            ctx.close()

    api = VisitApi(cookie)
    with allure.step("API: c:exp_client_list — bugungi rejadagi chanalar"):
        clients, _ = api.client_list()
        assert len(clients) >= count, (
            f"kamida {count} chana kutilgan edi, rejada {len(clients)} ta topildi"
        )

    visit_ids = []
    for i, c in enumerate(clients[:count], start=1):
        person_id = VisitApi.person_id(c)
        with allure.step(f"API visit {i}/{count}: begin → save → end (person_id={person_id})"):
            visit_ids.append(api.run_visit(person_id, user_id, VisitApi.legal_form_id(c)))

    allure.attach(str(visit_ids), name="api_visit_ids",
                  attachment_type=allure.attachment_type.TEXT)
    return visit_ids


# ══════════════════════════════════════════════════════════════════════════════
# 4-QADAM — Отслеживание пользователей (UI)
# ══════════════════════════════════════════════════════════════════════════════
def _count_map_markers(page: Page) -> int:
    """Leaflet xarita markerlari soni (best-effort).

    TODO: "Завершённый визит" (YASHIL) markerlarni aniq ikonka src bo'yicha
    filtrlash. Reja 5 chana (Плановый) + 2 bajarilgan (Завершённый) bo'lgani uchun
    umumiy marker soni 2 ga TENG EMAS — yashil-faqat sanash ikonka URL'ini talab
    qiladi; uni 2 tasi Завершён/qolgani Плановый bo'lgan agent bilan MCP orqali
    aniqlash kerak. Asosiy ishonchli tekshiruv — "Визиты (N)" (pastda hard-assert)."""
    try:
        return page.locator(".leaflet-marker-pane img.leaflet-marker-icon").count()
    except Exception:
        return -1


def verify_tracking(page: Page, agent: str, expected_visits: int = N_VISITS) -> None:
    """Отслеживание пользователей: sana avtomatik BUGUNGI, agent tanlanadi va
    o'ng paneldagi "Визиты (N)" bajarilgan visitlar soniga teng ekani tekshiriladi
    (N=expected_visits). Xarita markerlari best-effort qayd etiladi."""
    m = BasePage(page)

    with allure.step("Модератор → Отслеживание пользователей"):
        flow_navigate(page, tab="Модератор", name="Отслеживание пользователей")
        page.wait_for_url(lambda u: "user_locations" in u, timeout=30_000)
        m.settle()

    with allure.step("Sana avtomatik bugungi kunga o'rnatilganini tekshirish"):
        today_str = date.today().strftime("%d.%m.%Y")
        expect(page.get_by_role("textbox", name="Выберите дату")).to_have_value(today_str)

    # "Визиты (N)" REJANI emas, bajarilgan VIZITNI sanaydi. API visit'lari treking
    # agregatsiyasida KECHIKIB (eventual-consistency) ko'rinadi — hisoblagich darrov
    # to'g'ri qiymatga yetmasligi mumkin (flaky, jonli run 2026-08-24). Shu sabab
    # agentni tanlab hisoblagichni tekshirishni RETRY qilamiz: har urinishда sahifani
    # qayta yuklab (yangi agregatsiya so'rovi) agentni qayta tanlaymiz.
    target = page.get_by_role("button", name=f"Визиты ({expected_visits})").first

    def _select_agent() -> None:
        # "Визиты (N)" tab ikki DOM elementга mos (smt-tab-button + ichki button) — .first
        box = page.get_by_role("textbox", name="Выберите...")
        box.click()
        box.fill(agent)
        page.locator(".cdk-overlay-container li").filter(has_text=agent).first.click()
        m.settle()

    with allure.step(f"Агент '{agent}' tanlab '{expected_visits}' visitni kutish (retry)"):
        found = False
        # API visit'lari treking agregatsiyasida KECHIKIB ko'rinadi; server YUK
        # ostida (masalan parallel run) kechikish uzayadi — shu sabab hisoblagich
        # aynan bu joyда flaky yiqilardi (Telegram run, 2026-08-28). Retry 4→6 va
        # har qayta urinishдан oldin agregatsiyaga qo'shimcha vaqt (3s) beramiz.
        for attempt in range(6):
            if attempt:
                page.wait_for_timeout(3_000)  # agregatsiya yetguncha kutish
                page.reload()
                page.wait_for_url(lambda u: "user_locations" in u, timeout=30_000)
                m.settle()
            _select_agent()
            try:
                expect(target).to_be_visible(timeout=20_000)
                found = True
                break
            except AssertionError:
                pass  # keyingi urinishда qayta yuklaymiz (agregatsiya yetguncha)
        if not found:
            expect(target).to_be_visible(timeout=10_000)  # yakuniy aniq xato
        markers = _count_map_markers(page)
        allure.attach(f"leaflet markerlari (best-effort, yashil-faqat emas): {markers}",
                      name="map_markers", attachment_type=allure.attachment_type.TEXT)


# ══════════════════════════════════════════════════════════════════════════════
# TEST — to'liq E2E zanjir
# ══════════════════════════════════════════════════════════════════════════════
@allure.epic("Документы")
@allure.feature("Отслеживание пользователей")
@allure.story("E2E: агент → план → API визит → трекинг")
@allure.title("Агент yaratish → 5 chanali reja → API orqali 2 visit → трекинг (2 visit)")
def test_agent_visit_tracking(page: Page) -> None:
    with allure.step("Tizimga kirish (admin)"):
        authorization(page)

    with allure.step("1-qadam: rol=Агент yangi Пользователь yaratish"):
        agent = run_create_agent(page)

    with allure.step(f"2-qadam: '{WEEKLY_SECTION}' reja + {N_POINTS} chana"):
        user_id = create_weekly_plan_5_points(page, agent)

    with allure.step(f"3-qadam: API orqali {N_VISITS} ta visit (requests, auth=agent)"):
        visit_ids = run_api_visits(page, agent, user_id, count=N_VISITS)
        assert len(visit_ids) == N_VISITS, f"{N_VISITS} visit kutilgan, olindi {visit_ids}"

    with allure.step(f"4-qadam: Отслеживание — bajarilgan visitlar soni ({len(visit_ids)}) ko'rinishi"):
        # DINAMIK: nechta visit HAQIQATDA bajarilgan bo'lsa (len(visit_ids)), xaritada
        # shuncha ko'rinishi tekshiriladi — 5 bajarilsa 5, 3 bajarilsa 3, 2 bajarilsa 2.
        verify_tracking(page, agent, expected_visits=len(visit_ids))

    with allure.step(f"Tozalash: '{agent}' agentini Неактивный qilish"):
        # Visitли agentni O'CHIRIB bo'lmaydi (child record) — Неактивный qilinadi
        # (loyiha uslubi, test_Plan_visit_recurrence bilan bir xil).
        _deactivate_agent(page, BasePage(page), agent)
