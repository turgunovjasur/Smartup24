"""S-05 seed'larini API orqali yaratish (``S05_SEED_MODE=api`` default; ``ui`` — eski web UI yo'li).

Endpointlar DEV'da UI so'rovini ushlab tasdiqlangan (MCP + run_* probe, 2026-10-20), so'ng
``requests`` bilan kontekst kalitlarisiz (``-project_code``/``-filial_id`` shart emas) qayta
tasdiqlangan. Admin formalari ``/sb/sbr/moderator/...`` (``MODERATOR_PATH``):
  region+add$save {code, name, state, [parent_region_id]} → {region_id}
  person/legal_form+add$save {name, short_name, side:"R", state} → {legal_form_id}
  product/product_group+add$save {parent_group_id, name, order_no, state, photos} → bo'sh
      (guruh: Отрасль pcode SB:3, Категория SB:1 — ``product_group_list:table`` d.parent_group_id=null)
  product/producer+add$save {name, order_no, state} → bo'sh   (producer = Производитель/Manufacturer)
  product/product+add$save (UI tanasi bilan bir xil) → {product_id}; ``+edit:model`` UI yaratgan
      tovar bilan solishtirildi — farq faqat nom/ID'larda.
  person/person+add$save (UI tanasi: is_supplier/is_client, region_id[], lob_product_group_id[],
      client_person_groups add:model'dan) → {person_id}; ``person+edit:model`` UI yaratgan
      supplier/client bilan solishtirildi — farq faqat nom/ID/tin/sanada.
  Server kalitlarida ``lob`` = Отрасль (line of business): ``lob_id``, ``lob_product_group_id`` —
  Python kodida ``industry``/``industry_id`` deb ataladi, so'rov kalitlari o'zgarmaydi.
Admin sessiyasida supplier/client formalari (kontekst supplier_id / client_id bilan):
  /sb/sbr/supplier/user+add$save (rol ``user+add:roles``), /sb/sbr/client/user+add$save
      (rol + savdo nuqtasi ``user+add:outlets``) — bo'sh javob; parol "1"
  /sb/sbr/supplier/client/client_list$send_request {supplier_id, client_id} →
      /sb/sbr/client/supplier/request_list:supplier_requests (status N) → $approve {request_id}
  supplier_product_bind_list$save {supplier_id, product_id[]} → /sb/sbr/supplier/product_list$change_avail
      (Y — shundan keyin «Склад по умолчанию»ga tushadi) → /sb/sbr/supplier/set_product_price$save
      {price_type_id («Цена по умолчанию», pcode SB:1), product_id[], price[]}
Bo'sh javobli save'lardan keyin ID ``:table`` dan aniq nom bo'yicha olinadi. API'da har qism qayta
o'qib tasdiqlanadi: «Склад по умолчанию» avtomatik paydo bo'lgani + supplier/client user
``s$log_in`` (WarehouseApi), hamkorlik «Мои клиенты»da, narx ``set_product_price:model``da.
Ombor/biriktirish/«В наличие» — ``WarehouseApi`` (supplier user sessiyasi).
"""
import os
import random

import allure
from playwright.sync_api import Page

from flows.flow_authorization import COMPANY_CODE, TEST_PASSWORD
from tests.sbr.supplier.warehouse.warehouse_api import WarehouseApi
from tests.sbr.supplier.warehouse.warehouse_helpers import (
    attach_product, create_child_region, create_clients, create_warehouse, detach_product, toggle_in_stock,
)
from tests.test_group_a.test_product import run_product
from tests.test_group_a.test_product_linking import run_product_linking
from tests.test_group_a.test_supplier import run_supplier
from tests.test_group_a.test_supplier_user import run_supplier_user
from tests.test_setup.test_manufacturer import run_manufacturer
from tests.test_setup.test_region import run_region
from tests.test_setup.test_supplier import ensure_refs

