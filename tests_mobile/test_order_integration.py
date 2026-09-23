"""WEB + MOBIL INTEGRATSIYA testi — to'liq End-to-End zakaz oqimi.

G'OYA
-----
Real hayotdagi oqim: back-office'da (WEB) hamma narsa tayyorlanadi, xaridor
esa MOBIL ilovadan buyurtma beradi. Shuni aynan takrorlaymiz — bitta pytest
chaqiruvида, bitta session'da UCH faza:

    FAZA 1 (web, Playwright)   →   FAZA 2 (mobil, Appium)   →   FAZA 3 (web)
    admin: supplier, supplier      client_user bilan            supplier_user bilan
    user, client, client user,     mobil ilovaga kirib          Заказы'da o'sha
    product, hamkorlik, narx,      ZAKAZ beradi                 zakaz statusini
    В наличие (reuse group_a)                                   o'zgartiradi (reuse)
            │                            ▲
            └────── runner_state ────────┘   (product_name; login `code` dan quriladi)

NEGA BITTA SESSION ISHLAYDI
---------------------------
Root `conftest.py` butun loyihaga tegishli → mobil testlar ham `code`,
`runner_state`, `session_page` fixturelarini ko'radi. Web+mobil bitta pytest
chaqiruvида yugursa `code` IKKALASI uchun bir xil bo'ladi — shuning uchun mobil
faza login'ni `client_user-{code}8@{COMPANY_CODE}` deb O'ZI hisoblaydi, alohida
bridge fayl kerak emas. Yaratilgan tovar nomi `runner_state` orqali uzatiladi.

WEB SEED = REUSE
----------------
supplier/client/user/hamkorlik/product/narx/В наличие QAYTA yozilmaydi — mavjud
`tests/test_group_a/` va `tests/test_setup/` run_* funksiyalari CHAQIRILADI.
Web zakaz (run_order) UMUMAN chaqirilmaydi — zakaz mobilга ko'chdi. Web zakaz
regressiyasi `tests/test_group_a/test_all_group_a.py`da o'z holicha qoladi.

ISHGA TUSHIRISH (telefon + Appium SHART — bu bo'lim CI cron'ida EMAS, lokal)
    appium --address 127.0.0.1 --port 4723      # alohida terminal
    .venv\\Scripts\\python -m pytest tests_mobile/test_order_integration.py -v -s

HOLAT: real telefonda 3/3 YASHIL (2026-09-23, dev sm24, ~5.5 min).
"""
import allure
from playwright.sync_api import Page

from flows.flow_authorization import COMPANY_CODE, authorization, logout

# ── WEB SEED — mavjud run_* funksiyalar (REUSE, qayta yozilmaydi) ────────────
from tests.test_setup.test_manufacturer import run_manufacturer as setup_manufacturer
from tests.test_setup.test_industry import run_industry as setup_industry
from tests.test_setup.test_category import run_category as setup_category
from tests.test_setup.test_region import run_region as setup_region
from tests.test_setup.test_form_of_ownership import run_form_of_ownership as setup_ownership
from tests.test_group_a.test_supplier import run_supplier as ga_supplier
from tests.test_group_a.test_client import run_client as ga_client
from tests.test_group_a.test_supplier_user import run_supplier_user as ga_supplier_user
from tests.test_group_a.test_client_user import run_client_user as ga_client_user
from tests.test_group_a.test_cooperation import run_cooperation as ga_cooperation
from tests.test_group_a.test_product import run_product as ga_product
from tests.test_group_a.test_product_linking import run_product_linking as ga_product_linking
from tests.test_group_a.test_order_status_change import run_order_status_change as ga_order_status, \
    run_order_status_change

# ── MOBIL ekran-obyektlari ───────────────────────────────────────────────────
from tests_mobile.pages.login_screen import LoginScreen
from tests_mobile.pages.order_screen import OrderScreen


def _code(code) -> str:
    """Integratsiya bo'limi kod varianti — boshqa bo'limlar (setup=code,
    group_a={code}2, regression={code}3, ...) bilan to'qnashmaslik uchun {code}8."""
    return f"{code}8"


