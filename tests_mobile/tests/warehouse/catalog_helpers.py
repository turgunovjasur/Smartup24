"""S-05 mobil katalog yordamchilari (test emas): mobil login, katalogda tovar ko'rinishini
o'qish, katalog guruhining umumiy seed'i (web UI) va har keys boshidagi holat (API).

«Yo'q» natijasi FAQAT yuklanganlik tasdiqlangandan keyin (soxta PASS bo'lmasin):
  «Категории» tabi umuman yo'q (tablar yuklangan) / kategoriya yo'q / ro'yxat yuklangan
  (tovar kartalari yoki «Ничего не найдено!»).
"""
import re

import allure
from playwright.sync_api import Page, expect

from flows.flow_authorization import COMPANY_CODE, authorization
from flows.flow_navbar import flow_navigate
from tests.sbr.supplier.warehouse.seed_api import (
    seed_clients, seed_products, seed_reference_data, seed_supplier, seed_warehouses,
)
from tests.sbr.supplier.warehouse.warehouse_api import WarehouseApi
from tests.sbr.supplier.warehouse.warehouse_helpers import (
    SAM_CODE, SAM_NAME, TSH_CODE, TSH_NAME, login_admin, login_supplier_user,
)
from utils.base_page import BasePage
from tests_mobile.config import WEB_USER_PASSWORD
from tests_mobile.screens.cart_screen import CartScreen
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


def stock_view(driver, client_code, supplier, category, product) -> dict:
    """Mobil: ``product`` qoldig'i — kartada ("list"), tovar sahifasida ("info") va savat
    qatorida ("basket"); ko'rsatilmasa None (0 emas). Savat oxirida bo'shatiladi."""
    mobile_login(driver, client_code)
    cs, cart = CatalogScreen(driver), CartScreen(driver)
    cart.clear()                     # oldingi run qoldig'i savat qatorini chalg'itmasin
    try:
        cs.open_supplier(supplier, require_categories=False)
        # catalog_view bilan bir xil yo'l: tablar va kategoriya kartasi yuklangach bosiladi
        assert cs.supplier_has_categories(), f"{supplier}: «Категории» tabi yo'q — shart bajarilmagan"
        assert cs.find_category(category), f"{category} supplier sahifasida yo'q"
        assert cs.open_category_listing(category), f"{category} bo'sh — shart bajarilmagan"
        view = {"list": cs.card_stock(product)}
        cs.add_to_cart(product)
        cs.open_product(product)
        view["info"] = cs.page_stock()
        cart.open()
        view["basket"] = cart.row_stock(product)
    finally:
        cart.clear()
    allure.attach(f"client_user-{client_code}: {product} qoldig'i {view}", name=f"qoldiq client-{client_code}",
                  attachment_type=allure.attachment_type.TEXT)
    return view


def expect_in_view(view, client_code, *, present=(), absent=()) -> None:
    """``present`` tovarlar ko'rinishi, ``absent`` lar ko'rinmasligi shart."""
    for p in present:
        assert view[p], f"client-{client_code} katalogida '{p}' YO'Q (kutilgan: bor). Ko'rinish: {view}"
    for p in absent:
        assert not view[p], f"client-{client_code} katalogida '{p}' BOR (kutilgan: yo'q). Ko'rinish: {view}"


# ── katalog guruhi: umumiy seed (web) va har keys boshidagi holat (API, Alfa) ─────────
def catalog_names(code) -> dict:
    """Seed nomlari ({code}11): shahar → tuman regionlari, Alfa/Gamma/Epsilon, 3 tovar."""
    return {
        "c": code, "supplier": f"supplier-{code}", "supplier_user": f"supplier_user-{code}", "category": f"Category-{code}",
        "gamma": f"{code}g", "epsilon": f"{code}e",
        "city": f"Region-{code}city", "tuman": f"Region-{code}tuman", "sam": f"Region-{code}sam",
        "sut": f"Sut 1L-{code}", "non": f"Non-{code}", "qatiq": f"Qatiq-{code}",
    }


def catalog_products(seed) -> tuple:
    return seed["sut"], seed["non"], seed["qatiq"]