SEED_MODE_ENV = "S05_SEED_MODE"
MODERATOR_PATH = "/sb/sbr/moderator"
# Xarakteristika guruhlari pcode'i (product_group_list ildizlari, moderator):
INDUSTRY_GROUP_PCODE = "SB:3"   # «Отрасль» guruhi (serverda lob)
CATEGORY_GROUP_PCODE = "SB:1"   # «Категория» guruhi
# Supplier narx turlari pcode'i (price_type_list, har supplier o'ziniki) — BOSHQA domen: qiymati
# CATEGORY_GROUP_PCODE bilan tasodifan bir xil ("SB:1"), lekin bir-biriga aloqasi yo'q.
DEFAULT_PRICE_TYPE_PCODE = "SB:1"   # «Цена по умолчанию»


def seed_mode() -> str:
    """Joriy seed rejimi: ``api`` (default) yoki ``ui`` (``S05_SEED_MODE``)."""
    mode = (os.getenv(SEED_MODE_ENV) or "api").strip().lower()
    assert mode in ("api", "ui"), f"{SEED_MODE_ENV}={mode!r} — faqat api|ui"
    return mode


class AdminSeedApi(WarehouseApi):
    """Admin sessiyasi (login/post/_ok/Allure biriktirish — ``WarehouseApi`` dan)."""

    def __init__(self):
        super().__init__(f"admin@{COMPANY_CODE}", TEST_PASSWORD)

    # ── ichki o'qish yordamchilari ──────────────────────────────────────────────────────
    def _read_table(self, path, columns, filters=None, params=None) -> list:
        body = {"p": {"column": columns, "filter": filters or [], "sort": [], "offset": 0, "limit": 50},
                "d": params or {}}
        return [dict(zip(columns, row)) for row in self._ok(path, body).json()["data"]]

    def _id_by_name(self, path, id_column, name, params=None) -> str:
        found = self._read_table(path, ["name", id_column], ["name", "=", name], params)
        assert len(found) == 1, f"{path}: «{name}» {len(found)} ta topildi"
        return str(found[0][id_column])

    def _group_root_id(self, pcode) -> str:
        roots = self._read_table(f"{MODERATOR_PATH}/product/product_group_list:table",
                                 ["name", "product_group_id", "pcode"], params={"parent_group_id": None})
        found = [group for group in roots if group["pcode"] == pcode]
        assert len(found) == 1, f"Xarakteristika guruhi {pcode}: {len(found)} ta"
        return str(found[0]["product_group_id"])

    # ── 1-qism: ma'lumotnomalar va tovar ─────────────────────────────────────────────────
    def create_region(self, name, parent_id=None) -> str:
        """Region yaratadi (``parent_id`` berilsa — bola region); ro'yxatdan tasdiqlab region_id qaytaradi."""
        body = {"code": str(random.randint(10**8, 10**9 - 1)), "name": name, "state": "A"}
        if parent_id:
            body["parent_region_id"] = parent_id
        region_id = str(self._ok(f"{MODERATOR_PATH}/region+add$save", body).json()["region_id"])
        listed = self._id_by_name(f"{MODERATOR_PATH}/region_list:table", "region_id", name,
                                  {"parent_region_id": parent_id} if parent_id else None)
        assert listed == region_id, f"Region «{name}»: save {region_id}, ro'yxatda {listed}"
        return region_id

    def region_id(self, name) -> str:
        """YUQORI darajali region ID'si nom bo'yicha (bola region bu ro'yxatda yo'q)."""
        return self._id_by_name(f"{MODERATOR_PATH}/region_list:table", "region_id", name)

    def create_legal_form(self, name) -> str:
        """Форма собственности (Организационно-правовая форма) yaratadi; legal_form_id qaytaradi."""
        response = self._ok(f"{MODERATOR_PATH}/person/legal_form+add$save",
                            {"name": name, "short_name": name, "side": "R", "state": "A"})
        return str(response.json()["legal_form_id"])

    def legal_form_id(self, name) -> str:
        """Форма собственности ID'si nom bo'yicha."""
        return self._id_by_name(f"{MODERATOR_PATH}/person/legal_form_list:table", "legal_form_id", name)

    def create_product_group(self, group_pcode, name) -> str:
        """Xarakteristika podtipi (Отрасль/Категория, ``group_pcode`` guruhida) yaratadi; ID qaytaradi."""
        parent_id = self._group_root_id(group_pcode)
        self._ok(f"{MODERATOR_PATH}/product/product_group+add$save",
                 {"parent_group_id": parent_id, "name": name, "order_no": None, "state": "A", "photos": []})
        return self._id_by_name(f"{MODERATOR_PATH}/product/product_group_list:table", "product_group_id", name,
                                {"parent_group_id": parent_id})

    def product_group_id(self, group_pcode, name) -> str:
        """Xarakteristika podtipi ID'si (``group_pcode`` guruhida) nom bo'yicha."""
        return self._id_by_name(f"{MODERATOR_PATH}/product/product_group_list:table", "product_group_id", name,
                                {"parent_group_id": self._group_root_id(group_pcode)})

    def create_manufacturer(self, name) -> str:
        """Производитель (serverda producer) yaratadi; producer_id qaytaradi."""
        self._ok(f"{MODERATOR_PATH}/product/producer+add$save", {"name": name, "order_no": None, "state": "A"})
        return self.manufacturer_id(name)

    def manufacturer_id(self, name) -> str:
        """Производитель (producer) ID'si nom bo'yicha."""
        return self._id_by_name(f"{MODERATOR_PATH}/product/producer_list:table", "producer_id", name)

    def measure_id(self, short_name="кг") -> str:
        """O'lchov birligi ID'si qisqa nom bo'yicha (default «кг»)."""
        found = self._read_table(f"{MODERATOR_PATH}/product/measure_list:table", ["short_name", "measure_id"],
                                 ["short_name", "=", short_name])
        assert len(found) == 1, f"O'lchov birligi «{short_name}» {len(found)} ta"
        return str(found[0]["measure_id"])

    def create_product(self, name, manufacturer_id, industry_id, category_id, measure_id) -> str:
        """Tovar yaratadi (``product+add$save`` — UI tanasi, tavsif turlari add:model'dan); product_id qaytaradi."""
        description_type_ids = [description[0] for description in
                                self._ok(f"{MODERATOR_PATH}/product/product+add:model", {}).json()[2]["descriptions"]]
        body = {"product_id": None, "code": None, "name": name, "short_name": name, "producer_id": manufacturer_id,
                "produced_region_id": None, "status": "A", "measure_id": measure_id, "box_type_id": None,
                "box_quant": None, "article_code": None, "barcode": None, "icps": None, "gtin": None,
                "weight_netto": None, "weight_brutto": None, "litr": None, "category_id": category_id,
                "brand_id": None, "lob_id": industry_id, "similar_product_id": [],
                "description_type_ids": description_type_ids,
                "description_type_texts": [None] * len(description_type_ids), "videos": [],
                "translates": [{"values": {}, "column_name": "NAME"}, {"values": {}, "column_name": "SHORT_NAME"}]
                + [{"values": {}, "description_type_id": type_id} for type_id in description_type_ids],
                "photos": []}
        product_id = str(self._ok(f"{MODERATOR_PATH}/product/product+add$save", body).json()["product_id"])
        # Jim e'tiborsiz qolgan maydon seed bosqichida aniq xato bersin
        saved = self._ok(f"{MODERATOR_PATH}/product/product+edit:model", {"product_id": product_id}).json()[2]["data"]
        expected = {"producer_id": manufacturer_id, "lob_id": industry_id, "category_id": category_id,
                    "measure_id": measure_id}
        actual = {key: str(saved.get(key)) for key in expected}
        assert actual == {key: str(value) for key, value in expected.items()}, \
            f"Tovar «{name}» ({product_id}) saqlangan maydonlari {actual}, kutilgan {expected}"
        return product_id

    # ── 2-qism: Юр. лицо, userlar, hamkorlik, tovar biriktirish + narx ───────────────────
    def create_legal_person(self, name, *, supplier, legal_form_id, industry_id, regions) -> str:
        """Юр. лицо (supplier=True — Поставщик, aks holda Клиент) yaratadi; person_id qaytaradi.

        UI tanasi: client_person_groups add:model'dagi barcha guruhlar bo'sh tur bilan, detail null'lar;
        supplier'da translates ham. ``regions`` — nomlar; ID add:model ``regions`` ([id, nom, ota]) dan —
        UI daraxti manbai, BARCHA darajalar (``region_list:table`` faqat yuqori darajani beradi)."""
        model = self._ok(f"{MODERATOR_PATH}/person/person+add:model", {}).json()[2]
        region_ids = []
        for region in regions:
            found = [str(item[0]) for item in model["regions"] if item[1] == region]
            assert len(found) == 1, f"Region «{region}» person+add:model'da {len(found)} ta"
            region_ids.append(found[0])
        detail_keys = (
            "outlet_category outlet_status pos_kind pos_kind_other has_pos has_terminal is_network is_round_clock "
            "network_name signboard_name street_name house_number contact_name contact_position "
            "contact_position_other freezer_count fridge_count order_phone work_time work_days agent_note latlng "
            "phone_number address note legal_name legal_short_name legal_phone legal_email legal_address "
            "legal_status director oked okpo opf soato soogu registration_date reregistration_date "
            "registering_authority registration_number vat_certificate_number vat_payer_number "
            "vat_certificate_status enterprise_category ownership_type tax_regime taxpayer_type "
            "authorized_capital is_doubtful termination_data working_hours area").split()
        body = {"name": name, "short_name": name, "tin": str(random.randint(100000000, 999999999)),
                "legal_form_id": legal_form_id, "status": "A", "is_supplier": "Y" if supplier else "N",
                "is_client": "N" if supplier else "Y", "is_outlet": "N", "lob_product_group_id": [industry_id],
                "category_product_group_id": [], "supplier_background_color": None,
                "client_person_groups": [{"person_group_id": group[0], "person_type_id": []}
                                         for group in model.get("client_person_groups") or []],
                "operator_status": None, "operator_notes": None, "detail": dict.fromkeys(detail_keys),
                "region_id": region_ids, "accounts": []}
        if supplier:
            body["translates"] = [{"values": {}, "column_name": item["column_name"]} for item in model["translates"]]
        body["photos"] = []
        person_id = str(self._ok(f"{MODERATOR_PATH}/person/person+add$save", body).json()["person_id"])
        # Jim e'tiborsiz qolgan maydon seed bosqichida aniq xato bersin (regionlar, Отрасль)
        saved = self._ok(f"{MODERATOR_PATH}/person/person+edit:model", {"person_id": person_id}).json()[2]
        saved_regions = sorted(map(str, saved.get("region_id") or []))
        saved_industries = sorted(str(group[0]) for group in saved.get("lob_product_groups") or [])
        assert saved_regions == sorted(region_ids), \
            f"«{name}» ({person_id}) regionlari {saved_regions}, kutilgan {sorted(region_ids)} ({list(regions)})"
        assert saved_industries == [str(industry_id)], \
            f"«{name}» ({person_id}) Отрасль {saved_industries}, kutilgan [{industry_id}]"
        return person_id

    def supplier_id(self, name) -> str:
        """Supplier (Поставщик) person_id'si nom bo'yicha."""
        return self._id_by_name(f"{MODERATOR_PATH}/supplier/supplier_list:table", "person_id", name)

    def _role_id(self, form_path, context, role) -> str:
        body = {"p": {"column": ["name", "role_id"], "filter": ["name", "=", role], "sort": [], "offset": 0,
                      "limit": 10}, "d": context}
        found = [str(row[1]) for row in self._ok(f"{form_path}:roles", body).json()["data"] if row[0] == role]
        assert len(found) == 1, f"Rol «{role}» {len(found)} ta"
        return found[0]

    @staticmethod
    def _random_phone() -> str:
        return f"99899{random.randint(1000000, 9999999)}"

    def create_supplier_user(self, supplier_id, supplier_name, login, role="Админ (Поставщик)") -> None:
        """Supplier foydalanuvchisini yaratadi (``sbr/supplier/user+add$save``, rol ``role``, parol "1")."""
        form_path = "/sb/sbr/supplier/user+add"
        context = {"person_id": supplier_id, "person_name": supplier_name, "supplier_id": supplier_id,
                   "supplier_name": supplier_name}
        self._ok(f"{form_path}$save", {
            **context, "name": login, "state": "A", "gender": "M", "photo_sha": None, "position_name": None,
            "phone_number": self._random_phone(), "email": None, "timezone_code": None, "lang_code": "ru",
            "role_id": [self._role_id(form_path, {"supplier_id": supplier_id}, role)],
            "login": login, "password": "1"})

    def create_client_user(self, client_id, client_name, login, role="Админ (Клиент)") -> None:
        """Klient foydalanuvchisini yaratadi (rol + klientning o'z savdo nuqtasi ``:outlets``, parol "1")."""
        form_path = "/sb/sbr/client/user+add"
        outlets = self._ok(f"{form_path}:outlets", {"p": {"column": ["name", "outlet_id"], "filter": [], "sort": [],
                                                          "offset": 0, "limit": 10}, "d": {"person_id": client_id}})
        outlet_ids = [str(outlet[1]) for outlet in outlets.json()["data"] if outlet[0] == client_name]
        assert len(outlet_ids) == 1, f"{client_name}: savdo nuqtasi {len(outlet_ids)} ta"
        self._ok(f"{form_path}$save", {
            "person_id": client_id, "client_id": client_id, "person_name": client_name, "name": login,
            "state": "A", "gender": "M", "photo_sha": None, "position_name": None,
            "phone_number": self._random_phone(), "email": None, "timezone_code": None, "lang_code": "ru",
            "outlet_id": outlet_ids, "role_id": [self._role_id(form_path, {"person_id": client_id}, role)],
            "banned_notification_groups": [], "login": login, "password": "1"})

    def _supplier_requests(self, client_id, status="N") -> list:
        columns = ["supplier_name", "status", "request_id", "supplier_id"]
        body = {"p": {"column": columns, "filter": ["status", "=", status], "sort": [], "offset": 0, "limit": 50},
                "d": {"client_id": client_id, "initiator": "S"}}
        rows = self._ok("/sb/sbr/client/supplier/request_list:supplier_requests", body).json()["data"]
        return [dict(zip(columns, row)) for row in rows]

    def supplier_clients(self, supplier_id) -> list:
        """Supplier'ning «Мои клиенты» ro'yxatidagi client_id'lar."""
        body = {"p": {"column": ["name", "client_id", "status"], "filter": [], "sort": [], "offset": 0, "limit": 50},
                "d": {"supplier_id": supplier_id}}
        return [str(row[1]) for row in
                self._ok("/sb/sbr/supplier/client/client_list:supplier_clients", body).json()["data"]]

    def create_cooperation(self, supplier_id, supplier_name, client_id) -> None:
        """Hamkorlik: supplier so'rovi (``$send_request``) → klient tasdig'i (``request_list$approve``);
        natija «Мои клиенты» ro'yxatidan o'qib tasdiqlanadi."""
        self._ok("/sb/sbr/supplier/client/client_list$send_request",
                 {"person_id": supplier_id, "person_name": supplier_name, "supplier_id": supplier_id,
                  "client_id": client_id})

        def _pending() -> list:
            return [request for request in self._supplier_requests(client_id)
                    if str(request["supplier_id"]) == str(supplier_id)]

        pending = _pending()
        assert len(pending) == 1, f"Klient {client_id}: supplier {supplier_id} so'rovi {len(pending)} ta"
        self._ok("/sb/sbr/client/supplier/request_list$approve",
                 {"person_id": client_id, "request_id": str(pending[0]["request_id"])})
        assert not _pending(), f"Klient {client_id}: so'rov hali «Новый»"
        assert str(client_id) in self.supplier_clients(supplier_id), \
            f"Hamkorlik tasdiqlanmadi: {client_id} supplier {supplier_id} mijozlarida yo'q"

    @staticmethod
    def _supplier_context(supplier_id, supplier_name) -> dict:
        return {"person_id": supplier_id, "person_name": supplier_name, "supplier_id": supplier_id}

    def link_product_to_supplier(self, supplier_id, supplier_name, product_id, price="100000") -> None:
        """Tovarni supplier'ga biriktiradi, «В наличие» qiladi va «Цена по умолчанию» narxini qo'yadi
        (run_product_linking ekvivalenti). ``change_avail`` Y dan keyin tovar «Склад по умолчанию»ga
        tushadi. Har qadam qayta o'qib tasdiqlanadi."""
        context = self._supplier_context(supplier_id, supplier_name)
        self._ok(f"{MODERATOR_PATH}/supplier/supplier_product_bind_list$save", {**context, "product_id": [product_id]})
        self._ok("/sb/sbr/supplier/product_list$change_avail", {**context, "avail": "Y", "product_id": product_id})
        columns = ["name", "warehouse_names", "avail", "product_id"]
        rows = self._ok("/sb/sbr/supplier/product_list:table",
                        {"p": {"column": columns, "filter": [], "sort": [], "offset": 0, "limit": 500},
                         "d": {"supplier_id": supplier_id}}).json()["data"]
        linked = [dict(zip(columns, row)) for row in rows if str(row[3]) == str(product_id)]
        assert len(linked) == 1 and linked[0]["avail"] == "Y", f"Tovar {product_id} supplier'da: {linked}"
        price_types = self._ok("/sb/sbr/supplier/price_type_list:table",
                               {"p": {"column": ["name", "pcode", "price_type_id"], "filter": ["state", "=", "A"],
                                      "sort": [], "offset": 0, "limit": 50},
                                "d": {"supplier_id": supplier_id}}).json()["data"]
        default_ids = [str(row[2]) for row in price_types if row[1] == DEFAULT_PRICE_TYPE_PCODE]
        assert len(default_ids) == 1, f"«Цена по умолчанию» ({DEFAULT_PRICE_TYPE_PCODE}) {len(default_ids)} ta: {price_types}"
        self._ok("/sb/sbr/supplier/set_product_price$save",
                 {**context, "price_type_id": default_ids[0], "product_id": [product_id], "price": [price]})
        prices = self._ok("/sb/sbr/supplier/set_product_price:model",
                          {**context, "price_type_id": default_ids[0]}).json()[2]["products"]
        saved = [row[3] for row in prices if str(row[0]) == str(product_id)]   # [id, nom, ?, narx]
        assert saved and float(saved[0] or 0) == float(price), f"Tovar {product_id} narxi {saved}, kutilgan {price}"


