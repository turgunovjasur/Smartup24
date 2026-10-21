"""S-05 API (web, ``requests``): 1.5 egalik, 1.3 standart ombor himoyasi, 2.1(f) mavjud
bo'lmagan region, 2.3 region_id kalitisiz tahrir, 3.2 boshqa supplier tovarini biriktirish.
Test-case: docs/qa/test-cases/sbr/supplier/warehouse.md.

Har test o'z vaqtinchalik omborini yaratadi va ``finally`` da tozalaydi — Alfa'ning
TSH/standart omborlariga tegilmaydi (papkada bu fayl birinchi yuradi). Tartib muhim:
1.5 «$delete» va 1.3 «$delete» Beta omborlarini o'chirishi mumkin — oxirroqda.
"""
import allure
import pytest

from flows.flow_authorization import COMPANY_CODE
from tests.sbr.supplier.warehouse.warehouse_api import DEFAULT_PCODE, W, WarehouseApi
from tests.sbr.supplier.warehouse.warehouse_helpers import (
    BUX_REGION, DEFAULT_WAREHOUSE, RAW_ERROR_MARKERS, TSH_REGION, known_bug,
)

REASON_OWNER = "SMAR24-926/1061: ombor egaligi tekshirilmaydi — Alfa {}"
REASON_DEFAULT = "SMAR24-1059: API pcode'ni tekshirmaydi — standart ombor {}"
REASON_REGION_RAW = "SMAR24-1060: mavjud bo'lmagan region_id — xom texnik xato (Z:#z: parent key not found)"
REASON_REGION_ABSENT = "SMAR24-1060: region_id kalitisiz edit$save barcha regionlarni o'chiradi"


@pytest.fixture
def alfa_api(alfa_seed):
    api = WarehouseApi(f"supplier_user-{alfa_seed['c']}@{COMPANY_CODE}")
    yield api
    api.logout()


@pytest.fixture
def beta_api(beta_seed):
    api = WarehouseApi(beta_seed["login"])
    yield api
    api.logout()


def _rejected(r) -> None:
    assert r.status_code != 200, f"So'rov rad etilmadi: HTTP 200 {r.text[:200]!r}"


def _delete_if_exists(apis, name) -> None:
    """Vaqtinchalik omborni uni ko'radigan sessiya bilan o'chiradi (tozalash)."""
    for api in apis:
        found = api.warehouses(name)
        if found:
            api.delete(*(str(w["warehouse_id"]) for w in found))
            return


# ── S-05.1.5 Egalik ─────────────────────────────────────────────────────────────────
@allure.id("S-05.1.5")
@allure.epic("Supplier")
@allure.feature("S-05 Склады")
@allure.story("Egalik")
@allure.title("S-05.1.5 — Alfa «Beta ombori» ma'lumotlarini ko'ra olmaydi")
@allure.tag("access", "negative", "bug-candidate")
def test_api_foreign_warehouse_edit_model_rejected(alfa_api, beta_seed) -> None:
    """Alfa sessiyasi → warehouse+edit:model «Beta ombori».
    Kutilgan: rad (HTTP 200 emas)."""
    with allure.step("Alfa → edit:model «Beta ombori»"):
        r = alfa_api.post(f"{W}/warehouse+edit:model", {"warehouse_id": beta_seed["warehouse_id"]})
    with allure.step("Kutilgan: rad"), known_bug(REASON_OWNER.format("«Beta ombori»ni ochadi (edit:model)")):
        _rejected(r)


