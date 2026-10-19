"""S-05 Склады — ombor endpointlari uchun kichik ``requests`` klienti (bitta user sessiyasi).

Kashfiyot (DEV, 2026-10-18): hammasi POST JSON, faqat Content-Type + sessiya cookie
(kontekst headerlari shart emas; cookie'siz → 401). Login ``biruni/s$log_in``.
Xato — HTTP 500 text/plain (masalan «Z:#z:sbr_supplier_warehouses null value name»).
``:model`` javobi massiv ``["(^_^)", meta, data, []]`` — data = [2].

``post()`` statusni TEKSHIRMAYDI (negativ testlar javobni o'zi tekshiradi); qolgan
yordamchilar «happy» yo'l — HTTP 200 ni assert qiladi. Har so'rov/javob Allure'ga
biriktiriladi (dalil).
"""
import json

import allure
import requests

from utils.base_api import BASE_URL

W = "/sb/sbr/supplier"
LIST_COLUMNS = ["name", "code", "region_names", "count_child", "warehouse_id", "pcode"]
BIND_COLUMNS = ["barcode", "name", "status", "status_name", "avail", "avail_name", "product_id"]
DEFAULT_PCODE = "SB:1"   # «Склад по умолчанию»


class WarehouseApi:
    def __init__(self, login, password="1"):
        self.login_name = login
        self.s = requests.Session()
        r = self.post("/biruni/s$log_in", {"login": login, "password": password})
        assert r.status_code == 200 and r.json().get("status") == "logged_in", \
            f"API login {login}: HTTP {r.status_code} {r.text[:200]}"

    def logout(self) -> None:
        self.s.post(f"{BASE_URL}/biruni/m$logout", json={}, timeout=60)
        self.s.close()

    # ── past daraja ───────────────────────────────────────────────────────────────────
    def post(self, path, body) -> requests.Response:
        r = self.s.post(f"{BASE_URL}{path}", json=body, timeout=60)
        shown = {**body, "password": "***"} if "password" in body else body
        allure.attach(
            f"[{self.login_name}] POST {path}\n{json.dumps(shown, ensure_ascii=False)}\n"
            f"→ HTTP {r.status_code}: {r.text[:1000]}",
            name=f"{path.rsplit('/', 1)[-1]} → {r.status_code}",
            attachment_type=allure.attachment_type.TEXT)
        return r

    def _ok(self, path, body) -> requests.Response:
        r = self.post(path, body)
        assert r.status_code == 200, f"{path} → HTTP {r.status_code}: {r.text[:300]}"
        return r

    # ── ombor ro'yxati / forma ──────────────────────────────────────────────────────
    def warehouses(self, name=None) -> list:
        """Joriy user ko'radigan omborlar (``name`` — aniq nom bo'yicha)."""
        body = {"p": {"column": LIST_COLUMNS, "filter": ["name", "esearch", f"%{name}%"] if name else [],
                      "sort": ["name"], "offset": 0, "limit": 50}, "d": {}}
        rows = [dict(zip(LIST_COLUMNS, row)) for row in self._ok(f"{W}/warehouse_list:table", body).json()["data"]]
        return [w for w in rows if w["name"] == name] if name else rows

    def warehouse_id(self, name) -> str:
        found = self.warehouses(name)
        assert len(found) == 1, f"«{name}» ombori {len(found)} ta topildi"
        return str(found[0]["warehouse_id"])

    def default_warehouse_id(self) -> str:
        found = [w for w in self.warehouses() if w["pcode"] == DEFAULT_PCODE]
        assert len(found) == 1, f"Standart ombor ({DEFAULT_PCODE}) {len(found)} ta topildi"
        return str(found[0]["warehouse_id"])

    def region_ids(self, *names) -> list:
        """``warehouse+add:model`` dagi faol regionlar ([id, name, parent_id]) — nom bo'yicha ID."""
        regions = self._ok(f"{W}/warehouse+add:model", {}).json()[2]["regions"]
        ids = []
        for name in names:
            match = [str(r[0]) for r in regions if r[1] == name]
            assert match, f"Region «{name}» add:model'da yo'q"
            ids.append(match[0])
        return ids

    def create(self, name, code, region_ids) -> str:
        """``warehouse+add$save`` (ID qaytmaydi) → ro'yxatdan nom bo'yicha ID."""
        self._ok(f"{W}/warehouse+add$save", {"code": code, "name": name, "region_id": list(region_ids)})
        return self.warehouse_id(name)

    def edit_model(self, warehouse_id) -> dict:
        return self._ok(f"{W}/warehouse+edit:model", {"warehouse_id": warehouse_id}).json()[2]

    def edit_save(self, model: dict, **changes) -> requests.Response:
        """``warehouse+edit$save`` — ``model`` (edit:model) maydonlari + ``changes``.
        Status tekshirilmaydi (negativ testlar uchun)."""
        body = {k: model[k] for k in ("warehouse_id", "supplier_id", "code", "name", "region_id")}
        body.update(changes)
        return self.post(f"{W}/warehouse+edit$save", body)

    def delete(self, *warehouse_ids) -> requests.Response:
        return self.post(f"{W}/warehouse_list$delete", {"warehouse_ids": list(warehouse_ids)})

    # ── ombor tovarlari ──────────────────────────────────────────────────────────────
    def products(self, warehouse_id, attached="Y", name=None) -> list:
        """``warehouse_product_bind_list:table`` — attached Y (Прикрепленные) / N (Доступные)."""
        body = {"p": {"column": BIND_COLUMNS, "filter": ["name", "esearch", f"%{name}%"] if name else [],
                      "sort": ["name"], "offset": 0, "limit": 50},
                "d": {"warehouse_id": warehouse_id, "attached": attached}}
        rows = self._ok(f"{W}/warehouse_product_bind_list:table", body).json()["data"]
        return [dict(zip(BIND_COLUMNS, row)) for row in rows if name is None or row[1] == name]

    def product_id(self, warehouse_id, name, attached="Y") -> str:
        found = self.products(warehouse_id, attached, name)
        assert len(found) == 1, f"«{name}» (attached={attached}) {len(found)} ta topildi"
        return str(found[0]["product_id"])

    def attach(self, warehouse_id, *product_ids) -> requests.Response:
        return self.post(f"{W}/warehouse_product_bind_list$attach",
                         {"warehouse_id": warehouse_id, "product_id": list(product_ids)})

    def detach(self, warehouse_id, *product_ids) -> requests.Response:
        return self.post(f"{W}/warehouse_product_bind_list$detach",
                         {"warehouse_id": warehouse_id, "product_id": list(product_ids)})