def _assert_can_login(login) -> WarehouseApi:
    """User ``s$log_in`` bilan kira oladimi (rol/filial) — WarehouseApi konstruktori assert qiladi."""
    return WarehouseApi(f"{login}@{COMPANY_CODE}")


# ── seed qadamlari: api | ui ─────────────────────────────────────────────────────────
def seed_reference_data(page: Page, code, regions=(), children=()) -> None:
    """Region/MCHJ/Industry/Category/Manufacturer-{code} + ``regions`` (run_region kodi: X → Region-X)
    + ``children`` ((ota nomi, bola nomi), ...). UI rejimida ``page`` admin sifatida kirgan bo'lishi shart."""
    mode = seed_mode()
    with allure.step(f"Seed refs ({mode}): Region/MCHJ/Industry/Category/Manufacturer-{code}, "
                     f"regionlar {list(regions)}, bola {list(children)}"):
        if mode == "ui":
            ensure_refs(page, code)
            run_manufacturer(page, code)
            for region_code in regions:
                run_region(page, region_code)
            for parent, child in children:
                create_child_region(page, parent, child)
            return
        api = AdminSeedApi()
        try:
            region_ids = {f"Region-{code}": api.create_region(f"Region-{code}")}
            api.create_legal_form(f"MCHJ-{code}")
            api.create_product_group(INDUSTRY_GROUP_PCODE, f"Industry-{code}")
            api.create_product_group(CATEGORY_GROUP_PCODE, f"Category-{code}")
            api.create_manufacturer(f"Manufacturer-{code}")
            for region_code in regions:
                region_ids[f"Region-{region_code}"] = api.create_region(f"Region-{region_code}")
            for parent, child in children:
                api.create_region(child, region_ids.get(parent) or api.region_id(parent))
        finally:
            api.logout()


