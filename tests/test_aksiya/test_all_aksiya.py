"""АКЦИЯ bo'limi runneri — supplier "Акция" (aksiya) to'liq oqimi bitta seansda.

Bu bo'lim group_a'dan ALOHIDA (aralashib ketmasligi uchun): o'zi ma'lumotnoma +
supplier/client/userlar/hamkorlik/tovar setup'ini quradi (setup va group_a
``run_*`` funksiyalarini QAYTA ISHLATADI), so'ng aksiyaning to'liq CRUD'ini va
eng muhimi — yaratilgan aksiya bo'yicha zakaz urib, bonus (tekin tovar) HAQIQATAN
qo'llanganini Модератор → Продажи → Заказы ichida tekshiradi.

DIZAYN (test_all_group_a / test_all_main bilan bir xil)
------------------------------------------------------
- **Bitta seans / session_page.** ``test_000`` admin bilan kiradi; zakaz bosqichida
  klient user'ga, bonus tekshiruvida yana admin'ga rol almashadi.
- **Kod varianti ``{code}4``** — setup(code)/group_a({code}2)/regression({code}3)
  bilan nom to'qnashmasligi uchun.
- **O'zini ta'minlaydi.** Refs + supplier/client/... shu runnerда yaratiladi.

OQIM
----
setup refs → supplier/client/userlar/hamkorlik/tovar+narx+В наличие →
aksiya CREATE → VIEW → EDIT → DUBLIKAT(xato) → ZAKAZ(klient) →
BONUS tekshiruvi(admin, Продажи→Заказы) → STATUS → DELETE.

ISHGA TUSHIRISH
---------------
    python -m pytest tests/test_aksiya/test_all_aksiya.py -v
"""
import allure
from playwright.sync_api import Page

from flows.flow_authorization import COMPANY_CODE, authorization, logout

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
from tests.test_group_a.test_order import run_order as ga_order

from tests.test_aksiya.test_promotion import (
    run_promotion, run_promotion_view, run_promotion_edit,
    run_promotion_status, run_promotion_delete, run_promotion_duplicate,
    run_promotion_deactivate,
    verify_order_bonus, verify_no_order_bonus,
)


def _ak_code(code) -> str:
    """Акция bo'limi kod varianti — boshqa bo'limlar bilan to'qnashmaslik uchun {code}4."""
    return f"{code}4"


# ══════════════════════════════════════════════════════════════════════════════
# 0. LOGIN
# ══════════════════════════════════════════════════════════════════════════════
@allure.epic("Акция")
@allure.feature("Runner — seans")
@allure.title("Login — admin bilan bir marta kirish (butun aksiya runner uchun)")
def test_000_login_admin(session_page: Page) -> None:
    authorization(session_page)


# ══════════════════════════════════════════════════════════════════════════════
# I. SETUP — ma'lumotnomalar ({code}4)
# ══════════════════════════════════════════════════════════════════════════════
@allure.epic("Акция")
@allure.feature("Setup")
@allure.title("Setup: Регион")
def test_100_region(session_page: Page, code) -> None:
    setup_region(session_page, _ak_code(code))


@allure.epic("Акция")
@allure.feature("Setup")
@allure.title("Setup: Форма собственности")
def test_101_ownership(session_page: Page, code) -> None:
    setup_ownership(session_page, _ak_code(code))


@allure.epic("Акция")
@allure.feature("Setup")
@allure.title("Setup: Отрасль")
def test_102_industry(session_page: Page, code) -> None:
    setup_industry(session_page, _ak_code(code))


@allure.epic("Акция")
@allure.feature("Setup")
@allure.title("Setup: Производитель")
def test_103_manufacturer(session_page: Page, code) -> None:
    setup_manufacturer(session_page, _ak_code(code))


@allure.epic("Акция")
@allure.feature("Setup")
@allure.title("Setup: Категория")
def test_104_category(session_page: Page, code) -> None:
    setup_category(session_page, _ak_code(code))


# ══════════════════════════════════════════════════════════════════════════════
# II. SETUP — supplier/client, userlar, hamkorlik, tovar
# ══════════════════════════════════════════════════════════════════════════════
@allure.epic("Акция")
@allure.feature("Setup")
@allure.title("Setup: Поставщик")
def test_110_supplier(session_page: Page, code) -> None:
    ak = _ak_code(code)
    ga_supplier(session_page, ak, region=f"Region-{ak}", ownership=f"MCHJ-{ak}", industry=f"Industry-{ak}")


@allure.epic("Акция")
@allure.feature("Setup")
@allure.title("Setup: Клиент")
def test_111_client(session_page: Page, code) -> None:
    ak = _ak_code(code)
    ga_client(session_page, ak, region=f"Region-{ak}", ownership=f"MCHJ-{ak}", industry=f"Industry-{ak}")


