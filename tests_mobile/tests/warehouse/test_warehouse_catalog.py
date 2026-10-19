"""S-05 mobil katalog (c:exp_product_list): 4.1, 2.2 (mobil), 4.2, 3.1 (mobil), 3.3, 4.3, 4.4.
Web zakaz katalogi ombor regionini filtrlamaydi — katalog MOBILDA tekshiriladi.
Har test boshida kerakli holat (ombor regionlari, bog'lanishlar, «В наличие») o'rnatiladi —
oldingi test yiqilsa ham keyingisi mustaqil. Seed: conftest.py (``S05_MOBILE_SEED``).
UI cheklovi: «Изменить наличие» tovarning BARCHA omborlarini birdan o'zgartiradi — 4.2 dagi
«Toshkentda Sut N» = Sut Toshkent omboriga biriktirilmagan (katalog uchun bir xil).
Test-case: docs/qa/test-cases/sbr/supplier/warehouse.md."""
import allure
import pytest
from playwright.sync_api import Page

from tests.sbr.supplier.warehouse.warehouse_helpers import (
    DEFAULT_WAREHOUSE, SAM_NAME, TSH_NAME, attach_product, detach_product, known_bug,
    login_supplier_user, set_in_stock,
)
from tests_mobile.screens.catalog_screen import CatalogScreen
from tests_mobile.tests.warehouse.catalog_helpers import (
    catalog_products, catalog_view, expect_in_view, mobile_login, set_catalog_state, set_stock_visible,
    stock_view,
)

pytestmark = [pytest.mark.mobile, allure.epic("Supplier"), allure.feature("S-05 Склады")]

REASON_SUPPLIER_DUP = "SMAR24-1063: c:exp_product_supplier_list — Alfa ikki marta (ombor qatorlari bilan join, distinct yo'q)"


def _view(driver, d, client_code) -> dict:
    return catalog_view(driver, client_code, d["supplier"], d["category"], catalog_products(d))


@allure.id("S-05.4.1")
@allure.story("Katalogda ko'rinish — avail Y kamida bitta omborda")
@allure.title("S-05.4.1 — Katalogda faqat «В наличие» tovarlar ko'rinadi")
@allure.tag("effect")
def test_catalog_shows_only_available_products(session_page: Page, driver, catalog_seed) -> None:
    """Sut (TSH+SAM Y), Non (TSH Y), Qatiq (TSH N). Kutilgan: Gamma — Sut, Non bor; Qatiq yo'q."""
    d = catalog_seed
    set_catalog_state(session_page, d,
                      binds={TSH_NAME: {d["sut"], d["non"], d["qatiq"]}, SAM_NAME: {d["sut"]}, DEFAULT_WAREHOUSE: set()},
                      stock={d["sut"]: True, d["non"]: True, d["qatiq"]: False})
    with allure.step("Kutilgan (Gamma): Sut, Non — bor; Qatiq — yo'q"):
        expect_in_view(_view(driver, d, d["gamma"]), d["gamma"],
                       present=(d["sut"], d["non"]), absent=(d["qatiq"],))


@allure.id("S-05.2.2")
@allure.story("Regionlar — multiselect, daraxt (mobil qismi)")
@allure.title("S-05.2.2 (mobil) — Shahar ombori tumandagi mijozni qamraydi")
@allure.tag("effect")
def test_catalog_city_warehouse_covers_district(session_page: Page, driver, catalog_seed) -> None:
    """Non faqat shahar regionli «Toshkent ombori»da. Kutilgan: tumandagi Gamma Non'ni ko'radi."""
    d = catalog_seed
    set_catalog_state(session_page, d,
                      binds={TSH_NAME: {d["non"]}, SAM_NAME: set(), DEFAULT_WAREHOUSE: set()},
                      stock={d["non"]: True})
    with allure.step(f"Kutilgan: Gamma ({d['tuman']}, {d['city']} ichida) {d['non']}'ni ko'radi"):
        expect_in_view(_view(driver, d, d["gamma"]), d["gamma"], present=(d["non"],))


