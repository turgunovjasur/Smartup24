"""Mobil Visit API klienti (``requests``) — UI uchun ``base_page.py`` qanday bo'lsa,
mobil API uchun shunday: test NIMA tekshirishni aytadi, endpoint/payload shu yerda.

Endpointlar: ``/sb/external:export`` (``exp_*`` — o'qish) va ``:import`` (``imp_*`` —
yozish). Javobdagi har "tape" elementi ``status == 'S'`` bo'lishi shart.
"""
from __future__ import annotations

import time

import requests

from flows.flow_authorization import LOGIN_URL

# Muhitga (prod/dev) qarab LOGIN_URL'dan: ".../a2/auth/login" -> ".../b" (dev'da /x24
# prefiks saqlanadi). COOKIE_DOMAIN — login host'ining oxirgi 2 labeli.
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

    Context tashqaridan beriladi (nested ``sync_playwright`` yo'q) — API'ni o'sha
    foydalanuvchi (masalan agent) nomidan chaqirish uchun."""
    p = context.new_page()
    try:
        p.goto(LOGIN_URL, timeout=60_000)   # dev-server sekin — default 30s yetmaydi
        p.get_by_role("textbox", name="Логин").fill(login)
        p.get_by_role("textbox", name="Введите пароль").fill(password)
        p.get_by_role("button", name="Войти").click()
        p.wait_for_url(lambda u: "/auth/login" not in u, timeout=60_000)
        # Sessiya cookie'si redirect'dan keyin ham kechikib yozilishi mumkin — ko'r-ko'rona
        # 1.5s kutish o'rniga JSESSIONID paydo bo'lguncha (15s gacha) tekshiramiz.
        deadline = time.monotonic() + 15
        while True:
            cookies = [c for c in context.cookies() if COOKIE_DOMAIN in c["domain"]]
            if any(c["name"] == "JSESSIONID" for c in cookies) or time.monotonic() > deadline:
                break
            p.wait_for_timeout(300)
    finally:
        p.close()
    return "; ".join(f"{c['name']}={c['value']}" for c in cookies)


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
    @staticmethod
    def _code(payload) -> str:
        """So'rov kodi (``c:exp_client_list`` ...) — xato xabarida qaysi amal yiqilgani."""
        item = payload[0] if isinstance(payload, list) and payload else payload
        return item.get("code", "?") if isinstance(item, dict) else "?"

    def _post(self, url: str, payload):
        """POST + JSON; HTTP 200 va har "tape" elementi ``status == 'S'`` ni tekshiradi.
        Export (``exp_*``) javobi LIST (har item status), import (``imp_*``) DICT (status).

        Faqat O'QISH (export) so'rovlari tarmoq uzilishi / 502-504 da 3 martagacha
        qayta yuboriladi. Import (begin/save/end) qayta yuborilMAYDI — server
        allaqachon bajargan bo'lsa ikkinchi visit yaratilib qolardi."""
        code = self._code(payload)
        attempts = 3 if url == self.export_url else 1
        for attempt in range(1, attempts + 1):
            try:
                resp = requests.post(url, json=payload, headers=self.headers, timeout=60)
            except (requests.ConnectionError, requests.Timeout) as exc:
                if attempt == attempts:
                    raise AssertionError(f"API {code}: server javob bermadi ({type(exc).__name__})") from None
                time.sleep(2 * attempt)
                continue
            if resp.status_code in (502, 503, 504) and attempt < attempts:
                time.sleep(2 * attempt)
                continue
            break
        assert resp.status_code == 200, f"API {code} → HTTP {resp.status_code}: {resp.text[:300]}"
        try:
            body = resp.json()
        except ValueError:
            # Sessiya tugagan bo'lsa server JSON o'rniga login/xato HTML sahifasini qaytaradi
            raise AssertionError(
                f"API {code}: JSON emas javob keldi (sessiya tugaganmi?): {resp.text[:200]!r}"
            ) from None
        for it in (body if isinstance(body, list) else [body]):
            assert it.get("status") == "S", f"API {code} → status!=S: {it.get('error_text') or it}"
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

        ``step_ids`` BO'SH yuboriladi: exp_client_list'dagi GLOBAL visit_steps
        step_id'lari prod'da sbmv_steps FK'ida bo'lmasligi mumkin (ORA-20999 parent
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
