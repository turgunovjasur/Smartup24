"""S-05 web testlari uchun umumiy ma'lumot — BIR MARTA yaratiladi (session scope: bitta
pytest chaqiruvida test_warehouse_list / _form / _products fayllari bo'lishadi).

Kod varianti ``{code}10``: Alfa supplier + user; tovarlar «Sut 1L / Non / Qatiq-{c}»;
«Toshkent ombori» (TSH, Ташкент) da Non; Qatiq hech qaysi omborda emas; Sut faqat
«Склад по умолчанию» da.

``beta_seed`` (``{code}12``, Alfa ma'lumotnomalari ustida): Beta supplier + user, tovar
«Beta-{c}» (Beta standart omboriga avtomatik tushadi) va API orqali «Beta ombori» —
S-05 API (egalik) testlari uchun.
"""
import allure
import pytest
from playwright.sync_api import Page

from flows.flow_authorization import COMPANY_CODE, authorization
from tests.sbr.supplier.warehouse.warehouse_api import WarehouseApi
from tests.sbr.supplier.warehouse.warehouse_helpers import (
    DEFAULT_WAREHOUSE, TSH_CODE, TSH_NAME, TSH_REGION,
    attach_product, create_products, create_warehouse, detach_product, login_admin,
    login_supplier_user,
)
from tests.test_group_a.test_product import run_product
from tests.test_group_a.test_product_linking import run_product_linking
from tests.test_group_a.test_supplier import run_supplier
from tests.test_group_a.test_supplier_user import run_supplier_user
from tests.test_setup.test_manufacturer import run_manufacturer
from tests.test_setup.test_supplier import ensure_refs


@pytest.fixture(scope="session")
def alfa_seed(session_page: Page, code) -> dict:
    c = f"{code}10"
    d = {"c": c, "supplier": f"supplier-{c}", "sut": f"Sut 1L-{c}", "non": f"Non-{c}",
         "qatiq": f"Qatiq-{c}"}
    page = session_page
    with allure.step(f"Setup (admin): refs + Manufacturer-{c}, Alfa {d['supplier']} + user"):
        authorization(page)
        ensure_refs(page, c)
        run_manufacturer(page, c)
        run_supplier(page, c, region=f"Region-{c}", ownership=f"MCHJ-{c}", industry=f"Industry-{c}")
        run_supplier_user(page, c)
    with allure.step(f"Setup (admin): tovarlar {d['sut']}, {d['non']}, {d['qatiq']} — biriktirish + narx"):
        create_products(page, c, f"Category-{c}", (d["sut"], d["non"], d["qatiq"]))
    with allure.step(f"Setup (Alfa): «{TSH_NAME}» ({TSH_REGION}) + {d['non']}; {d['qatiq']} hech qaysi omborda emas"):
        login_supplier_user(page, c)
        create_warehouse(page, TSH_NAME, TSH_CODE, TSH_REGION)
        attach_product(page, TSH_NAME, d["non"])
        detach_product(page, DEFAULT_WAREHOUSE, d["qatiq"])
    return d


@pytest.fixture(scope="session")
def beta_seed(session_page: Page, code, alfa_seed) -> dict:
    a, c = alfa_seed["c"], f"{code}12"
    d = {"c": c, "supplier": f"supplier-{c}", "product": f"Beta-{c}", "warehouse": f"Beta ombori-{c}",
         "login": f"supplier_user-{c}@{COMPANY_CODE}"}
    page = session_page
    with allure.step(f"Setup (admin): Beta {d['supplier']} + user, tovar {d['product']} (Alfa ma'lumotnomalari)"):
        login_admin(page)
        run_supplier(page, c, region=f"Region-{a}", ownership=f"MCHJ-{a}", industry=f"Industry-{a}")
        run_supplier_user(page, c)
        run_product(page, c, manufacturer=f"Manufacturer-{a}", industry=f"Industry-{a}",
                    category=f"Category-{a}", name=d["product"])
        run_product_linking(page, c, product_name=d["product"])
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