@allure.epic("Акция")
@allure.feature("Setup")
@allure.title("Setup: Пользователь поставщика")
def test_112_supplier_user(session_page: Page, code) -> None:
    ga_supplier_user(session_page, _ak_code(code))


@allure.epic("Акция")
@allure.feature("Setup")
@allure.title("Setup: Пользователь клиента")
def test_113_client_user(session_page: Page, code) -> None:
    ga_client_user(session_page, _ak_code(code))


@allure.epic("Акция")
@allure.feature("Setup")
@allure.title("Setup: Запрос на сотрудничество")
def test_114_cooperation(session_page: Page, code) -> None:
    ga_cooperation(session_page, _ak_code(code))


@allure.epic("Акция")
@allure.feature("Setup")
@allure.title("Setup: Продукт")
def test_115_product(session_page: Page, code, runner_state) -> None:
    ak = _ak_code(code)
    product_name = ga_product(
        session_page, ak,
        manufacturer=f"Manufacturer-{ak}", industry=f"Industry-{ak}", category=f"Category-{ak}",
    )
    runner_state["ak_product_name"] = product_name


@allure.epic("Акция")
@allure.feature("Setup")
@allure.title("Setup: Прикрепление товара — narx + В наличие")
def test_116_product_linking(session_page: Page, code, runner_state) -> None:
    product_name = ga_product_linking(
        session_page, _ak_code(code), product_name=runner_state.get("ak_product_name"),
    )
    runner_state["ak_product_name"] = product_name


# ══════════════════════════════════════════════════════════════════════════════
# III. АКЦИЯ — CRUD (create → view → edit → dublikat)
# ══════════════════════════════════════════════════════════════════════════════
@allure.epic("Акция")
@allure.feature("CRUD")
@allure.title("Акция: Создание — 'buy 2 → 1 tekin'")
def test_200_promotion_create(session_page: Page, code, runner_state) -> None:
    ak = _ak_code(code)
    name = run_promotion(
        session_page, ak,
        supplier_name=f"supplier-{ak}",
        bonus_product=runner_state.get("ak_product_name"),
        case="qty_free",
    )
    runner_state["ak_promotion_name"] = name


@allure.epic("Акция")
@allure.feature("CRUD")
@allure.title("Акция: Просмотр")
def test_201_promotion_view(session_page: Page, code, runner_state) -> None:
    ak = _ak_code(code)
    run_promotion_view(
        session_page, supplier_name=f"supplier-{ak}",
        name=runner_state["ak_promotion_name"],
    )


@allure.epic("Акция")
@allure.feature("CRUD")
@allure.title("Акция: Редактирование — nom o'zgartirish")
def test_202_promotion_edit(session_page: Page, code, runner_state) -> None:
    ak = _ak_code(code)
    new_name = run_promotion_edit(
        session_page, supplier_name=f"supplier-{ak}",
        name=runner_state["ak_promotion_name"],
        new_name=f"{runner_state['ak_promotion_name']}-edit",
    )
    runner_state["ak_promotion_name"] = new_name


@allure.epic("Акция")
@allure.feature("CRUD")
@allure.title("Акция: Дубликат — bir xil nom bilan xatolik")
def test_203_promotion_duplicate(session_page: Page, code, runner_state) -> None:
    ak = _ak_code(code)
    run_promotion_duplicate(
        session_page, ak,
        supplier_name=f"supplier-{ak}",
        bonus_product=runner_state.get("ak_product_name"),
        name=runner_state["ak_promotion_name"],
    )


# ══════════════════════════════════════════════════════════════════════════════
# IV. ZAKAZ + BONUS — aksiya haqiqatan ishlaydimi
# ══════════════════════════════════════════════════════════════════════════════
@allure.epic("Акция")
@allure.feature("Заказ")
@allure.title("Акция: Заказ — klient 2 dona buyurtma qiladi (aksiya triggeri)")
def test_210_order(session_page: Page, code, runner_state) -> None:
    ak = _ak_code(code)
    logout(session_page)
    authorization(session_page, email=f"client_user-{ak}@{COMPANY_CODE}", password="1")
    ga_order(session_page, ak, product_name=runner_state.get("ak_product_name"))


@allure.epic("Акция")
@allure.feature("Заказ")
@allure.title("Акция: Бонус — zakazда 'buy 2 → 1 tekin' qo'llangani (Продажи→Заказы)")
def test_211_order_bonus(session_page: Page, code, runner_state) -> None:
    ak = _ak_code(code)
    # Bonus tekshiruvi admin (Модератор) rolida — klient seansdan admin'ga qaytamiz.
    logout(session_page)
    authorization(session_page)
    verify_order_bonus(
        session_page,
        bonus_product=runner_state.get("ak_product_name"),
        client_name=f"client-{ak}",
        expected_qty="1",
    )