@allure.id("S-05.4.2")
@allure.story("Ombor regionlari — mijoz regioni bo'yicha filtr")
@allure.title("S-05.4.2 — Katalog ombor regioni bo'yicha filtrlanadi")
@allure.tag("effect", "boundary")
def test_catalog_filters_by_warehouse_region(session_page: Page, driver, catalog_seed) -> None:
    """TSH: Non; SAM: Sut; standart (regionsiz): Qatiq — hammasi Y. Kutilgan: Gamma — Non, Qatiq,
    Sut yo'q; Epsilon — Sut, Qatiq, Non yo'q; regionlar olib tashlansa ikkalasi hamma tovar."""
    d = catalog_seed
    binds = {TSH_NAME: {d["non"]}, SAM_NAME: {d["sut"]}, DEFAULT_WAREHOUSE: {d["qatiq"]}}
    set_catalog_state(session_page, d, binds=binds,
                      stock={d["sut"]: True, d["non"]: True, d["qatiq"]: True})
    with allure.step("Gamma: Non (a — shahar ombori tumanni qamraydi), Qatiq (b — regionsiz ombor), Sut yo'q"):
        expect_in_view(_view(driver, d, d["gamma"]), d["gamma"],
                       present=(d["non"], d["qatiq"]), absent=(d["sut"],))
    with allure.step("Epsilon: Sut, Qatiq bor; Non yo'q"):
        expect_in_view(_view(driver, d, d["epsilon"]), d["epsilon"],
                       present=(d["sut"], d["qatiq"]), absent=(d["non"],))
    set_catalog_state(session_page, d, binds=binds, stock={}, regions={TSH_NAME: set(), SAM_NAME: set()})
    for who in ("gamma", "epsilon"):
        with allure.step(f"(c) Barcha omborlar regionsiz — eski filtr: {who} hamma tovarni ko'radi"):
            expect_in_view(_view(driver, d, d[who]), d[who], present=catalog_products(d))


@allure.id("S-05.3.1")
@allure.story("Прикрепленные / Доступные (mobil qismi)")
@allure.title("S-05.3.1 (mobil) — Yangi biriktirilgan va olib tashlangan tovar katalogda ko'rinmaydi")
@allure.tag("crud", "effect")
def test_catalog_hides_new_and_detached_products(session_page: Page, driver, catalog_seed) -> None:
    """Qatiq TSH'ga biriktiriladi (avail N), keyin Non TSH'dan olib tashlanadi.
    Kutilgan: Qatiq katalogda hali ko'rinmaydi; Non katalogdan yo'qoladi."""
    d = catalog_seed
    set_catalog_state(session_page, d,
                      binds={TSH_NAME: {d["sut"], d["non"]}, SAM_NAME: set(), DEFAULT_WAREHOUSE: set()},
                      stock={d["sut"]: True, d["non"]: True})
    with allure.step("Shart nazorati: Gamma katalogida Non bor"):
        expect_in_view(_view(driver, d, d["gamma"]), d["gamma"], present=(d["non"],))
    with allure.step(f"Alfa: {TSH_NAME} → Доступные → {d['qatiq']} → Прикрепить → Да (avail N)"):
        login_supplier_user(session_page, d["c"])
        attach_product(session_page, TSH_NAME, d["qatiq"])
    with allure.step(f"Gamma: {d['qatiq']} katalogda hali ko'rinmaydi"):
        expect_in_view(_view(driver, d, d["gamma"]), d["gamma"], absent=(d["qatiq"],))
    with allure.step(f"Alfa: Прикрепленные → {d['non']} → Открепить → Да"):
        login_supplier_user(session_page, d["c"])
        detach_product(session_page, TSH_NAME, d["non"])
    with allure.step(f"Gamma: {d['non']} katalogdan yo'qoladi (boshqa omborda yo'q)"):
        expect_in_view(_view(driver, d, d["gamma"]), d["gamma"], absent=(d["non"],))


@allure.id("S-05.3.3")
@allure.story("«Изменить наличие»")
@allure.title("S-05.3.3 — «Изменить наличие» katalogda darhol aks etadi")
@allure.tag("effect")
def test_catalog_follows_change_avail(session_page: Page, driver, catalog_seed) -> None:
    """Qatiq → Да; Sut → Нет; Sut → Да. Kutilgan: Qatiq paydo bo'ladi; Sut yo'qoladi, keyin qaytadi."""
    d = catalog_seed
    set_catalog_state(session_page, d,
                      binds={TSH_NAME: {d["sut"], d["qatiq"]}, SAM_NAME: {d["sut"]}, DEFAULT_WAREHOUSE: set()},
                      stock={d["sut"]: True, d["qatiq"]: False})
    for product, avail, present, absent in ((d["qatiq"], True, (d["qatiq"],), ()),
                                            (d["sut"], False, (), (d["sut"],)),
                                            (d["sut"], True, (d["sut"],), ())):
        with allure.step(f"Alfa: Товары → {product} → Изменить наличие → {'Да' if avail else 'Нет'}"):
            login_supplier_user(session_page, d["c"])
            set_in_stock(session_page, product, avail)
        with allure.step(f"Gamma: {product} {'ko‘rinadi' if avail else 'yo‘qoladi'}"):
            expect_in_view(_view(driver, d, d["gamma"]), d["gamma"], present=present, absent=absent)