# ══════════════════════════════════════════════════════════════════════════════
# FAZA 1 — WEB SEED (admin nomidan barcha ma'lumot tayyorlanadi)
# ══════════════════════════════════════════════════════════════════════════════
@allure.epic("Web+Mobil E2E")
@allure.feature("Faza 1 — Web seed")
@allure.title("Web seed: supplier/client/userlar/hamkorlik/tovar/narx/В наличие")
def test_100_web_seed(session_page: Page, code, runner_state) -> None:
    """Zakaz uchun kerakli hamma narsani WEB'да yaratadi (mavjud run_* reuse).
    Oxirida biriktirilgan tovar nomi `runner_state`ga yoziladi — mobil faza shuni
    zakazga qo'shadi."""
    c = _code(code)
    authorization(session_page)

    with allure.step("Ma'lumotnomalar: Регион / Форма собственности / Отрасль / Производитель / Категория"):
        setup_region(session_page, c)
        setup_ownership(session_page, c)
        setup_industry(session_page, c)
        setup_manufacturer(session_page, c)
        setup_category(session_page, c)

    with allure.step("Поставщик va Клиент"):
        ga_supplier(session_page, c, region=f"Region-{c}", ownership=f"MCHJ-{c}", industry=f"Industry-{c}")
        ga_client(session_page, c, region=f"Region-{c}", ownership=f"MCHJ-{c}", industry=f"Industry-{c}")

    with allure.step("Пользователи: поставщик + клиент (login uchun rollari bilan)"):
        ga_supplier_user(session_page, c)
        ga_client_user(session_page, c)

    with allure.step("Сотрудничество: hamkorlik so'rovi + tasdiqlash"):
        ga_cooperation(session_page, c)

    with allure.step("Товар: yaratish → biriktirish → В наличие → narx"):
        product_name = ga_product(
            session_page, c,
            manufacturer=f"Manufacturer-{c}", industry=f"Industry-{c}", category=f"Category-{c}",
        )
        product_name = ga_product_linking(session_page, c, product_name=product_name)
        runner_state["int_product_name"] = product_name


# ══════════════════════════════════════════════════════════════════════════════
# FAZA 2 — MOBIL ZAKAZ (web'да yaratilgan client_user bilan)
# ══════════════════════════════════════════════════════════════════════════════
@allure.epic("Web+Mobil E2E")
@allure.feature("Faza 2 — Mobil zakaz")
@allure.title("Mobil: client_user bilan kirib zakaz berish")
def test_200_mobile_order(driver, code, runner_state) -> None:
    """Web'да yaratilgan klient foydalanuvchisi bilan MOBIL ilovaga kirib zakaz
    beradi. Login `code` dan quriladi (web faza bilan bir xil session → bir xil
    `code`); tovar nomi Faza 1'dan `runner_state` orqali keladi."""
    c = _code(code)
    login = f"client_user-{c}@{COMPANY_CODE}"
    supplier_name = f"supplier-{c}"
    category = f"Category-{c}"
    product_name = runner_state.get("int_product_name") or f"product-{c}"

    login_screen = LoginScreen(driver)
    with allure.step(f"Mobil login: {login}"):
        login_screen.ensure_logged_out()
        login_screen.open_login_form()
        login_screen.submit_login(login, "1")
        assert login_screen.is_logged_in(), f"Mobil login muvaffaqiyatsiz: {login}"

    order = OrderScreen(driver)
    with allure.step(f"Zakaz: {supplier_name} / {category} / {product_name} / Наличные"):
        order.create_order(
            supplier_name=supplier_name, category=category, product_name=product_name, qty=1,
        )
        assert order.is_order_created(), "Mobil zakaz saqlanmadi"

    with allure.step("Zakaz ichига kirib ma'lumotlarни tekshirish"):
        order.open_last_order()
        order.verify_order(supplier_name, product_name, payment="Наличные")


# ══════════════════════════════════════════════════════════════════════════════
# FAZA 3 — WEB TEKSHIRUV (supplier_user zakaz statusini o'zgartiradi)
# ══════════════════════════════════════════════════════════════════════════════
@allure.epic("Web+Mobil E2E")
@allure.feature("Faza 3 — Web tekshiruv")
@allure.title("Web: supplier_user bilan mobil zakaz statusini o'zgartirish")
def test_300_web_status_change(session_page: Page, code) -> None:
    """Loop-close: mobil urgan zakaz backend'ga tushdimi — supplier_user bilan
    web'ga kirib Заказы'da topib statusini to'liq sikl bo'ylab o'zgartiramiz
    (run_order_status_change reuse).

    ⚠ TODO(device): run_order_status_change zanjiri Черновик statusidan
    boshlanadi (web zakaz shunday yaratardi). Mobil zakaz qaysi statusda
    tushishi QURILMADA tasdiqlansin — agar 'Новый' bo'lsa STATUS_CHAIN'ni
    moslashtirish kerak bo'ladi."""
    c = _code(code)
    logout(session_page)
    with allure.step(f"Web login: supplier_user-{c}@{COMPANY_CODE}"):
        authorization(session_page, email=f"supplier_user-{c}@{COMPANY_CODE}", password="1")
    run_order_status_change(session_page, c)
