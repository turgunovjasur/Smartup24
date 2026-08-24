"""Услуги — basic create.

Товары ro'yxati sarlavhasidagi "Услуги" sub-nav bo'limi (biruni
``service_list``). Форма товар (Продукт) ga o'xshaydi: Название *, Краткое
название *, "Ед. изм. *" (majburiy select) + Штрих-код/ИКПУ va Характеристика
(Категории/Бренд/Отрасль, ixtiyoriy) — MCP tasdiqlangan 2026-08-21.

Majburiy "Ед. изм." uchun tizimda GLOBAL bor "кг" birligi tanlanadi (Продукт
testidagi ``m.select("кг", label="measure")`` bilan bir xil — yangi yaratilgan
birlik Подбор qidiruvida darrov ko'rinmaydi/boshqa maydon bo'yicha qidiriladi,
"кг" esa doim topiladi).
"""
import allure
from playwright.sync_api import Page

from flows.flow_authorization import authorization
from flows.flow_navbar import flow_navigate
from utils.base_page import BasePage


def run_service(page: Page, code, measure_name="кг") -> None:
    m = BasePage(page)
    name = f"Service-{code}"

    with allure.step("Навигация: Модератор → Товары"):
        flow_navigate(page, tab="Модератор", name="Товары")
        m.expect_heading("Товары")

    with allure.step("Услуги bo'limiga o'tish"):
        m.click_link("Услуги")
        m.expect_heading("Услуги")

    with allure.step("Создать: yangi xizmat formasi ochish"):
        m.open_create()
        m.expect_heading("Услуга (Создание)")

    with allure.step(f"Форма: Название = {name}, Ед. изм. = {measure_name}"):
        m.input(label="Название", value=name)
        # Короткое: qisqa unikal (product-katalog короткое ~10 belgigacha kesilib
        # dublikat bo'lmasligi uchun — box_type/measure bilan bir xil xavf).
        m.input(label="Краткое название", value=f"sv{code}")
        m.select(measure_name, label="Ед. изм.")

    with allure.step("Сохранить va ro'yxatga qaytish"):
        m.save_and_expect_heading("Услуги")

    with allure.step(f"Qidiruv va ro'yxatda '{name}' tekshirish"):
        m.search(name)
        m.grid_row(name)


@allure.epic("Модератор")
@allure.feature("Товары")
@allure.story("Услуги")
@allure.title("Yangi xizmat (Услуга) yaratish")
def test_service(page: Page, code) -> None:
    with allure.step("Tizimga kirish"):
        authorization(page)
    run_service(page, code)