@allure.id("S-05.4.3")
@allure.story("c:exp_product_supplier_list — regionsiz va dublikat")
@allure.title("S-05.4.3 — Tovar sahifasida yetkazib beruvchi bir marta chiqadi")
@allure.tag("effect", "bug-candidate")
def test_product_suppliers_listed_once(session_page: Page, driver, catalog_seed) -> None:
    """Sut Toshkent va Samarqand omborlarida Y. Gamma: tovar sahifasi → «Другие поставщики».
    Kutilgan: Alfa bir marta."""
    d = catalog_seed
    set_catalog_state(session_page, d,
                      binds={TSH_NAME: {d["sut"]}, SAM_NAME: {d["sut"]}, DEFAULT_WAREHOUSE: set()},
                      stock={d["sut"]: True})
    with allure.step(f"Gamma-user: {d['supplier']} → {d['category']} → {d['sut']} → «Другие поставщики»"):
        # Navigatsiya xatolari oddiy FAIL — xfail faqat pastdagi bag assertion'ida (known_bug)
        mobile_login(driver, d["gamma"])
        cs = CatalogScreen(driver)
        cs.open_supplier(d["supplier"], require_categories=False)
        # catalog_view bilan bir xil yo'l: tablar va kategoriya kartasi yuklangach bosiladi
        assert cs.supplier_has_categories(), f"{d['supplier']}: «Категории» tabi yo'q — shart bajarilmagan"
        assert cs.find_category(d["category"]), f"{d['category']} supplier sahifasida yo'q"
        assert cs.open_category_listing(d["category"]), f"{d['category']} bo'sh — shart bajarilmagan"
        cs.open_product(d["sut"])
        count = cs.supplier_offers(d["supplier"])
        allure.attach(str(count), name=f"{d['supplier']} qatorlari soni",
                      attachment_type=allure.attachment_type.TEXT)
    with allure.step("Kutilgan: Alfa bir marta"):
        with known_bug(REASON_SUPPLIER_DUP):
            assert count == 1, f"{d['supplier']} «Изменить поставщика» ro'yxatida {count} marta"


@allure.id("S-05.4.4")
@allure.story("stock_quantity — faqat ruxsat etilgan mijozga, barcha omborlar yig'indisi")
@allure.title("S-05.4.4 — Qoldiq faqat ruxsat etilgan mijozga, barcha omborlar yig'indisi")
@allure.tag("effect", "access")
def test_stock_visible_only_to_allowed_client(session_page: Page, driver, catalog_seed) -> None:
    """Sut Toshkent va Samarqand omborlarida «В наличие»; «Кому показывать остатки» = [Gamma].
    Kutilgan: Gamma qoldiqni barcha omborlar yig'indisi sifatida ko'radi (regiondan qat'i nazar —
    Gamma regionini faqat Toshkent ombori qamraydi); Epsilon qoldiqni umuman ko'rmaydi (0 ham
    emas); ro'yxat bo'shatilsa Gamma ham ko'rmaydi.
    UI cheklovi: aniq qoldiq (100 / 50) qo'yib bo'lmaydi — «Изменить наличие» har omborga
    1 000 000 yozadi, shuning uchun kutilgan yig'indi 2 × 1 000 000 (kartada — c:exp_product_list,
    tovar sahifasida — c:exp_product_info, savat qatorida — c:exp_basket_headers_info).
    Savat har mijoz tekshiruvidan keyin bo'shatiladi."""
    d = catalog_seed
    expected = 2 * 1_000_000
    gamma_client = f"client-{d['gamma']}"
    set_catalog_state(session_page, d,
                      binds={TSH_NAME: {d["sut"]}, SAM_NAME: {d["sut"]}, DEFAULT_WAREHOUSE: set()},
                      stock={d["sut"]: True})

    def _stock(client_code) -> dict:
        return stock_view(driver, client_code, d["supplier"], d["category"], d["sut"])

    emptied = False
    try:
        set_stock_visible(session_page, d["supplier"], {gamma_client}, d["supplier_user"])
        with allure.step(f"Gamma (ruxsat etilgan): {d['sut']} qoldig'i = 2 000 000 (TSH + SAM)"):
            view = _stock(d["gamma"])
            assert view == dict.fromkeys(("list", "info", "basket"), expected), \
                f"Gamma qoldig'i {view} (kutilgan: kartada, tovar sahifasida va savatda {expected})"
        with allure.step(f"Epsilon (ruxsatsiz): {d['sut']} qoldig'i umuman ko'rsatilmaydi (0 ham emas)"):
            view = _stock(d["epsilon"])
            assert view == dict.fromkeys(("list", "info", "basket")), f"Epsilon qoldiqni ko'rmoqda: {view}"
        set_stock_visible(session_page, d["supplier"], set(), d["supplier_user"])
        emptied = True
        with allure.step("Ro'yxat bo'sh: Gamma ham qoldiqni ko'rmaydi"):
            view = _stock(d["gamma"])
            assert view == dict.fromkeys(("list", "info", "basket")), \
                f"Ro'yxat bo'sh, lekin Gamma qoldiqni ko'rmoqda: {view}"
    finally:
        # Assert yiqilsa ham ro'yxat bo'sh qolsin — boshqa keyslar qoldiq ko'rinishiga bog'lanmasin
        if not emptied:
            set_stock_visible(session_page, d["supplier"], set(), d["supplier_user"])