def create_catalog_seed(page, seed) -> None:
    """Regionlar (city → tuman «Области» orqali, sam); Alfa (city+tuman+sam) + user; Gamma
    (tuman) va Epsilon (sam) + userlar + hamkorlik; Sut/Non/Qatiq; omborlar TSH (city), SAM (sam)."""
    c = seed["c"]
    with allure.step(f"Seed (admin): refs, Manufacturer, regionlar {seed['city']} → {seed['tuman']}, {seed['sam']}"):
        authorization(page)
        seed_reference_data(page, c, regions=(f"{c}city", f"{c}sam"), children=((seed["city"], seed["tuman"]),))
    common = dict(ownership=f"MCHJ-{c}", industry=f"Industry-{c}")
    with allure.step(f"Seed (admin): Alfa {seed['supplier']} + user, Gamma/Epsilon + userlar, hamkorlik"):
        seed_supplier(page, c, region=seed["city"], extra_regions=(seed["tuman"], seed["sam"]), **common)
        seed_clients(page, c, seed["supplier"], ((seed["gamma"], seed["tuman"]), (seed["epsilon"], seed["sam"])),
                     **common)
    with allure.step(f"Seed (admin): tovarlar {', '.join(catalog_products(seed))} ({seed['category']}) + narx"):
        seed_products(page, c, seed["category"], catalog_products(seed))
    with allure.step(f"Seed (Alfa): «{TSH_NAME}» ({seed['city']}), «{SAM_NAME}» ({seed['sam']})"):
        login_supplier_user(page, c)
        seed_warehouses(page, c, ((TSH_NAME, TSH_CODE, seed["city"]), (SAM_NAME, SAM_CODE, seed["sam"])))


def _api_regions(api: WarehouseApi, warehouse, names) -> None:
    """Ombor regionlari AYNAN ``names`` (edit$save region_id — string ID massivi)."""
    wid = api.warehouse_id(warehouse)
    want = sorted(api.region_ids(*names)) if names else []
    model = api.edit_model(wid)
    if sorted(map(str, model["region_id"] or [])) != want:
        r = api.edit_save(model, region_id=want)
        assert r.status_code == 200, f"«{warehouse}» edit$save → HTTP {r.status_code}: {r.text[:300]}"
    have = sorted(map(str, api.edit_model(wid)["region_id"] or []))
    assert have == want, f"«{warehouse}» regionlari {have}, kutilgan {want} ({sorted(names)})"


def _api_binds(api: WarehouseApi, warehouse, want, products) -> None:
    """``products`` doirasida ombor bog'lanishlari AYNAN ``want``: ortiqchasi detach,
    yetishmagani attach (yangi bog'lanish avail N)."""
    wid = api.warehouse_id(warehouse)

    def _attached() -> dict:
        return {p["name"]: str(p["product_id"]) for p in api.products(wid, "Y") if p["name"] in products}

    have = _attached()
    extra, missing = sorted(set(have) - set(want)), sorted(set(want) - set(have))
    if extra:
        r = api.detach(wid, *(have[p] for p in extra))
        assert r.status_code == 200, f"«{warehouse}» $detach {extra} → HTTP {r.status_code}: {r.text[:300]}"
    if missing:
        r = api.attach(wid, *(api.product_id(wid, p, attached="N") for p in missing))
        assert r.status_code == 200, f"«{warehouse}» $attach {missing} → HTTP {r.status_code}: {r.text[:300]}"
    have = set(_attached())
    assert have == set(want), f"«{warehouse}» bog'lanishlari {sorted(have)}, kutilgan {sorted(want)}"


def _api_stock(api: WarehouseApi, product, want: bool) -> None:
    """Tovar «В наличие» Y/N: supplier tovari va uning BARCHA ombor bog'lanishlari."""
    flag = "Y" if want else "N"

    def _state() -> tuple:
        binds = {w["name"]: p["avail"] for w in api.warehouses()
                 for p in api.products(str(w["warehouse_id"]), "Y", product)}
        return api.supplier_product(product), binds

    info, binds = _state()
    if info["avail"] != flag or any(a != flag for a in binds.values()):
        api.change_avail(str(info["product_id"]), flag)
        info, binds = _state()
    assert info["avail"] == flag and all(a == flag for a in binds.values()), \
        f"{product}: avail={info['avail']}, omborlarda {binds} (kutilgan hammasi {flag})"


def set_catalog_state(page, seed, *, binds: dict, stock: dict, regions: dict | None = None) -> None:
    """API (Alfa, ``WarehouseApi``): ombor regionlari (default TSH=city, SAM=sam),
    bog'lanishlar, «В наличие» — idempotent, har qismi qo'llangach qayta o'qib tasdiqlanadi
    (server begona/noma'lum ID'da jim 200 qaytarishi mumkin). ``page`` ishlatilmaydi —
    chaqiruvlar mos qolishi uchun saqlangan; web seans holatiga tegilmaydi."""
    regions = regions or {TSH_NAME: {seed["city"]}, SAM_NAME: {seed["sam"]}}
    products = catalog_products(seed)
    with allure.step(f"Holat (API, Alfa): regionlar {regions}; bog'lanishlar {binds}; В наличие {stock}"):
        api = WarehouseApi(f"supplier_user-{seed['c']}@{COMPANY_CODE}")
        try:
            for warehouse, names in regions.items():
                _api_regions(api, warehouse, names)
            for warehouse, want in binds.items():
                _api_binds(api, warehouse, want, products)
            for product, want in stock.items():
                _api_stock(api, product, want)
        finally:
            api.logout()