def seed_products(page: Page, code, category, names, refs_code=None) -> None:
    """Tovarlar (Manufacturer-/Industry-{refs_code}, ``category``; refs_code default ``code``) +
    supplier-{code} ga biriktirish, «В наличие» va narx (run_product_linking ekvivalenti).
    UI rejimi = ``create_products``."""
    mode, refs_code = seed_mode(), refs_code or code
    with allure.step(f"Seed tovarlar ({mode}): {', '.join(names)} ({category})"):
        if mode == "ui":
            for name in names:
                run_product(page, code, manufacturer=f"Manufacturer-{refs_code}", industry=f"Industry-{refs_code}",
                            category=category, name=name)
                run_product_linking(page, code, product_name=name)
            return
        api = AdminSeedApi()
        try:
            manufacturer_id = api.manufacturer_id(f"Manufacturer-{refs_code}")
            industry_id = api.product_group_id(INDUSTRY_GROUP_PCODE, f"Industry-{refs_code}")
            category_id = api.product_group_id(CATEGORY_GROUP_PCODE, category)
            measure_id = api.measure_id("кг")
            supplier = f"supplier-{code}"
            supplier_id = api.supplier_id(supplier)
            for name in names:
                product_id = api.create_product(name, manufacturer_id, industry_id, category_id, measure_id)
                api.link_product_to_supplier(supplier_id, supplier, product_id)
        finally:
            api.logout()