@allure.id("S-05.1.5")
@allure.epic("Supplier")
@allure.feature("S-05 Склады")
@allure.story("Egalik")
@allure.title("S-05.1.5 — Alfa «Beta ombori»ni qayta nomlay olmaydi")
@allure.tag("access", "negative", "bug-candidate")
def test_api_foreign_warehouse_rename_rejected(alfa_api, beta_api, beta_seed) -> None:
    """Alfa sessiyasi → warehouse+edit$save «Beta ombori» yangi nom bilan.
    Kutilgan: rad, Beta sessiyasida nom o'zgarmagan."""
    wid = beta_seed["warehouse_id"]
    model = beta_api.edit_model(wid)
    try:
        with allure.step("Alfa → edit$save «Beta ombori» name=«Alfa nomi»"):
            r = alfa_api.edit_save(model, name=f"Alfa nomi-{beta_seed['c']}")
        with allure.step("Kutilgan: rad, Beta'da nom o'zgarmagan"):
            name = beta_api.edit_model(wid)["name"]
            with known_bug(REASON_OWNER.format("«Beta ombori»ni qayta nomlaydi")):
                assert name == model["name"], f"Nom o'zgargan: «{name}» (HTTP {r.status_code})"
                _rejected(r)
    finally:
        if beta_api.edit_model(wid)["name"] != model["name"]:
            beta_api.edit_save(model)   # asl nomni tiklash


@allure.id("S-05.1.5")
@allure.epic("Supplier")
@allure.feature("S-05 Склады")
@allure.story("Egalik")
@allure.title("S-05.1.5 — Alfa o'z tovarini «Beta ombori»ga biriktira olmaydi")
@allure.tag("access", "negative", "bug-candidate")
def test_api_foreign_warehouse_attach_rejected(alfa_api, alfa_seed, beta_seed) -> None:
    """Alfa sessiyasi → bind_list$attach «Beta ombori» + Alfa tovari.
    Kutilgan: rad, «Beta ombori»da Alfa tovari yo'q. Bind ro'yxati faqat CHAQIRUVCHI supplier
    tovarlarini ko'rsatadi (DEV 2026-10-18) — shuning uchun Alfa ko'rinishidan tekshiriladi."""
    wid, sut = beta_seed["warehouse_id"], alfa_seed["sut"]
    pid = alfa_api.product_id(alfa_api.default_warehouse_id(), sut)
    try:
        with allure.step(f"Alfa → $attach «Beta ombori» + {sut}"):
            r = alfa_api.attach(wid, pid)
        with allure.step("Kutilgan: rad, «Beta ombori»da Alfa tovari yo'q"):
            attached = alfa_api.products(wid, "Y", sut)
            with known_bug(REASON_OWNER.format("«Beta ombori»ga o'z tovarini biriktiradi")):
                assert not attached, f"{sut} «Beta ombori»ga biriktirilgan (HTTP {r.status_code})"
                _rejected(r)
    finally:
        if alfa_api.products(wid, "Y", sut):
            alfa_api.detach(wid, pid)   # Beta sessiyasi Alfa tovarini ocholmaydi (ko'rmaydi)


@allure.id("S-05.1.5")
@allure.epic("Supplier")
@allure.feature("S-05 Склады")
@allure.story("Egalik")
@allure.title("S-05.1.5 — Alfa «Beta ombori»dan Beta tovarini ochira olmaydi")
@allure.tag("access", "negative", "bug-candidate")
def test_api_foreign_warehouse_detach_rejected(alfa_api, beta_api, beta_seed) -> None:
    """Beta sessiyasi «Beta ombori»ga Beta tovarini biriktiradi → Alfa sessiyasi $detach.
    Kutilgan: rad (holat o'zgarmagan) — tovar Beta «Прикрепленные»da qoladi.
    DEV 2026-10-18: server 200 qaytaradi, lekin begona tovarni jim e'tiborsiz qoldiradi — xato xabari yo'q (Team Lead'ga xabar)."""
    wid, pid, product = beta_seed["warehouse_id"], beta_seed["product_id"], beta_seed["product"]
    try:
        with allure.step(f"Beta → $attach «Beta ombori» + {product}"):
            assert beta_api.attach(wid, pid).status_code == 200
            assert beta_api.products(wid, "Y", product), "Beta o'z tovarini biriktira olmadi"
        with allure.step(f"Alfa → $detach «Beta ombori» + {product}"):
            r = alfa_api.detach(wid, pid)
        with allure.step(f"Kutilgan: rad — tovar biriktirilganicha qoladi (javob HTTP {r.status_code}, faqat dalil)"):
            assert beta_api.products(wid, "Y", product), f"{product} ochirilgan (HTTP {r.status_code})"
    finally:
        if beta_api.products(wid, "Y", product):
            beta_api.detach(wid, pid)


