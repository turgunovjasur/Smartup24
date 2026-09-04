"""Web↔Mobile Visit API klienti — Postman/newman EMAS, to'g'ridan-to'g'ri ``requests``.

``utils/base_page.py`` UI amallari uchun qanday umumiy qatlam bo'lsa, ``base_api.py``
MOBIL VISIT API so'rovlari uchun shunday: test fayllar NIMA tekshirishni aytadi,
endpoint/payload mexanikasi shu yerda turadi.

Ilgari bu mantiq IKKI joyda takrorlangan edi:
  - ``test_Plan_visit_recurrence.py`` da embedded Postman ``COLLECTION`` (newman yuritardi)
  - ``test_agent_visit_tracking.py`` da ``requests`` bilan qayta yozilgan begin/save/end
Payload o'zgarса ikkala fayl tuzatilishi kerak edi (bag manbai). Endi bitta manba —
faqat shu fayl.

Backend endpointlari: ``/sb/external:export`` (``exp_*`` — o'qish) va ``:import``
(``imp_*`` — yozish). Javob "tape" formatida: har element ``status == 'S'`` bo'lishi
shart, aks holda ``error_text`` bilan yiqiladi.
"""
from __future__ import annotations

import requests

from flows.flow_authorization import LOGIN_URL

# API backend URL va cookie domeni MUHITGA qarab LOGIN_URL'dan olinadi (prod/dev) —
# qattiq kodlanmaydi (aks holda agent PROD'da yaratilib login DEV'ga borib timeout
# berardi). BASE_URL: ".../a2/auth/login" -> ".../b" (dev'da "/x24" prefiks saqlanadi:
# app2.greenwhite.uz/x24/b; prod: app.smartup24.com/b). COOKIE_DOMAIN: login host'ining
# registrable domeni (oxirgi 2 label) — prod cookie'lari (smartup24.com) dev filtridan
# (greenwhite.uz) chiqib ketmasin.
BASE_URL = LOGIN_URL.replace("/a2/auth/login", "/b")
COOKIE_DOMAIN = ".".join(LOGIN_URL.split("//", 1)[1].split("/", 1)[0].split(".")[-2:])

# begin/end uchun statik koordinatalar (embedded kolleksiyadagi asl qiymatlar)
BEGIN_LATLNG = "41.311081,69.240562"
END_LATLNG = "41.312500,69.241800"


def _leads(legal_form_id, latlng: str) -> dict:
    """imp_temporary_visit_save / imp_visit_end uchun "leads" bloki (Avtotest Dokon)."""
    return {
        "legal_form_id": legal_form_id,
        "name": "Avtotest Dokon", "short_name": "AvtoDkn",
        "latlng": latlng, "phone_number": "+998901112233",
        "address": "Toshkent sh., Shayxontohur t.", "area": "50",
        "regions": [], "lob_product_groups": [], "category_product_groups": [],
    }


def login_cookie(context, login: str, password: str) -> str:
    """Berilgan Playwright ``context`` da foydalanuvchi sifatida login qilib
    "k=v; ..." cookie satrini qaytaradi (JSESSIONID HttpOnly bo'lsa ham).

    Context TASHQARIDAN beriladi — ishlab turgan sync Playwright ichida ham
    chaqirса bo'ladi (nested ``sync_playwright`` YO'Q). Agent (yoki boshqa user)
    cookie'sini olib API'ni O'SHA foydalanuvchi nomidan chaqirish uchun ishlatiladi."""
    p = context.new_page()
    # Default goto timeout 30s — dev-server sekin javob berganda login sahifasi
    # yuklanmay broken bo'lardi; navigatsiya timeout'i (60s) beriladi.
    p.goto(LOGIN_URL, timeout=60_000)
    p.get_by_role("textbox", name="Логин").fill(login)
    p.get_by_role("textbox", name="Введите пароль").fill(password)
    p.get_by_role("button", name="Войти").click()
    p.wait_for_url(lambda u: "/auth/login" not in u, timeout=60_000)
    p.wait_for_timeout(1_500)
    cookies = context.cookies()
    p.close()
    return "; ".join(f"{c['name']}={c['value']}" for c in cookies if COOKIE_DOMAIN in c["domain"])


