"""S-05 web testlari uchun umumiy ma'lumot — BIR MARTA yaratiladi (session scope: bitta
pytest chaqiruvida test_warehouse_list / _form / _products fayllari bo'lishadi).

Kod varianti ``{code}10``: Alfa supplier + user; tovarlar «Sut 1L / Non / Qatiq-{c}»;
«Toshkent ombori» (TSH, Ташкент) da Non; Qatiq hech qaysi omborda emas; Sut faqat
«Склад по умолчанию» da.

``beta_seed`` (``{code}12``, Alfa ma'lumotnomalari ustida): Beta supplier + user, tovar
«Beta-{c}» (Beta standart omboriga avtomatik tushadi) va API orqali «Beta ombori» —
S-05 API (egalik) testlari uchun.

Seed yiqilsa (`retry_seed`) sahifa tiklanib 1 marta `r`-prefiksli kod bilan (`r{code}10`,
`r{code}12`) noldan qayta yaratiladi; testlar faqat qaytgan dict (`["c"]`) bilan ishlaydi.

Refs/tovar/ombor/bog'lanishlar ``S05_SEED_MODE`` (default ``api``, ``ui`` — eski yo'l) bo'yicha
``seed_api`` orqali (supplier + user va tovarni supplier'ga biriktirish + narx ham).
"""
import allure
import pytest
from playwright.sync_api import Page

from flows.flow_authorization import COMPANY_CODE, authorization, logout
from tests.sbr.supplier.warehouse.warehouse_api import WarehouseApi
from tests.sbr.supplier.warehouse.seed_api import (
    seed_binds, seed_products, seed_reference_data, seed_supplier, seed_warehouses,
)
from tests.sbr.supplier.warehouse.warehouse_helpers import (
    DEFAULT_WAREHOUSE, TSH_CODE, TSH_NAME, TSH_REGION, login_supplier_user, retry_seed,
)


def _build_alfa(page: Page, c) -> dict:
    d = {"c": c, "supplier": f"supplier-{c}", "sut": f"Sut 1L-{c}", "non": f"Non-{c}",
         "qatiq": f"Qatiq-{c}"}
    with allure.step(f"Setup (admin): refs + Manufacturer-{c}, Alfa {d['supplier']} + user"):
        authorization(page)
        seed_reference_data(page, c)
        seed_supplier(page, c, region=f"Region-{c}", ownership=f"MCHJ-{c}", industry=f"Industry-{c}")
    with allure.step(f"Setup (admin): tovarlar {d['sut']}, {d['non']}, {d['qatiq']} — biriktirish + narx"):
        seed_products(page, c, f"Category-{c}", (d["sut"], d["non"], d["qatiq"]))
    with allure.step(f"Setup (Alfa): «{TSH_NAME}» ({TSH_REGION}) + {d['non']}; {d['qatiq']} hech qaysi omborda emas"):
        login_supplier_user(page, c)
        seed_warehouses(page, c, ((TSH_NAME, TSH_CODE, TSH_REGION),))
        seed_binds(page, c, attach=((TSH_NAME, d["non"]),), detach=((DEFAULT_WAREHOUSE, d["qatiq"]),))
    return d


@pytest.fixture(scope="session")
def alfa_seed(session_page: Page, code) -> dict:
    """Yiqilsa ``retry_seed`` 1 marta ``r{code}10`` bilan noldan qayta yaratadi."""
    return retry_seed(session_page, lambda c: _build_alfa(session_page, c), f"{code}10", "alfa_seed")


def _build_beta(page: Page, c, a) -> dict:
    d = {"c": c, "supplier": f"supplier-{c}", "product": f"Beta-{c}", "warehouse": f"Beta ombori-{c}",
         "login": f"supplier_user-{c}@{COMPANY_CODE}"}
    with allure.step(f"Setup (admin): Beta {d['supplier']} + user, tovar {d['product']} (Alfa ma'lumotnomalari)"):
        # 1-urinishda alfa'dan keyin supplier user seansi ochiq — faqat shunda logout;
        # retry'da sahifa login'da (login_admin ichidagi logout 60s bekor kutardi).
        if page.locator("app-user-dropdown").is_visible():
            logout(page)
        authorization(page)
        seed_supplier(page, c, region=f"Region-{a}", ownership=f"MCHJ-{a}", industry=f"Industry-{a}")
        seed_products(page, c, f"Category-{a}", (d["product"],), refs_code=a)
    with allure.step(f"Setup (Beta, API): «{d['warehouse']}» ({TSH_REGION}); ID'lar"):
        api = WarehouseApi(d["login"])
        try:
            d["warehouse_id"] = api.create(d["warehouse"], "BET", api.region_ids(TSH_REGION))
            d["default_id"] = api.default_warehouse_id()
            d["supplier_id"] = str(api.edit_model(d["warehouse_id"])["supplier_id"])
            d["product_id"] = api.product_id(d["default_id"], d["product"])   # standartga avtomatik
        finally:
            api.logout()
    return d


@pytest.fixture(scope="session")
def beta_seed(session_page: Page, code, alfa_seed) -> dict:
    """Yiqilsa ``retry_seed`` 1 marta ``r{code}12`` bilan noldan qayta yaratadi."""
    a = alfa_seed["c"]
    return retry_seed(session_page, lambda c: _build_beta(session_page, c, a), f"{code}12", "beta_seed")