def seed_supplier(page: Page, code, *, region, ownership, industry, extra_regions=()) -> None:
    """supplier-{code} (Поставщик, regionlar ``region`` + ``extra_regions``) + supplier_user-{code}
    («Админ (Поставщик)», parol "1"). api: yaratilgach «Склад по умолчанию» avtomatik paydo
    bo'lgani va user login'i tekshiriladi. UI rejimi = run_supplier + run_supplier_user."""
    mode = seed_mode()
    with allure.step(f"Seed supplier ({mode}): supplier-{code} ({region}, {list(extra_regions)}) "
                     f"+ supplier_user-{code}"):
        if mode == "ui":
            run_supplier(page, code, region=region, ownership=ownership, industry=industry,
                         extra_regions=extra_regions)
            run_supplier_user(page, code)
            return
        api = AdminSeedApi()
        try:
            name = f"supplier-{code}"
            supplier_id = api.create_legal_person(
                name, supplier=True, legal_form_id=api.legal_form_id(ownership),
                industry_id=api.product_group_id(INDUSTRY_GROUP_PCODE, industry), regions=(region, *extra_regions))
            api.create_supplier_user(supplier_id, name, f"supplier_user-{code}")
        finally:
            api.logout()
        user_api = _assert_can_login(f"supplier_user-{code}")
        try:
            user_api.default_warehouse_id()   # «Склад по умолчанию» supplier bilan avtomatik
        finally:
            user_api.logout()


