import re

import allure
from playwright.sync_api import Page, expect

from flows.flow_authorization import authorization
from flows.flow_navbar import flow_navigate
from utils.base_page import BasePage


def run_cooperation(page: Page, code) -> None:
    """Group A: supplier-{code} dan client-{code} ga hamkorlik so'rovi yuboradi
    va klient tomonида uni tasdiqlaydi (run_supplier va run_client dan keyin).

    Клиент 'Рекомендованные клиенты' ro'yxatiga tushishi uchun supplier bilan
    bir xil Регион va Отрасль bo'lishi kerak (run_supplier/run_client shuni
    ta'minlaydi — ikkalasi ham birinchi Region-*/Industry-* ni tanlaydi)."""
    m = BasePage(page)
    supplier_name = f"supplier-{code}"
    client_name = f"client-{code}"

    with allure.step("Навигация: Модератор → Поставщики"):
        flow_navigate(page, tab="Модератор", name="Поставщики")
        m.expect_heading("Поставщики")

    with allure.step(f"'{supplier_name}' Просмотр formasini ochish"):
        m.search(supplier_name)
        m.click_grid_row(supplier_name)
        m.click_button("Просмотреть")
        m.expect_heading("Поставщик (Просмотр)")

    with allure.step("Запросы на сотрудничество → Клиент → Рекомендованные клиенты"):
        m.click_button("Запросы на сотрудничество")
        # Navbar'da ham "Клиент" bor, view ichida esa smt-tab-button[role=button]
        # ham matnga mos keladi — shu sabab CSS `button` tag bilan aniqlanadi
        page.locator("#main-content button").filter(has_text=re.compile(r"^Клиент$")).first.click()

    with allure.step(f"'{client_name}' ga hamkorlik so'rovi yuborish"):
        # DIQQAT: bu tab'da qidiruv ISHLATILMAYDI — backend recommended_clients
        # so'rovida yo'q client_code ustuni bo'yicha filtr yuboradi va 500 qaytadi.
        # Ro'yxat baribir kichik: faqat shu run'ning Region/Отрасль'iga mos klientlar.
        #
        # POYGA: "Клиент" bosilgach grid avval "Мои клиенты"
        # ma'lumotini (client_list:supplier_clients) yuklaydi. Shu so'rov tugamasidan
        # "Рекомендованные клиенты" bosilsa grid ESKI ustunlar (has_active_deal,
        # client_code) bilan so'rov yuboradi — backend "FAZO_QUERY: Field not found
        # [has_active_deal]" bilan 500 qaytaradi va ro'yxat "Нет результатов" qoladi.
        # Tez toggle qilish DAVOLAMAYDI: supplier_clients so'rovi umuman ketmay,
        # ustun holati yangilanmaydi (2026-07-10 run trace'ida 4 urinishning
        # hammasi eski ustunlar bilan 500). Shuning uchun har tab bosishdan OLDIN
        # _settle (loader + networkidle) bilan joriy grid so'rovi tugashi kutiladi
        # — inson tezligida MCP bilan tasdiqlangan, hammasi 200.
        row = page.locator(".smt-data-row").filter(has_text=client_name).first
        for _ in range(3):
            m.settle()
            m.click_button("Рекомендованные клиенты")
            try:
                expect(row).to_be_visible(timeout=5_000)
                break
            except AssertionError:
                m.click_button("Мои клиенты")
        else:
            expect(row).to_be_visible(timeout=3_000)
        m.click_grid_row(client_name)
        m.click_button("Отправить запрос на сотрудничество")
        m.confirm("да")

    with allure.step("Навигация: Модератор → Клиенты"):
        flow_navigate(page, tab="Модератор", name="Клиенты")
        m.expect_heading("Клиенты")

    with allure.step(f"'{client_name}' Просмотр formasini ochish"):
        m.search(client_name)
        m.click_grid_row(client_name)
        m.click_button("Просмотреть")
        m.expect_heading("Клиент (Просмотр)")

    with allure.step(f"Запросы поставщиков: '{supplier_name}' so'rovini tasdiqlash"):
        m.click_button("Запросы на сотрудничество")
        # Klient tomonidagi "Запросы поставщиков" ro'yxati BIR MARTALIK yuklanadi
        # va bu tab'da qidiruv ISHLATILMAYDI — supplier yuborgan so'rov serverda
        # ozgina KECHIKIB paydo bo'lsa, grid_row eski (bo'sh) DOM'ni qayta
        # tekshiraveradi va uni ko'rmaydi ("Нет результатов" bilan yiqiladi —
        # test_214, 2026-08-25 CI). Shu sabab ro'yxatni "Мои запросы" ↔ "Запросы
        # поставщиков" tablari orasida qayta ochib (server ro'yxatni QAYTA
        # so'raydi) supplier qatori chiqquncha bir necha marta urinamiz.
        supplier_row = page.locator(".smt-data-row").filter(has_text=supplier_name).first
        for attempt in range(6):
            m.click_button("Запросы поставщиков")
            m.settle()
            try:
                expect(supplier_row).to_be_visible(timeout=5_000)
                break
            except AssertionError:
                if attempt == 5:
                    raise
                m.click_button("Мои запросы")  # tab almashtirib ro'yxatni qayta yuklaymiz
                m.settle()
        m.click_grid_row(supplier_name)
        m.click_button("Подтвердить")
        m.confirm("да")


@allure.epic("Модератор")
@allure.feature("Group A")
@allure.story("Запрос на сотрудничество")
@allure.title("Group A: Поставщик ↔ Клиент hamkorlik so'rovi va tasdiqlash")
def test_cooperation(page: Page, code) -> None:
    with allure.step("Tizimga kirish"):
        authorization(page)
    run_cooperation(page, code)
