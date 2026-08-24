from datetime import datetime, timedelta

import allure
from playwright.sync_api import Page, expect

from flows.flow_authorization import COMPANY_CODE, authorization
from flows.flow_navbar import flow_navigate
from utils.base_page import BasePage


def _set_qty(page: Page, value: str = "2", *, attempts: int = 5) -> None:
    """Товары qatorining Кол-во (3-katagi: 0=Название,1=Цена,2=Кол-во) ni yozadi
    va qiymat TURG'UN bo'lguncha kutadi.

    Tovar tanlangач qator modeli serverdan KECHIKIB qayta yuklanib miqdorni 0 ga
    qaytarishi mumkin (race, MCP/trace 2026-07-08). Oldin fixed 1200ms uyqu bilan
    kutilardi va faqat BIR marta tekshirilardi — 1200ms dan KEYIN kelgan reset
    "o'tib ketib" save bosqichiga qolar edi. Endi qiymat ~1.5s oynada TURG'UN
    turishini polling bilan tasdiqlaymiz: har ~250ms o'qiymiz, birorta o'qishda
    qiymat o'zgarsa (kechikkan reload 0 ga qaytardi) tashqi sikl qayta yozadi;
    toza o'tsa fixed uyquni kutmasdan erta qaytamiz. Bu sehrli sonni reset
    oynasini to'liq qoplaydigan event-reaktiv kutishga almashtiradi."""
    row = page.locator(".smt-data-row").first
    qty = row.locator("smt-cell-content").nth(2).locator("input").first
    for _ in range(attempts):
        qty.click()
        qty.fill(value)
        # Turg'unlik oynasi: ~1.5s (6 × 250ms). Drift aniqlansa darhol qayta yozamiz.
        stable = True
        for _ in range(6):
            page.wait_for_timeout(250)
            if (qty.input_value() or "").strip() != value:
                stable = False
                break
        if stable:
            return
    # baribir turmasa — oxirgi yozuv qoladi, save bosqichida qayta uriniladi


def _fill_step2_and_advance(page: Page, m: BasePage, product_name: str, value: str = "2") -> None:
    """2-qadam Товары → 3-qadam Завершение. Qator ICHIDAGI qidiruv (LABEL'siz
    smt-data-select) orqali tovarni tanlaydi ("Подбор" TUGMASI/alohida sahifasi
    EMAS — u klient katalogida bo'sh chiqadi), Кол-во ni yozadi va Завершение
    qadamiga o'tadi. Qty-reset race (qator modeli kechikib 0 ga tushishi)
    "Не указано количество" dialogi bilan transition'ni to'sishi mumkin — dialogni
    yopib, qty ni qayta yozib, Завершение ochilguncha (Тип оплаты ko'ringuncha)
    qayta urinamiz."""
    row = page.locator(".smt-data-row").first
    m.select(product_name, root=row)
    error_dialog = page.get_by_role("dialog").filter(has_text="Не указано количество")
    tip_oplaty = page.get_by_text("Тип оплаты").first
    for _ in range(4):
        _set_qty(page, value)
        m.wizard_step("Завершение")
        m.settle()
        if error_dialog.count():
            error_dialog.get_by_role("button", name="Закрыть").first.click()
            expect(error_dialog).to_be_hidden()
            m.wizard_step("Товары")  # qaytib qty qayta yoziladi
            continue
        try:
            expect(tip_oplaty).to_be_visible(timeout=5_000)
            return  # 3-qadam ochildi
        except AssertionError:
            m.wizard_step("Товары")
            continue
    raise AssertionError("Товары → Завершение: Кол-во qabul qilinmadi (qty-reset race)")