@allure.id("S-05.1.5")
@allure.epic("Supplier")
@allure.feature("S-05 Склады")
@allure.story("Egalik")
@allure.title("S-05.1.5 — Alfa o'z omborini Beta'ga o'tkaza olmaydi")
@allure.tag("access", "negative", "bug-candidate")
def test_api_warehouse_owner_change_rejected(alfa_api, beta_api, beta_seed) -> None:
    """Alfa vaqtinchalik ombor → warehouse+edit$save supplier_id = Beta.
    Kutilgan: rad, ombor Alfa'da qoladi, Beta ro'yxatida yo'q."""
    c = beta_seed["c"]
    name = f"API egasi-{c}"
    try:
        with allure.step(f"Alfa: vaqtinchalik ombor «{name}»"):
            model = alfa_api.edit_model(alfa_api.create(name, f"AE{c}", alfa_api.region_ids(TSH_REGION)))
        with allure.step("Alfa → edit$save supplier_id = Beta"):
            r = alfa_api.edit_save(model, supplier_id=beta_seed["supplier_id"])
        with allure.step("Kutilgan: rad, ombor Alfa'da, Beta'da yo'q"):
            in_beta, in_alfa = beta_api.warehouses(name), alfa_api.warehouses(name)
            with known_bug(REASON_OWNER.format("o'z omborini Beta'ga o'tkazadi (edit$save supplier_id)")):
                assert not in_beta, f"Ombor Beta ro'yxatiga o'tgan (HTTP {r.status_code})"
                assert in_alfa, "Ombor Alfa ro'yxatidan yo'qolgan"
                _rejected(r)
    finally:
        _delete_if_exists((alfa_api, beta_api), name)


@allure.id("S-05.1.5")
@allure.epic("Supplier")
@allure.feature("S-05 Склады")
@allure.story("Egalik")
@allure.title("S-05.1.5 — Alfa «Beta ombori»ni o'chira olmaydi")
@allure.tag("access", "negative", "bug-candidate")
def test_api_foreign_warehouse_delete_rejected(alfa_api, beta_api, beta_seed) -> None:
    """Alfa sessiyasi → warehouse_list$delete «Beta ombori» (1.5 ning oxirgi testi).
    Kutilgan: rad, Beta ro'yxatida ombor qoladi."""
    with allure.step("Alfa → $delete «Beta ombori»"):
        r = alfa_api.delete(beta_seed["warehouse_id"])
    with allure.step("Kutilgan: rad, «Beta ombori» Beta'da bor"):
        left = beta_api.warehouses(beta_seed["warehouse"])
        with known_bug(REASON_OWNER.format("«Beta ombori»ni o'chiradi")):
            assert left, f"«Beta ombori» o'chirilgan (HTTP {r.status_code})"
            _rejected(r)


