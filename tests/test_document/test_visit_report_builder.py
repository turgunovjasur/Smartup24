"""Конструктор отчетов по визитам (visit report BUILDER) — ochilish smoke testi.

Форма: sarlavha "Конструктор отчетов по визитам", URL /x24/a2/sb/rep/sbmv/visit.
Bu Анализ маршрутов'дан BOSHQA forma — OLAP/pivot hisobot QURUVCHISI (Названия
maydonlar ro'yxati + Строки/Столбцы/Фильтры/Значения drop zonalar + eksport
HTML/EXCEL/CSV/XML + Просмотреть). To'g'ridan-to'g'ri menyu yozuvi yo'q — Анализ
маршрутов sahifasidagi breadcrumb havolasi orqali ochiladi.

DIQQAT: hisobot QURISH (maydon drag → Строки/Столбцы, preview, eksport) CDK
drag-drop va O'ZGARUVCHAN ma'lumotга bog'liq — flaky/qimmat, shuning uchun bu yerда
FAQAT formaning to'g'ri OCHILISHI tekshiriladi (bo'limlar + eksport tugmalari
ko'rinadi). MCP tasdiqlangan 2026-09-11.

Loyiha uslubi (flat): run_* (biznes logika) + test_* (authorization + run_*).
"""
import allure
from playwright.sync_api import Page, expect

from flows.flow_authorization import authorization
from flows.flow_navbar import flow_navigate
from utils.base_page import BasePage

BUILDER_LINK = "Конструктор отчетов по визитам"


def _open_builder(page: Page, m: BasePage) -> None:
    """Анализ маршрутов formasini ochib, breadcrumb'даги "Конструктор отчетов по
    визитам" havolasi orqali BUILDER sahifasiga o'tadi (parent link)."""
    flow_navigate(page, tab="Модератор", name="Анализ маршрутов")
    page.wait_for_url(lambda u: "route_analysis" in u, timeout=15_000)
    m.settle()
    page.get_by_role("link", name=BUILDER_LINK).first.click()
    page.wait_for_url(lambda u: "sbmv/visit" in u, timeout=15_000)
    m.settle()


def run_builder_opens(page: Page) -> None:
    """"Конструктор отчетов по визитам" to'g'ri ochiladi: asosiy bo'limlar (Названия +
    drop zonalar) va eksport tugmalari (HTML/EXCEL/CSV/XML + Просмотреть) ko'rinadi."""
    m = BasePage(page)
    _open_builder(page, m)
    for zone in ("Названия", "Строки", "Столбцы", "Фильтры", "Значения"):
        expect(page.get_by_role("heading", name=zone).first).to_be_visible()
    for fmt in ("HTML", "EXCEL", "CSV", "XML"):
        expect(page.get_by_role("button", name=fmt, exact=True).first).to_be_visible()
    expect(page.get_by_role("button", name="Просмотреть").first).to_be_visible()


@allure.epic("Документы")
@allure.feature("Конструктор отчетов по визитам")
@allure.title("Builder: forma ochiladi (bo'limlar + eksport tugmalari)")
def test_builder_opens(page: Page) -> None:
    authorization(page)
    run_builder_opens(page)