# ── «Кому показывать остатки» (Модератор → Поставщик → Настройки → Основное) ─────────────
# DEV DOM (probe 2026-10-19): label «Кому показывать остатки» → ``smt-control`` ichida
# ``smt-multi-data-select`` (smtid YO'Q; smtkeyfield=person_id), filtr input placeholder «Поиск»,
# variantlar ``[role=menuitemcheckbox]``; tanlangan mijoz ``smt-tag`` chipi, olib tashlash
# ``button[aria-label="Remove this tag"]``. «Сохранить» formani YOPMAYDI (view'da qoladi) —
# saqlash ``supplier/setting$save_setting`` POST 200 bilan tasdiqlanadi.
STOCK_VISIBLE_LABEL = "Кому показывать остатки"
# «Системный пользователь *» — MAJBURIY ``smt-data-select`` (smtid YO'Q, smtkeyfield=user_id,
# placeholder «Выберите...», variant matni = user nomi). Yangi supplier'da bo'sh — forma jim
# bloklaydi, save_setting so'rovi KETMAYDI (MCP tasdiqlangan 2026-10-19).
SYSTEM_USER_LABEL = "Системный пользователь"


def _stock_visible_field(page: Page):
    label = page.locator("label").filter(has_text=re.compile(rf"^\s*{STOCK_VISIBLE_LABEL}\s*$"))
    return page.locator("smt-control").filter(has=label).last


def _system_user_input(page: Page):
    label = page.locator("label").filter(has_text=re.compile(rf"^\s*{SYSTEM_USER_LABEL}\s*\*?\s*$"))
    return page.locator("smt-control").filter(has=label).last.locator("smt-data-select input").first


def _open_supplier_settings(page: Page, supplier) -> BasePage:
    """Модератор → Поставщики → supplier → Просмотреть → Настройки → Основное (model yuklangach)."""
    m = BasePage(page)
    flow_navigate(page, tab="Модератор", name="Поставщики")
    m.expect_heading("Поставщики")
    m.search(supplier)
    m.click_grid_row(supplier)
    m.click_button("Просмотреть", expect_heading="Поставщик (Просмотр)")
    # Chiplar setting:model javobidan keyin chiziladi — javobni kutmasak bo'sh ro'yxat o'qiladi
    with page.expect_response(lambda r: "supplier/setting:model" in r.url):
        m.click_button("Настройки")
    m.settle()
    page.get_by_role("button", name="Основное", exact=True).last.click()
    m.settle()
    expect(_stock_visible_field(page)).to_be_visible()
    return m


def _stock_visible_names(page: Page) -> set:
    return {t.strip() for t in _stock_visible_field(page).locator("smt-tag").all_inner_texts()}


def set_stock_visible(page: Page, supplier, clients, system_user) -> None:
    """Admin: supplier «Кому показывать остатки» ro'yxatini aynan ``clients`` (mijoz nomlari)
    ga keltiradi, saqlaydi va qayta ochib tekshiradi. «Системный пользователь» bo'sh bo'lsa
    (yangi supplier) ``system_user`` tanlanadi — aks holda forma saqlanmaydi; to'la bo'lsa tegilmaydi."""
    want = set(clients)
    with allure.step(f"Admin: {supplier} → Настройки → Основное → «{STOCK_VISIBLE_LABEL}» = {sorted(want) or 'bo‘sh'}"):
        login_admin(page)
        m = _open_supplier_settings(page, supplier)
        have = _stock_visible_names(page)
        if have != want:
            if not _system_user_input(page).input_value().strip():
                m.select(system_user, label=SYSTEM_USER_LABEL)
            field = _stock_visible_field(page)
            for name in sorted(have - want):
                tag = field.locator("smt-tag").filter(has_text=re.compile(rf"^\s*{re.escape(name)}\s*$"))
                tag.get_by_role("button", name="Remove this tag").click()
                expect(tag).to_have_count(0)
            for name in sorted(want - have):
                m.select(name, label=STOCK_VISIBLE_LABEL)
            with page.expect_response(lambda r: "supplier/setting$save_setting" in r.url) as resp:
                m.click_button("Сохранить")
            assert resp.value.status == 200, \
                f"setting$save_setting → HTTP {resp.value.status}: {resp.value.text()[:300]}"
            m.wait_for_loader()
            _open_supplier_settings(page, supplier)
        tags = _stock_visible_field(page).locator("smt-tag")
        expect(tags).to_have_count(len(want))
        for name in want:
            expect(tags.filter(has_text=name)).to_have_count(1)