# ══════════════════════════════════════════════════════════════════════════════
# IV-B. NEGATIV CASE 1 — trigger sharti bajarilmasa bonus YO'Q (qty < Мин.значение)
# ══════════════════════════════════════════════════════════════════════════════
@allure.epic("Акция")
@allure.feature("Заказ — негатив")
@allure.title("Акция (негатив): Заказ — klient 1 dona buyurtma qiladi (Мин=2, trigger bajarilmaydi)")
def test_212_order_below_min(session_page: Page, code, runner_state) -> None:
    ak = _ak_code(code)
    logout(session_page)
    authorization(session_page, email=f"client_user-{ak}@{COMPANY_CODE}", password="1")
    # Мин.значение=2 → 1 dona buyurtма aksiya triggerini BAJARMAYDI (bonus yo'q kutiladi)
    ga_order(session_page, ak, product_name=runner_state.get("ak_product_name"), qty="1")


@allure.epic("Акция")
@allure.feature("Заказ — негатив")
@allure.title("Акция (негатив): Бонус YO'Q — qty=1 zakazда 'Акция' tab bo'sh")
def test_213_no_bonus_below_min(session_page: Page, code, runner_state) -> None:
    ak = _ak_code(code)
    logout(session_page)
    authorization(session_page)
    verify_no_order_bonus(
        session_page,
        bonus_product=runner_state.get("ak_product_name"),
        client_name=f"client-{ak}",
    )


# ══════════════════════════════════════════════════════════════════════════════
# V. АКЦИЯ — status + delete (bonus tekshiruvидан KEYIN — aksiyaga destruktiv amal)
# ══════════════════════════════════════════════════════════════════════════════
@allure.epic("Акция")
@allure.feature("CRUD")
@allure.title("Акция: Статус — Неактивный/Активный")
def test_220_promotion_status(session_page: Page, code, runner_state) -> None:
    ak = _ak_code(code)
    run_promotion_status(
        session_page, supplier_name=f"supplier-{ak}",
        name=runner_state["ak_promotion_name"],
    )


@allure.epic("Акция")
@allure.feature("CRUD")
@allure.title("Акция: Удаление — alohida (order'да ishlatilmagan) aksiya")
def test_221_promotion_delete(session_page: Page, code, runner_state) -> None:
    ak = _ak_code(code)
    # Order'даги aksiyani O'CHIRIB BO'LMAYDI (SBD_DEAL_PRODUCTS child record) —
    # o'chirish uchun ALOHIDA throwaway aksiya yaratib, o'shani o'chiramiz.
    name = run_promotion(
        session_page, ak, supplier_name=f"supplier-{ak}",
        bonus_product=runner_state.get("ak_product_name"),
        case="qty_free", name=f"aksiya-del-{ak}",
    )
    run_promotion_delete(session_page, supplier_name=f"supplier-{ak}", name=name)


# ══════════════════════════════════════════════════════════════════════════════
# VI. NEGATIV CASE 4 — Неактивный aksiya → bonus YO'Q (status oxirida: destruktiv)
# ══════════════════════════════════════════════════════════════════════════════
@allure.epic("Акция")
@allure.feature("Заказ — негатив")
@allure.title("Акция (негатив): asosiy aksiyani Неактивный qilish")
def test_230_promotion_deactivate(session_page: Page, code, runner_state) -> None:
    ak = _ak_code(code)
    # test_220 aksiyani Активный holatда qoldirgan — endi doimiy deaktivatsiya qilamiz.
    run_promotion_deactivate(
        session_page, supplier_name=f"supplier-{ak}",
        name=runner_state["ak_promotion_name"],
    )


@allure.epic("Акция")
@allure.feature("Заказ — негатив")
@allure.title("Акция (негатив): Неактивный aksiyada Заказ — klient 2 dona (trigger to'g'ri, lekin aksiya o'chiq)")
def test_231_order_inactive_promo(session_page: Page, code, runner_state) -> None:
    ak = _ak_code(code)
    logout(session_page)
    authorization(session_page, email=f"client_user-{ak}@{COMPANY_CODE}", password="1")
    # Miqdor Мин=2 ni QANOATLANTIRADI, lekin aksiya Неактивный → bonus kutilMAYDI.
    ga_order(session_page, ak, product_name=runner_state.get("ak_product_name"), qty="2")


@allure.epic("Акция")
@allure.feature("Заказ — негатив")
@allure.title("Акция (негатив): Бонус YO'Q — Неактивный aksiyada qty=2 zakazда 'Акция' tab bo'sh")
def test_232_no_bonus_inactive(session_page: Page, code, runner_state) -> None:
    ak = _ak_code(code)
    logout(session_page)
    authorization(session_page)
    verify_no_order_bonus(
        session_page,
        bonus_product=runner_state.get("ak_product_name"),
        client_name=f"client-{ak}",
    )


