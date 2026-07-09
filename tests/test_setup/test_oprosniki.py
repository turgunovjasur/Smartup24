import allure
from playwright.sync_api import Page

from flows.flow_authorization import authorization
from flows.flow_navbar import flow_navigate
from utils.base_page import BasePage


def run_oprosniki(page: Page, code, name=None) -> None:
    """Yangi Опросник yaratadi. Forma yangilangan (MCP tasdiqlangan 2026-07-07):
    "Дата начала" va "Конец" endi MAJBURIY (smt-date-picker, sana matn
    sifatida yoziladi)."""
    m = BasePage(page)
    if name is None:
        name = f"oprosniki-{code}"

    with allure.step("Навигация: Модератор → Опросники"):
        flow_navigate(page, tab="Модератор", name="Опросники")
        m.expect_heading("Опросники")

    with allure.step("Создать: yangi Опросник formasi ochish"):
        m.open_create()
        m.expect_heading("Опросник (Создание)")

    with allure.step(f"Форма: Название = {name}, Дата начала/Конец"):
        m.input(label="Название", value=name)
        m.input(label="Дата начала", value="01.08.2026")
        m.input(label="Конец", value="31.08.2026")

    with allure.step("Сохранить va ro'yxatga qaytish"):
        m.save_and_expect_heading("Опросники")

    with allure.step(f"Qidiruv va ro'yxatda '{name}' tekshirish"):
        m.search(name)
        m.grid_row(name)


@allure.epic("Модератор")
@allure.feature("Опросники")
@allure.story("Создание опросника")
@allure.title("Yangi Опросник yaratish")
def test_oprosniki(page: Page, code) -> None:
    with allure.step("Tizimga kirish"):
        authorization(page)
    run_oprosniki(page, code)