# ── S-05.1.3 Standart ombor himoyasi ──────────────────────────────────────────────────
@allure.id("S-05.1.3")
@allure.epic("Supplier")
@allure.feature("S-05 Склады")
@allure.story("Standart ombor himoyasi")
@allure.title("S-05.1.3 — «Склад по умолчанию»ni API orqali qayta nomlab bo'lmaydi")
@allure.tag("negative", "bug-candidate")
def test_api_default_warehouse_rename_rejected(beta_api, beta_seed) -> None:
    """Beta sessiyasi → edit$save o'z standart omboriga name=«Boshqa».
    Kutilgan: rad (pcode), nom o'zgarmagan."""
    wid = beta_seed["default_id"]
    model = beta_api.edit_model(wid)
    try:
        with allure.step("Beta → edit$save «Склад по умолчанию» name=«Boshqa»"):
            r = beta_api.edit_save(model, name="Boshqa")
        with allure.step(f"Kutilgan: rad, nom «{DEFAULT_WAREHOUSE}»"):
            name = beta_api.edit_model(wid)["name"]
            with known_bug(REASON_DEFAULT.format("qayta nomlanadi")):
                assert name == DEFAULT_WAREHOUSE, f"Standart ombor qayta nomlangan: «{name}» (HTTP {r.status_code})"
                _rejected(r)
    finally:
        if beta_api.edit_model(wid)["name"] != model["name"]:
            beta_api.edit_save(model)


@allure.id("S-05.1.3")
@allure.epic("Supplier")
@allure.feature("S-05 Склады")
@allure.story("Standart ombor himoyasi")
@allure.title("S-05.1.3 — «Склад по умолчанию»ni API orqali o'chirib bo'lmaydi")
@allure.tag("negative", "bug-candidate")
def test_api_default_warehouse_delete_rejected(beta_api, beta_seed) -> None:
    """Beta sessiyasi → $delete o'z standart ombori (o'chsa tiklab bo'lmaydi — faqat Beta).
    Kutilgan: rad (pcode), standart ombor qoladi."""
    with allure.step("Beta → $delete «Склад по умолчанию»"):
        r = beta_api.delete(beta_seed["default_id"])
    with allure.step("Kutilgan: rad, standart ombor ro'yxatda"):
        left = [w for w in beta_api.warehouses() if w["pcode"] == DEFAULT_PCODE]
        with known_bug(REASON_DEFAULT.format("o'chiriladi")):
            assert left, f"Standart ombor o'chirilgan (HTTP {r.status_code})"
            _rejected(r)


# ── S-05.2.1 (f) / 2.3 Forma (API) ───────────────────────────────────────────────────
@allure.id("S-05.2.1")
@allure.epic("Supplier")
@allure.feature("S-05 Склады")
@allure.story("Yaratish — maydonlar va tekshiruvlar")
@allure.title("S-05.2.1 (f) — Mavjud bo'lmagan region_id: tushunarli xato")
@allure.tag("crud", "negative", "bug-candidate")
def test_api_create_unknown_region_error(alfa_api, alfa_seed) -> None:
    """Alfa → warehouse+add$save region_id=[999999999]. Kutilgan: tushunarli xato
    (xom belgilarsiz), ombor yaratilmaydi. «Beta kompaniyasi regioni» qismi — DEV'da
    ikkinchi kompaniya yo'q, tekshirilmaydi."""
    c = alfa_seed["c"]
    name = f"API region-{c}"
    try:
        with allure.step("Alfa → add$save region_id=[999999999]"):
            r = alfa_api.post(f"{W}/warehouse+add$save", {"code": f"AR{c}", "name": name, "region_id": ["999999999"]})
        with allure.step("Kutilgan: xato (200 emas), ombor yaratilmagan"):
            _rejected(r)
            assert r.text.strip(), "Xato matni bo'sh"
            assert not alfa_api.warehouses(name), "Ombor yaratilgan"
        with allure.step("Kutilgan: tushunarli xato — matn xom texnik belgilarsiz"), known_bug(REASON_REGION_RAW):
            raw = [mk for mk in RAW_ERROR_MARKERS if mk in r.text]
            assert not raw, f"Xom texnik xato ({', '.join(raw)}): {r.text[:300]}"
    finally:
        _delete_if_exists((alfa_api,), name)


