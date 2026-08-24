"""Тип вопроса — basic create.

Вопросы ro'yxati sarlavhasidagi "Тип вопроса" sub-nav bo'limi (biruni
``quiz_type_list``). Sodda справочnik: Статус switch, Код, Название *,
Порядок (MCP tasdiqlangan 2026-08-21).
"""
import allure
from playwright.sync_api import Page

from flows.flow_authorization import authorization
from flows.flow_navbar import flow_navigate
from utils.base_page import BasePage


def run_quiz_type(page: Page, code) -> None:
    m = BasePage(page)
    name = f"QuizType-{code}"

    with allure.step("Навигация: Модератор → Вопросы"):
        flow_navigate(page, tab="Модератор", name="Вопросы")
        m.expect_heading("Вопросы")

    with allure.step("Тип вопроса bo'limiga o'tish"):
        m.click_link("Тип вопроса")
        m.expect_heading("Тип вопроса")

    with allure.step("Создать: yangi savol turi formasi ochish"):
        m.open_create()
        m.expect_heading("Тип вопроса (Создание)")

    with allure.step(f"Форма: Название = {name}"):
        m.input(label="Название", value=name)

    with allure.step("Сохранить va ro'yxatga qaytish"):
        m.save_and_expect_heading("Тип вопроса")

    with allure.step(f"Qidiruv va ro'yxatda '{name}' tekshirish"):
        m.search(name)
        m.grid_row(name)


@allure.epic("Модератор")
@allure.feature("Вопрос")
@allure.story("Тип вопроса")
@allure.title("Yangi savol turi yaratish")
def test_quiz_type(page: Page, code) -> None:
    with allure.step("Tizimga kirish"):
        authorization(page)
    run_quiz_type(page, code)
