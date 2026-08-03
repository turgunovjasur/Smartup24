from datetime import date, timedelta

import allure
from playwright.sync_api import Page

from flows.flow_authorization import authorization
from flows.flow_navbar import flow_navigate
from utils.base_page import BasePage

# Dinamik sanalar — hardcoded "01.08.2026" o'tmishga aylanib qolmasligi uchun har
# run bugundan hisoblanadi. Bu konstantalar regression (basic/full/duplicate
# kiritish + view/full assertion) da ham IMPORT qilinadi — kiritilgan sana =
# tekshirilgan sana bo'lishi shart.
# DIQQAT: boshlanish KELAJAKDA qoldiriladi (bugun+1) — eski literal "01.08.2026"
# ham bugundan keyin edi; forma boshlanish sanasi kelajakda bo'lishini talab
# qilsa (ehtimoliy validatsiya) bugungi sana buzardi. today+1 buni oldini oladi.
OPROS_START = (date.today() + timedelta(days=1)).strftime("%d.%m.%Y")
OPROS_END = (date.today() + timedelta(days=31)).strftime("%d.%m.%Y")


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

    with allure.step(f"Форма: Название = {name}, Дата начала = {OPROS_START}, Конец = {OPROS_END}"):
        m.input(label="Название", value=name)
        m.input(label="Дата начала", value=OPROS_START)
        m.input(label="Конец", value=OPROS_END)

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