@allure.id("S-05.2.3")
@allure.epic("Supplier")
@allure.feature("S-05 Склады")
@allure.story("Regionsiz tahrirlash (API)")
@allure.title("S-05.2.3 — region_id kaliti yuborilmasa regionlar o'zgarmaydi")
@allure.tag("crud", "negative", "bug-candidate")
def test_api_edit_without_region_key_keeps_regions(alfa_api, alfa_seed) -> None:
    """Alfa vaqtinchalik ombor 2 region bilan → edit$save yangi nom, region_id kalitisiz.
    Kutilgan: ikkala region saqlanib qoladi («absent keeps»)."""
    c = alfa_seed["c"]
    name = f"API 2 region-{c}"
    try:
        with allure.step(f"Alfa: vaqtinchalik ombor «{name}» ({TSH_REGION} + {BUX_REGION})"):
            regions = alfa_api.region_ids(TSH_REGION, BUX_REGION)
            model = alfa_api.edit_model(alfa_api.create(name, f"A2{c}", regions))
            assert sorted(map(str, model["region_id"])) == sorted(regions), f"Regionlar: {model['region_id']}"
        with allure.step(f"Alfa → edit$save name=«{name} 2», region_id kalitisiz"):
            body = {k: model[k] for k in ("warehouse_id", "supplier_id", "code")}
            r = alfa_api.post(f"{W}/warehouse+edit$save", {**body, "name": f"{name} 2"})
            assert r.status_code == 200, f"Saqlanmadi: HTTP {r.status_code} {r.text[:200]}"
        with allure.step("Kutilgan: edit:model'da ikkala region"):
            after = alfa_api.edit_model(model["warehouse_id"])["region_id"] or []
            with known_bug(REASON_REGION_ABSENT):
                assert sorted(map(str, after)) == sorted(regions), f"Regionlar o'zgargan: {after}"
    finally:
        _delete_if_exists((alfa_api,), name)
        _delete_if_exists((alfa_api,), f"{name} 2")


# ── S-05.3.2 Boshqa supplier tovarini biriktirish ─────────────────────────────────────
@allure.id("S-05.3.2")
@allure.epic("Supplier")
@allure.feature("S-05 Склады")
@allure.story("Boshqa yetkazib beruvchi tovarini biriktirish")
@allure.title("S-05.3.2 — Alfa omboriga Beta tovarini biriktirib bo'lmaydi")
@allure.tag("access", "negative", "bug-candidate")
def test_api_attach_foreign_product_rejected(alfa_api, beta_api, alfa_seed, beta_seed) -> None:
    """Alfa vaqtinchalik ombor → $attach Beta tovari. Kutilgan: rad (holat o'zgarmagan), «Прикрепленные»da yo'q
    (bind ro'yxati chaqiruvchi supplier tovarlarini ko'rsatadi — Beta ko'rinishidan ham).
    Xizmat («Yetkazib berish») qismi — DEV'da xizmat tovari yo'q, tekshirilmaydi.
    DEV 2026-10-18: server 200 qaytaradi, lekin begona tovarni jim e'tiborsiz qoldiradi — xato xabari yo'q (Team Lead'ga xabar)."""
    c, product = alfa_seed["c"], beta_seed["product"]
    name = f"API chet tovar-{c}"
    try:
        with allure.step(f"Alfa: vaqtinchalik ombor «{name}»"):
            wid = alfa_api.create(name, f"AT{c}", alfa_api.region_ids(TSH_REGION))
        with allure.step(f"Alfa → $attach «{name}» + {product} (Beta tovari)"):
            r = alfa_api.attach(wid, beta_seed["product_id"])
        with allure.step(f"Kutilgan: rad — «Прикрепленные»da yo'q (javob HTTP {r.status_code}, faqat dalil)"):
            assert not alfa_api.products(wid, "Y", product), f"{product} biriktirilgan (HTTP {r.status_code})"
            assert not beta_api.products(wid, "Y", product), f"{product} biriktirilgan (Beta ko'rinishi)"
    finally:
        _delete_if_exists((alfa_api,), name)
