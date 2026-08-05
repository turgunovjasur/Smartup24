import allure
from playwright.sync_api import Page

from flows.flow_authorization import authorization
from flows.flow_navbar import flow_navigate
from utils.base_page import BasePage


def run_shablon(page: Page, code, name=None) -> str:
    """Yangi Шаблон отчета по опросам yaratadi (faqat majburiy Название).
    ``name`` berilmasa Shablon-{code}. Yaratilgan nomni qaytaradi (regression
    CRUD testlari edit/view/delete/status shunga tayanadi)."""
    m = BasePage(page)
    if name is None:
        name = f"Shablon-{code}"

    with allure.step("Навигация: Модератор → Шаблоны отчетов по опросам"):
        flow_navigate(page, tab="Модератор", name="Шаблоны отчетов по опросам")
        m.expect_heading("Шаблоны отчетов по опросам")

    with allure.step("Создать: yangi Шаблон formasi ochish"):
        m.open_create()
        m.expect_heading("Шаблон отчета по опросам (Создание)")

    with allure.step(f"Форма: Название = {name}"):
        m.input(label="Название", value=name)

    with allure.step("Сохранить va ro'yxatga qaytish"):
        # Saqlashdan keyingi redirect BARQAROR EMAS — ba'zan ro'yxat o'rniga
        # dashboardga (/biruni/intro/dashboard) ketib qoladi (2026-07-31 runner,
        # shablon create). save_and_expect_heading shu sababli timeout berardi.
        # run_shablon_basic/full/edit kabi: save'ni tasdiqlab (forma yopiladi),
        # ro'yxatga o'zimiz kiramiz.
        m.save()
        flow_navigate(page, tab="Модератор", name="Шаблоны отчетов по опросам")
        m.expect_heading("Шаблоны отчетов по опросам")

    with allure.step(f"Qidiruv va ro'yxatda '{name}' tekshirish"):
        m.search(name)
        m.grid_row(name)

    return name


@allure.epic("Модератор")
@allure.feature("Шаблоны отчетов")
@allure.story("Создание шаблона")
@allure.title("Yangi Шаблон отчета по опросам yaratish")
def test_shablon(page: Page, code) -> None:
    with allure.step("Tizimga kirish"):
        authorization(page)
    run_shablon(page, code)