# ══════════════════════════════════════════════════════════════════════════════
# VII. CASE 2 — Скидка (chegirma) TIPIDAGI aksiya yaratish
# ══════════════════════════════════════════════════════════════════════════════
# DIQQAT: Скидка-tipidagi aksiya (Тип бонуса=Скидка) bu tizimda ORDER'ga na
# Черновик, na Новый bosqichida qo'llanmaydi (MCP 2026-09-21: deal 882521 Новый'да
# ham "Общая сумма скидки"=0, "Акция" tab bo'sh) — tekin-mahsulot bonusidan (Количество)
# farqli. Shu sabab bu case order-darajasida EMAS, faqat aksiya YARATISH darajasida
# qamrab olinadi (chegirma-tur promo muvaffaqiyatli saqlanadi). Chegirmaning order'да
# qo'llanish MEXANIZMI hali noaniq (ehtimol keyingi status yoki backend config) —
# kelajakda tekshirish uchun. Yaratilgan promo test_250'да deaktivatsiya qilinadi.
@allure.epic("Акция")
@allure.feature("CRUD")
@allure.title("Акция (Скидка): qty_discount TIPIDAGI aksiya yaratish (Тип бонуса=Скидка 10%)")
def test_240_promotion_discount_create(session_page: Page, code, runner_state) -> None:
    ak = _ak_code(code)
    name = run_promotion(
        session_page, ak,
        supplier_name=f"supplier-{ak}",
        bonus_product=runner_state.get("ak_product_name"),
        case="qty_discount",
        name=f"aksiya-discount-{ak}",
    )
    runner_state["ak_discount_name"] = name


# ══════════════════════════════════════════════════════════════════════════════
# VIII. CASE 5 — Сумма triggeri: buyurtma summasi ≥ Мин → tekin mahsulot bonusi
# ══════════════════════════════════════════════════════════════════════════════
@allure.epic("Акция")
@allure.feature("Заказ")
@allure.title("Акция (Сумма): chegirma aksiyasini Неактивный + sum_free aksiya yaratish")
def test_250_promotion_sum_create(session_page: Page, code, runner_state) -> None:
    ak = _ak_code(code)
    # Chegirma aksiyasini o'chiramiz — endi faqat sum_free ta'sir qilsin (interferensiya yo'q).
    run_promotion_deactivate(
        session_page, supplier_name=f"supplier-{ak}",
        name=runner_state["ak_discount_name"],
    )
    # Тип акции=Сумма, Мин=100000. Mahsulot narxi 100000 → qty=2 = 200000 ≥ 100000 (trigger).
    name = run_promotion(
        session_page, ak,
        supplier_name=f"supplier-{ak}",
        bonus_product=runner_state.get("ak_product_name"),
        case="sum_free",
        name=f"aksiya-sum-{ak}",
    )
    runner_state["ak_sum_name"] = name


@allure.epic("Акция")
@allure.feature("Заказ")
@allure.title("Акция (Сумма): Заказ — klient 2 dona (summa 200 000 ≥ Мин 100 000)")
def test_251_order_sum(session_page: Page, code, runner_state) -> None:
    ak = _ak_code(code)
    logout(session_page)
    authorization(session_page, email=f"client_user-{ak}@{COMPANY_CODE}", password="1")
    ga_order(session_page, ak, product_name=runner_state.get("ak_product_name"), qty="2")


@allure.epic("Акция")
@allure.feature("Заказ")
@allure.title("Акция (Сумма): Бонус qo'llangani — summa triggeri tekin mahsulot berdi")
def test_252_order_sum_bonus(session_page: Page, code, runner_state) -> None:
    ak = _ak_code(code)
    logout(session_page)
    authorization(session_page)
    verify_order_bonus(
        session_page,
        bonus_product=runner_state.get("ak_product_name"),
        client_name=f"client-{ak}",
        expected_qty="1",
    )


# ── CASE 3 (subtype targeting negativ) OLIB TASHLANDI ─────────────────────────
# "Характеристики клиента" podtiplari GLOBAL emas, har SUPPLIERга xos (MCP 2026-09-21):
# test'ning supplier-{code}4'sida faqat "Подтип по умолчанию" bor (Saber OOO'да 3 ta).
# Boshqa podtipga yo'naltirilgan aksiya yaratib bo'lmaydi (picker'да yagona podtip) →
# subtype-targeting negativ case uchun avval supplierга 2-podtip + o'sha podtipli
# klient yaratish kerak (katta qo'shimcha setup). KELAJAK ish sifatida qoldirildi.