class VisitApi:
    """Mobil visit API klienti — bitta agent cookie'si bilan.

    Namuna::

        cookie = login_cookie(ctx, f"{agent}@{COMPANY_CODE}", "1")
        api = VisitApi(cookie)
        clients, _ = api.client_list()                 # bugungi rejadagi chanalar
        c = clients[0]
        visit_id = api.run_visit(VisitApi.person_id(c), user_id,
                                 VisitApi.legal_form_id(c))   # begin→save→end
        data = api.client_info(VisitApi.person_id(c), user_id)
        assert data["visit_status"] == "C"             # yakunlangan
    """

    def __init__(self, cookie: str, base_url: str = BASE_URL):
        assert cookie and "JSESSIONID" in cookie, f"session cookie yo'q/noto'g'ri: {cookie[:80]!r}"
        self.export_url = f"{base_url}/sb/external:export"
        self.import_url = f"{base_url}/sb/external:import"
        self.headers = {"Cookie": cookie, "Content-Type": "application/json"}

    # -- past daraja: POST + "tape" status tekshiruvi ------------------------------------
    def _post(self, url: str, payload):
        """POST + JSON; HTTP 200 va har "tape" elementi ``status == 'S'`` ni tekshiradi.
        Export (``exp_*``) javobi LIST (har item status), import (``imp_*``) DICT (status)."""
        resp = requests.post(url, json=payload, headers=self.headers, timeout=60)
        assert resp.status_code == 200, f"{url} → HTTP {resp.status_code}: {resp.text[:300]}"
        body = resp.json()
        for it in (body if isinstance(body, list) else [body]):
            assert it.get("status") == "S", f"{url} → status!=S: {it.get('error_text') or it}"
        return body

    # -- chana dict'idan maydon ajratish (test dict shakliga tegmasin) -------------------
    @staticmethod
    def person_id(client) -> int:
        """Chana ``person_id`` (server STRING qaytaradi — numericga o'giriladi)."""
        return int(client["person_id"])

    @staticmethod
    def legal_form_id(client):
        """Chana ``legal_form.form_id`` (yo'q bo'lsa None)."""
        return (client.get("legal_form") or {}).get("form_id")

    # -- yuqori daraja API amallari ------------------------------------------------------
    def client_list(self, rows_count: int = 50):
        """Bugungi rejadagi chanalar (``c:exp_client_list``). ``(clients, step_ids)``
        qaytaradi — ``clients`` chana dict'lari, ``step_ids`` global visit_steps."""
        body = self._post(self.export_url, [{
            "code": "c:exp_client_list",
            "filter": {"search_value": "", "region_ids": [], "lob_group_ids": [],
                       "sort_by": "A", "row_start": 1, "rows_count": rows_count},
        }])
        data = body[0]["data"]
        clients = data.get("clients") or []
        step_ids = [int(s["step_id"]) for s in (data.get("visit_steps") or [])]
        return clients, step_ids

    def client_info(self, person_id, user_id) -> dict:
        """Chana bo'yicha joriy visit ma'lumoti (``c:exp_client_info``) — yakunlangan
        visitni tekshirish uchun (``data["visit_status"] == "C"``)."""
        body = self._post(self.export_url, [{
            "code": "c:exp_client_info",
            "filter": {"person_id": int(person_id), "user_id": int(user_id)},
        }])
        return body[0]["data"]

    def begin(self, person_id, user_id) -> str:
        """Visitni boshlaydi (``c:imp_visit_begin``) — yangi ``visit_id`` qaytaradi."""
        body = self._post(self.import_url, {"code": "c:imp_visit_begin", "data": {
            "person_id": int(person_id), "user_id": int(user_id), "begin_latlng": BEGIN_LATLNG,
        }})
        return body["data"]["visit_id"]

    def temporary_save(self, person_id, user_id, visit_id, legal_form_id=None) -> None:
        """Visit o'rtasida qoralama saqlash (``c:imp_temporary_visit_save``)."""
        self._post(self.import_url, {"code": "c:imp_temporary_visit_save", "data": {
            "person_id": int(person_id), "user_id": int(user_id), "visit_id": visit_id,
            "data": {"leads": _leads(legal_form_id, BEGIN_LATLNG), "fields": [], "photos": [],
                     "visit_audios": [], "quiz_results": []},
        }})

    def end(self, person_id, visit_id, legal_form_id=None) -> None:
        """Visitni yakunlaydi (``c:imp_visit_end``) — visit ``C`` holatiga o'tadi.

        ``step_ids`` BO'SH yuboriladi: exp_client_list'даги GLOBAL visit_steps
        step_id'lari prod'да sbmv_steps FK'ida bo'lmasligi mumkin (ORA-20999 parent
        key not found) — step visit yakunlash uchun MAJBURIY emas."""
        self._post(self.import_url, {"code": "c:imp_visit_end", "data": {
            "person_id": int(person_id), "visit_id": visit_id, "end_latlng": END_LATLNG,
            "data": {"reason_id": None, "leads": _leads(legal_form_id, END_LATLNG),
                     "fields": [], "photos": [], "visit_photos": [], "visit_audios": [],
                     "step_ids": [], "quiz_results": []},
        }})

    def run_visit(self, person_id, user_id, legal_form_id=None) -> str:
        """Bitta to'liq visit: begin → temporary_save → end. ``visit_id`` (str) qaytaradi."""
        visit_id = self.begin(person_id, user_id)
        self.temporary_save(person_id, user_id, visit_id, legal_form_id)
        self.end(person_id, visit_id, legal_form_id)
        return str(visit_id)