def seed_clients(page: Page, code, supplier, clients, *, ownership, industry) -> None:
    """``clients`` — ((client_code, region), ...): client-{client_code} + client_user-{client_code}
    («Админ (Клиент)», o'z savdo nuqtasi), so'ng ``supplier`` bilan hamkorlik (so'rov + tasdiq).
    api: user login'i va hamkorlik «Мои клиенты»da tekshiriladi. UI rejimi = ``create_clients``."""
    mode = seed_mode()
    with allure.step(f"Seed mijozlar ({mode}): {[f'client-{client_code}' for client_code, _ in clients]} "
                     f"+ userlar, hamkorlik {supplier}"):
        if mode == "ui":
            create_clients(page, code, supplier, clients, ownership=ownership, industry=industry)
            return
        api = AdminSeedApi()
        try:
            legal_form_id = api.legal_form_id(ownership)
            industry_id = api.product_group_id(INDUSTRY_GROUP_PCODE, industry)
            supplier_id = api.supplier_id(supplier)
            client_ids = []
            for client_code, region in clients:
                name = f"client-{client_code}"
                client_id = api.create_legal_person(name, supplier=False, legal_form_id=legal_form_id,
                                                    industry_id=industry_id, regions=(region,))
                api.create_client_user(client_id, name, f"client_user-{client_code}")
                client_ids.append(client_id)
            for client_id in client_ids:
                api.create_cooperation(supplier_id, supplier, client_id)
        finally:
            api.logout()
        for client_code, _ in clients:
            _assert_can_login(f"client_user-{client_code}").logout()