def run_order(page: Page, code, product_name=None) -> None:
    """Group A: klient foydalanuvchisi nomidan yangi Заказ yaratadi — 3 qadamli
    wizard: Основное (savdo nuqtasi/postavshik/yetkazish vaqti) → Товары (tovar
    va miqdor) → Завершение (to'lov turi va status).

    client_user-{code} bilan login qilingan bo'lishi kerak (run_client_user
    yaratadi); dropdownlarda faqat hamkorlik tasdiqlangan postavshik
    (run_cooperation) va unga biriktirilgan narxli tovar chiqadi — shu sabab
    ``product_name`` ga run_product_linking HAQIQATDA biriktirgan tovar nomi
    beriladi (u har doim ham product-{code} emas)."""
    m = BasePage(page)
    supplier_name = f"supplier-{code}"
    client_name = f"client-{code}"
    product_name = product_name or f"product-{code}"
    delivery_time = (datetime.now() + timedelta(days=7)).strftime("%d.%m.%Y %H:%M")

    with allure.step("Навигация: Клиент → Заказы"):
        flow_navigate(page, tab="Клиент", name="Заказы")
        m.expect_heading("Заказы")

    with allure.step("Создать: yangi Заказ formasi ochish"):
        m.open_create()
        m.expect_heading("Заказ (создание)")

    with allure.step(
        f"1-qadam Основное: Торговые точки = {client_name}, "
        f"Поставщики = {supplier_name}, Время доставки = {delivery_time}"
    ):
        m.select(client_name, label="Торговые точки")
        m.select(supplier_name, label="Поставщики")
        # "Время доставки" savdo nuqtasi tanlangunicha disabled bo'ladi —
        # shu tartibda to'ldirilishi shart (MCP tasdiqlangan 2026-07-17)
        m.input(label="Время доставки", value=delivery_time)
        # "ДАЛЕЕ" tugmasi olib tashlangan — qadam tabi bosiladi (2026-07-17)
        m.wizard_step("Товары")

    with allure.step(f"2-qadam Товары: {product_name} tanlash, Кол-во = 2 → Завершение"):
        _fill_step2_and_advance(page, m, product_name)

    with allure.step("3-qadam Завершение: Тип оплаты = Наличные"):
        # "Статус *" ham majburiy (dump 2026-07-30) — lekin default "Черновик"
        # bilan to'lgan; faqat "Тип оплаты" tanlanadi.
        m.select("Наличные", label="Тип оплаты")

    with allure.step("Сохранить va Заказы ro'yxatiga qaytish"):
        # 2-qadamda qty allaqachon tasdiqlangan (Завершение ochilgan) — save
        # to'g'ridan-to'g'ri o'tadi; xavfsizlik uchun bir marta qayta uriniladi.
        error_dialog = page.get_by_role("dialog").filter(has_text="Не указано количество")
        for attempt in range(2):
            m.click_button("Сохранить")
            try:
                m.expect_heading("Заказы", timeout=8_000)
                break
            except AssertionError:
                if attempt == 1:
                    raise
                if error_dialog.count():
                    error_dialog.get_by_role("button", name="Закрыть").first.click()
                    expect(error_dialog).to_be_hidden()
                m.wizard_step("Товары")
                _set_qty(page)
                m.wizard_step("Завершение")

    with allure.step(f"Ro'yxatda yangi order ({supplier_name} / {client_name} / Черновик) tekshirish"):
        # Yangi order Черновик statusida yaratiladi (MCP tasdiqlangan 2026-07-17)
        m.grid_row(supplier_name, client_name, "Черновик")


@allure.epic("Клиент")
@allure.feature("Group A")
@allure.story("Создание заказа")
@allure.title("Group A: klient foydalanuvchisi nomidan yangi Заказ yaratish")
def test_order(page: Page, code) -> None:
    with allure.step("Tizimga kirish (klient foydalanuvchisi)"):
        # To'liq login = "<Логин>@<kompaniya kodi>" (admin@sm24 bilan bir xil format)
        authorization(page, email=f"client_user-{code}@{COMPANY_CODE}", password="1")
    run_order(page, code)
