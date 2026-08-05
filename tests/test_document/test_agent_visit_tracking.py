"""E2E: Агент yaratish → haftalik reja (5 chana) → API orqali 2 vizit → Треking.

TEST CASE (4 qadam)
-------------------
1) UI  — Модератор → Пользователи: rol=Агент yangi user (uniq nom+parol).
2) UI  — Модератор → Планирование визитов: agentга "Каждую неделю" (BUGUNGI
         hafta kuni) reja, 5 ta chana biriktirib saqlash.
3) API — mavjud "plan vizit API test" (test_Plan_visit_recurrence.py) endpoint
         va payloadlari asosida, AUTENTIFIKATSIYA yangi agentга almashtirilgan
         holda, kamida 2 ta chana uchun vizit bajariladi (begin→autosave→end).
4) UI  — Модератор → Отслеживание пользователей: sana avtomatik bugungi, agent
         tanlanadi, 2 ta vizit ("Визиты (2)") ko'rinishi tekshiriladi.

3-QADAM — MAVJUD API TESTIDAN NIMA OLINDI / NIMA O'ZGARDI (MCP dev/sm24 2026-08-03)
--------------------------------------------------------------------------------
- OLINDI: `cookie_from_context(ctx, login, parol)` — agent sifatida login qilib
  JSESSIONID cookie'sini oladi (test_Plan_visit_recurrence.py da ALLAQACHON
  parametrlangan — hardcoded emas, refaktor SHART emas). Endpointlar
  (/x24/b/sb/external:export | :import) va payload strukturasi o'sha fayldagi
  EMBEDDED Postman kolleksiyasidan aynan ko'chirildi (exp_client_list →
  imp_visit_begin → imp_temporary_visit_save → imp_visit_end).
- O'ZGARDI: (a) AUTH — endi yangi yaratilgan agentning login-paroli beriladi;
  (b) newman (Postman CLI) O'RNIGA `requests` ishlatiladi (spec talabi, newman
  o'rnatishga bog'liqlik yo'q); (c) bitta vizit o'rniga birinchi 2 ta chana
  bo'yicha SIKL — spec "kamida 2 vizit" talab qiladi.

TRACKING METKALARI
------------------
Xarita — Leaflet+Yandex; "Завершённый визит" (yashil) markerlari Leaflet pane'da
`img.leaflet-marker-icon` bo'lib render bo'ladi, ammo yashil-faqat filtrlash
ikonka src'iga bog'liq (2 vizitli agent bilan aniqlanishi kerak — `_count_map_markers`
da TODO). ISHONCHLI hard-assert — o'ng paneldagi "Визиты (N)" hisoblagichi:
u REJANI emas, bajarilgan VIZITNI sanaydi (rejasi bor, viziti yo'q agent "Визиты (0)"
ko'rsatadi — MCP tasdiqlangan) — 2 API viziti uchun aynan "Визиты (2)".
"""
import re
from datetime import date

import allure
import requests
from playwright.sync_api import Page, expect

from flows.flow_authorization import COMPANY_CODE, authorization
from flows.flow_navbar import flow_navigate
from utils.base_page import BasePage

# Mavjud plan-vizit test fayli — agent/reja/cookie helperlari va API konstantalari
# shu yerdan QAYTA ISHLATILADI (yangi selektor/login logikasi yozilmaydi).
from tests.test_document.test_Plan_visit_recurrence import (
    BASE_URL,
    WEEKDAY_LABELS,
    cookie_from_context,
    run_create_agent,
    _deactivate_agent,
    _open_agent_plans,
    _open_plan_form,
    _pick_in_section,
)

WEEKLY_SECTION = "Каждую неделю"
N_POINTS = 5           # rejaga biriktiriladigan chana soni (precondition: >=5 chana)
N_VISITS = 2           # API orqali bajariladigan vizit soni (spec: kamida 2)
PASSWORD = "1"  # yaratilgan agent paroli "1" (run_create_agent bilan bir xil, group_a uslubi)

# API — begin/end uchun statik koordinatalar (embedded kolleksiyadagi qiymatlar)
BEGIN_LATLNG = "41.311081,69.240562"
END_LATLNG = "41.312500,69.241800"
EXPORT_URL = f"{BASE_URL}/sb/external:export"
IMPORT_URL = f"{BASE_URL}/sb/external:import"


