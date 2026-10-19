"""S-05 mobil katalog yordamchilari (test emas): mobil login, katalogda tovar ko'rinishini
o'qish, katalog guruhining umumiy seed'i va har keys boshidagi web holat.

«Yo'q» natijasi FAQAT yuklanganlik tasdiqlangandan keyin (soxta PASS bo'lmasin):
  «Категории» tabi umuman yo'q (tablar yuklangan) / kategoriya yo'q / ro'yxat yuklangan
  (tovar kartalari yoki «Ничего не найдено!»).
"""
import allure

from flows.flow_authorization import COMPANY_CODE, authorization
from tests.sbr.supplier.warehouse.warehouse_helpers import (
    SAM_CODE, SAM_NAME, TSH_CODE, TSH_NAME,
    create_child_region, create_warehouse, login_supplier_user, set_binds, set_in_stock,
    set_warehouse_regions,
)
from tests.test_group_a.test_client import run_client
from tests.test_group_a.test_client_user import run_client_user
from tests.test_group_a.test_cooperation import run_cooperation
from tests.test_group_a.test_product import run_product
from tests.test_group_a.test_product_linking import run_product_linking
from tests.test_group_a.test_supplier import run_supplier
from tests.test_group_a.test_supplier_user import run_supplier_user
from tests.test_setup.test_manufacturer import run_manufacturer
from tests.test_setup.test_region import run_region
from tests.test_setup.test_supplier import ensure_refs
from tests_mobile.config import WEB_USER_PASSWORD
from tests_mobile.screens.catalog_screen import CatalogScreen
from tests_mobile.screens.login_screen import LoginScreen


# ── mobil katalog ───────────────────────────────────────────────────────────────────
def mobile_login(driver, client_code) -> None:
    """client_user-{client_code} sifatida (allaqachon kirgan bo'lsa qayta kirmaydi)."""
    user = f"client_user-{client_code}@{COMPANY_CODE}"
    with allure.step(f"Mobil login: {user}"):
        login = LoginScreen(driver)
        login.ensure_logged_in_as(user, WEB_USER_PASSWORD)
        # sekin emulyatorda login 20s dan oshadi — faqat shu yerda 60s
        assert login.is_logged_in(timeout=60), f"Mobil login muvaffaqiyatsiz: {user}"


def catalog_view(driver, client_code, supplier, category, products) -> dict:
    """Mobil: Постав. → supplier → category; har tovar ko'rinadimi ({tovar: bool})."""
    mobile_login(driver, client_code)
    cs = CatalogScreen(driver)
    cs.open_supplier(supplier, require_categories=False)
    view = {p: False for p in products}
    if not cs.supplier_has_categories():
        state = "«Категории» tabi yo'q"
    elif not cs.find_category(category):
        state = f"{category} yo'q"
    elif not cs.open_category_listing(category):
        state = "«Ничего не найдено!»"
    else:
        state = "tovar kartalari"
        view = {p: cs.has_product(p) for p in products}
    allure.attach(f"client_user-{client_code}: {state}; {view}", name=f"katalog client-{client_code}",
                  attachment_type=allure.attachment_type.TEXT)
    return view


def expect_in_view(view, client_code, *, present=(), absent=()) -> None:
    """``present`` tovarlar ko'rinishi, ``absent`` lar ko'rinmasligi shart."""
    for p in present:
        assert view[p], f"client-{client_code} katalogida '{p}' YO'Q (kutilgan: bor). Ko'rinish: {view}"
    for p in absent:
        assert not view[p], f"client-{client_code} katalogida '{p}' BOR (kutilgan: yo'q). Ko'rinish: {view}"


# ── katalog guruhi: umumiy seed va har keys boshidagi holat (web, Alfa) ───────────────
def catalog_names(c) -> dict:
    """Seed nomlari ({code}11): shahar → tuman regionlari, Alfa/Gamma/Epsilon, 3 tovar."""
    return {
        "c": c, "supplier": f"supplier-{c}", "category": f"Category-{c}",
        "gamma": f"{c}g", "epsilon": f"{c}e",
        "city": f"Region-{c}city", "tuman": f"Region-{c}tuman", "sam": f"Region-{c}sam",
        "sut": f"Sut 1L-{c}", "non": f"Non-{c}", "qatiq": f"Qatiq-{c}",
    }


def catalog_products(d) -> tuple:
    return d["sut"], d["non"], d["qatiq"]


def create_catalog_seed(page, d) -> None:
    """Regionlar (city → tuman «Области» orqali, sam); Alfa (city+tuman+sam) + user; Gamma
    (tuman) va Epsilon (sam) + userlar + hamkorlik; Sut/Non/Qatiq; omborlar TSH (city), SAM (sam)."""
    c = d["c"]
    with allure.step(f"Seed (admin): refs, Manufacturer, regionlar {d['city']} → {d['tuman']}, {d['sam']}"):
        authorization(page)
        ensure_refs(page, c)
        run_manufacturer(page, c)
        run_region(page, f"{c}city")
        run_region(page, f"{c}sam")
        create_child_region(page, d["city"], d["tuman"])
    common = dict(ownership=f"MCHJ-{c}", industry=f"Industry-{c}")
    with allure.step(f"Seed (admin): Alfa {d['supplier']} + user, Gamma/Epsilon + userlar, hamkorlik"):
        run_supplier(page, c, region=d["city"], extra_regions=(d["tuman"], d["sam"]), **common)
        run_supplier_user(page, c)
        for client_code, region in ((d["gamma"], d["tuman"]), (d["epsilon"], d["sam"])):
            run_client(page, client_code, region=region, **common)
            run_client_user(page, client_code)
        for client_code in (d["gamma"], d["epsilon"]):
            run_cooperation(page, c, supplier_name=d["supplier"], client_name=f"client-{client_code}")
    with allure.step(f"Seed (admin): tovarlar {', '.join(catalog_products(d))} ({d['category']}) + narx"):
        for name in catalog_products(d):
            run_product(page, c, manufacturer=f"Manufacturer-{c}", industry=f"Industry-{c}",
                        category=d["category"], name=name)
            run_product_linking(page, c, product_name=name)
    with allure.step(f"Seed (Alfa): «{TSH_NAME}» ({d['city']}), «{SAM_NAME}» ({d['sam']})"):
        login_supplier_user(page, c)
        create_warehouse(page, TSH_NAME, TSH_CODE, d["city"])
        create_warehouse(page, SAM_NAME, SAM_CODE, d["sam"])


def set_catalog_state(page, d, *, binds: dict, stock: dict, regions: dict | None = None) -> None:
    """Web (Alfa): ombor regionlari (default TSH=city, SAM=sam), bog'lanishlar, «В наличие»."""
    regions = regions or {TSH_NAME: {d["city"]}, SAM_NAME: {d["sam"]}}
    universe = (d["city"], d["tuman"], d["sam"])
    with allure.step(f"Holat (web, Alfa): regionlar {regions}; bog'lanishlar {binds}; В наличие {stock}"):
        login_supplier_user(page, d["c"])
        for warehouse, want in regions.items():
            set_warehouse_regions(page, warehouse, want, universe)
        set_binds(page, binds, catalog_products(d))
        for product, want in stock.items():
            set_in_stock(page, product, want)