def seed_warehouses(page: Page, code, warehouses) -> None:
    """Alfa (supplier_user-{code}) omborlari: ``warehouses`` — ((nom, kod, region nomi), ...).
    UI rejimida ``page`` supplier_user-{code} sifatida kirgan bo'lishi shart."""
    mode = seed_mode()
    with allure.step(f"Seed omborlar ({mode}): {[warehouse[0] for warehouse in warehouses]}"):
        if mode == "ui":
            for name, warehouse_code, region in warehouses:
                create_warehouse(page, name, warehouse_code, region)
            return
        api = WarehouseApi(f"supplier_user-{code}@{COMPANY_CODE}")
        try:
            for name, warehouse_code, region in warehouses:
                api.create(name, warehouse_code, api.region_ids(region))
        finally:
            api.logout()


def seed_binds(page: Page, code, attach=(), detach=(), in_stock=()) -> None:
    """Alfa bog'lanishlari: ``attach``/``detach`` — ((ombor, tovar), ...); ``in_stock`` — tovarlar
    («В наличие» Y — tovarning BARCHA ombor bog'lanishlari). Har qism qayta o'qib tasdiqlanadi.
    UI rejimida ``page`` supplier_user-{code} sifatida kirgan bo'lishi shart."""
    mode = seed_mode()
    with allure.step(f"Seed bog'lanishlar ({mode}): +{list(attach)} −{list(detach)} В наличие {list(in_stock)}"):
        if mode == "ui":
            for warehouse, product in attach:
                attach_product(page, warehouse, product)
            for warehouse, product in detach:
                detach_product(page, warehouse, product)
            for product in in_stock:
                toggle_in_stock(page, product)
            return
        api = WarehouseApi(f"supplier_user-{code}@{COMPANY_CODE}")
        try:
            for warehouse, product in attach:
                warehouse_id = api.warehouse_id(warehouse)
                response = api.attach(warehouse_id, api.product_id(warehouse_id, product, attached="N"))
                assert response.status_code == 200, \
                    f"«{warehouse}» $attach {product} → HTTP {response.status_code}: {response.text[:300]}"
                api.product_id(warehouse_id, product, attached="Y")
            for warehouse, product in detach:
                warehouse_id = api.warehouse_id(warehouse)
                response = api.detach(warehouse_id, api.product_id(warehouse_id, product, attached="Y"))
                assert response.status_code == 200, \
                    f"«{warehouse}» $detach {product} → HTTP {response.status_code}: {response.text[:300]}"
                assert not api.products(warehouse_id, "Y", product), f"«{warehouse}» da {product} hali biriktirilgan"
            for product in in_stock:
                api.change_avail(str(api.supplier_product(product)["product_id"]), "Y")
                info = api.supplier_product(product)
                avail_by_warehouse = {warehouse["name"]: bind["avail"] for warehouse in api.warehouses()
                                      for bind in api.products(str(warehouse["warehouse_id"]), "Y", product)}
                assert info["avail"] == "Y" and all(avail == "Y" for avail in avail_by_warehouse.values()), \
                    f"{product}: avail={info['avail']}, omborlarda {avail_by_warehouse} (kutilgan hammasi Y)"
        finally:
            api.logout()