# ══════════════════════════════════════════════════════════════════════════════
# 2-QADAM — haftalik reja + 5 chana (UI)
# ══════════════════════════════════════════════════════════════════════════════
def create_weekly_plan_5_points(page: Page, agent: str) -> str:
    """Agentга "Каждую неделю" (BUGUNGI hafta kuni) reja yaratib, ``N_POINTS`` ta
    chanani biriktiradi va saqlaydi. Agentning user_id (Планы URL'idan) ni
    qaytaradi — 3-qadam API vizitlari uchun kerak (MCP tasdiqlangan 2026-08-03).

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
# 3-QADAM — API orqali vizit (requests; auth = yangi agent)
# ══════════════════════════════════════════════════════════════════════════════
def _api_post(url: str, payload, headers: dict):
    """POST + JSON; HTTP 200 va "tape" status 'S' ni tekshiradi.
    Export (exp_*) javobi LIST (har item status), import (imp_*) javobi DICT (status)."""
    resp = requests.post(url, json=payload, headers=headers, timeout=60)
    assert resp.status_code == 200, f"{url} → HTTP {resp.status_code}: {resp.text[:300]}"
    body = resp.json()
    items = body if isinstance(body, list) else [body]
    for it in items:
        assert it.get("status") == "S", f"{url} → status!=S: {it.get('error_text') or it}"
    return body


def _leads(legal_form_id):
    """imp_temporary_visit_save / imp_visit_end uchun "leads" bloki
    (embedded kolleksiyadagi Avtotest Dokon qiymatlari)."""
    return {
        "legal_form_id": legal_form_id,
        "name": "Avtotest Dokon", "short_name": "AvtoDkn",
        "latlng": BEGIN_LATLNG, "phone_number": "+998901112233",
        "address": "Toshkent sh., Shayxontohur t.", "area": "50",
        "regions": [], "lob_product_groups": [], "category_product_groups": [],
    }


def run_api_visits(page: Page, agent: str, user_id: str, count: int = N_VISITS) -> list:
    """Yangi agent sifatida cookie olib (auth ALMASHTIRILGAN), bugungi rejadagi
    birinchi ``count`` ta chana uchun vizitni API orqali bajaradi:
    exp_client_list → (har chana: imp_visit_begin → imp_temporary_visit_save →
    imp_visit_end). Bajarilgan visit_id'lar ro'yxatini qaytaradi.

    Endpoint/payloadlar test_Plan_visit_recurrence.py EMBEDDED kolleksiyasidan;
    faqat auth yangi agentга, newman→requests, 1→count vizit o'zgargan."""
    agent_login = f"{agent}@{COMPANY_CODE}"

    with allure.step(f"API auth: '{agent_login}' sifatida login → JSESSIONID cookie"):
        ctx = page.context.browser.new_context()
        try:
            cookie = cookie_from_context(ctx, agent_login, PASSWORD)
        finally:
            ctx.close()
        assert "JSESSIONID" in cookie, f"session cookie olinmadi: {cookie[:80]}"
    headers = {"Cookie": cookie, "Content-Type": "application/json"}

    with allure.step("API: c:exp_client_list — bugungi rejadagi chanalar"):
        body = _api_post(EXPORT_URL, [{
            "code": "c:exp_client_list",
            "filter": {"search_value": "", "region_ids": [], "lob_group_ids": [],
                       "sort_by": "A", "row_start": 1, "rows_count": 50},
        }], headers)
        data = body[0]["data"]
        clients = data.get("clients") or []
        step_ids = [int(s["step_id"]) for s in (data.get("visit_steps") or [])]
        assert len(clients) >= count, (
            f"kamida {count} chana kutilgan edi, rejada {len(clients)} ta topildi"
        )

    visit_ids = []
    for i, c in enumerate(clients[:count], start=1):
        person_id = int(c["person_id"])   # server STRING qaytaradi — numericга o'giriladi
        legal_form_id = (c.get("legal_form") or {}).get("form_id")
        leads = _leads(legal_form_id)

        with allure.step(f"API vizit {i}/{count}: begin (person_id={person_id})"):
            begin = _api_post(IMPORT_URL, {"code": "c:imp_visit_begin", "data": {
                "person_id": person_id, "user_id": int(user_id), "begin_latlng": BEGIN_LATLNG,
            }}, headers)
            visit_id = begin["data"]["visit_id"]

        with allure.step(f"API vizit {i}/{count}: temporary_visit_save (visit_id={visit_id})"):
            _api_post(IMPORT_URL, {"code": "c:imp_temporary_visit_save", "data": {
                "person_id": person_id, "user_id": int(user_id), "visit_id": visit_id,
                "data": {"leads": leads, "fields": [], "photos": [],
                         "visit_audios": [], "quiz_results": []},
            }}, headers)

        with allure.step(f"API vizit {i}/{count}: end (yakunlash)"):
            _api_post(IMPORT_URL, {"code": "c:imp_visit_end", "data": {
                "person_id": person_id, "visit_id": visit_id, "end_latlng": END_LATLNG,
                "data": {"reason_id": None, "leads": leads, "fields": [], "photos": [],
                         # step_ids exp_client_list'dagi GLOBAL visit_steps ro'yxati —
                         # prod'da ba'zi step_id'lar (masalan 41) sbmv_steps FK'ida yo'q
                         # (ORA-20999 parent key not found, company 101). Vizit yakunlash
                         # uchun step MAJBURIY emas — bo'sh yuboramiz (visit C ga yetadi).
                         "visit_photos": [], "visit_audios": [], "step_ids": [],
                         "quiz_results": []},
            }}, headers)
            visit_ids.append(str(visit_id))

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
    o'ng paneldagi "Визиты (N)" bajarilgan vizitlar soniga teng ekani tekshiriladi
    (N=expected_visits). Xarita markerlari best-effort qayd etiladi (MCP 2026-08-03)."""
    m = BasePage(page)

    with allure.step("Модератор → Отслеживание пользователей"):
        flow_navigate(page, tab="Модератор", name="Отслеживание пользователей")
        page.wait_for_url(lambda u: "user_locations" in u, timeout=30_000)
        m._settle()

    with allure.step("Sana avtomatik bugungi kunga o'rnatilganini tekshirish"):
        today_str = date.today().strftime("%d.%m.%Y")
        expect(page.get_by_role("textbox", name="Выберите дату")).to_have_value(today_str)

    with allure.step(f"Агентlar ro'yxatidan '{agent}' ni tanlash"):
        box = page.get_by_role("textbox", name="Выберите...")
        box.click()
        box.fill(agent)
        page.locator(".cdk-overlay-container li").filter(has_text=agent).first.click()
        m._settle()

    with allure.step(f"Xaritada '{expected_visits}' ta vizit ('Визиты ({expected_visits})')"):
        # ISHONCHLI: "Визиты (N)" REJANI emas, bajarilgan VIZITNI sanaydi
        # "Визиты (N)" tab ham ikki DOM elementга mos (smt-tab-button + ichki button) — .first
        expect(page.get_by_role("button", name=f"Визиты ({expected_visits})").first).to_be_visible(timeout=30_000)
        markers = _count_map_markers(page)
        allure.attach(f"leaflet markerlari (best-effort, yashil-faqat emas): {markers}",
                      name="map_markers", attachment_type=allure.attachment_type.TEXT)


# ══════════════════════════════════════════════════════════════════════════════
# TEST — to'liq E2E zanjir
# ══════════════════════════════════════════════════════════════════════════════
@allure.epic("Документы")
@allure.feature("Отслеживание пользователей")
@allure.story("E2E: агент → план → API визит → трекинг")
@allure.title("Агент yaratish → 5 chanali reja → API orqali 2 vizit → трекинг (2 vizit)")
def test_agent_visit_tracking(page: Page) -> None:
    with allure.step("Tizimga kirish (admin)"):
        authorization(page)

    with allure.step("1-qadam: rol=Агент yangi Пользователь yaratish"):
        agent = run_create_agent(page)

    with allure.step(f"2-qadam: '{WEEKLY_SECTION}' reja + {N_POINTS} chana"):
        user_id = create_weekly_plan_5_points(page, agent)

    with allure.step(f"3-qadam: API orqali {N_VISITS} ta vizit (requests, auth=agent)"):
        visit_ids = run_api_visits(page, agent, user_id, count=N_VISITS)
        assert len(visit_ids) == N_VISITS, f"{N_VISITS} vizit kutilgan, olindi {visit_ids}"

    with allure.step(f"4-qadam: Отслеживание — bajarilgan vizitlar soni ({len(visit_ids)}) ko'rinishi"):
        # DINAMIK: nechta vizit HAQIQATDA bajarilgan bo'lsa (len(visit_ids)), xaritada
        # shuncha ko'rinishi tekshiriladi — 5 bajarilsa 5, 3 bajarilsa 3, 2 bajarilsa 2.
        verify_tracking(page, agent, expected_visits=len(visit_ids))

    with allure.step(f"Tozalash: '{agent}' agentini Неактивный qilish"):
        # Vizitли agentni O'CHIRIB bo'lmaydi (child record) — Неактивный qilinadi
        # (loyiha uslubi, test_Plan_visit_recurrence bilan bir xil).
        _deactivate_agent(page, BasePage(page), agent)
