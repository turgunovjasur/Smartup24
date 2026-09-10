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

    with allure.step("Поставщик view → 'Клиент' bo'limi"):
        # Рекомендованные клиенты "Клиент" BO'LIMI ichida (eski UI'да "Запросы на
        # сотрудничество" ichida edi — 2026-09-10 MCP bilan tekshirildi, endi alohida
        # "Клиент" bo'limi). Navbar'да ham "Клиент" bor, shu sabab #main-content scope.
        page.locator("#main-content button").filter(has_text=re.compile(r"^Клиент$")).first.click()
        m.settle()

    with allure.step(f"Рекомендованные клиенты → '{client_name}' ga hamkorlik so'rovi"):
        # "Рекомендованные клиенты" grid backend so'rovi SEKIN/beqaror — klient qatori
        # bir necha soniyadан keyin chiqadi (MCP 2026-09-10: inson tezligiда chiqadi,
        # tez avtomat run'да ulgurmaydi). Shuning uchun: tabni bir marta bosib _settle
        # bilan so'rov tugashini kutamiz, keyin qatorni SABR bilan (katta timeout)
        # kutamiz. Tez toggle QILMAYMIZ — u so'rovni reset qilib ro'yxatni bo'shatadi;
        # topilmasagina bir marta Мои клиенты↔Рекомендованные toggle bilan qayta urinamiz.
        row = page.locator(".smt-data-row").filter(has_text=client_name).first
        m.click_button("Рекомендованные клиенты")
        m.settle()
        try:
            expect(row).to_be_visible(timeout=20_000)
        except AssertionError:
            m.click_button("Мои клиенты")
            m.settle()
            m.click_button("Рекомендованные клиенты")
            m.settle()
            expect(row).to_be_visible(timeout=20_000)

        # Qatorni TO'G'RIDAN-TO'G'RI bosamiz (click_grid_row ichki _settle bilan
        # so'rovni qayta yuborib ro'yxatni bo'shatishi mumkin). Action panelда
        # "Отправить запрос на сотрудничество" chiqadi (qator following-sibling'i).
        send_btn = page.get_by_role("button", name="Отправить запрос на сотрудничество").first
        for _ in range(6):
            row.click(position={"x": 120, "y": 12})
            try:
                expect(send_btn).to_be_visible(timeout=3_000)
                break
            except AssertionError:
                continue
        send_btn.click()
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
        # DIQQAT: bu bosqich dev BACKEND 500'iga qarab yiqilishi mumkin —
        # request_list:supplier_requests "FAZO_QUERY: Field not found
        # [supplier_pinfl]" qaytaradi (2026-08-26 trace). Bu test kodidan
        # tuzatib bo'lmaydi; runner'da test_214 shu sabab xfail belgilangan.
        m.click_button("Запросы на сотрудничество")
        m.click_button("Запросы поставщиков")
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
