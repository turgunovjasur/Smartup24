import random

import allure
from playwright.sync_api import Page

from flows.flow_authorization import authorization
from flows.flow_navbar import flow_navigate
from utils.base_page import BasePage


def run_supplier_user(page: Page, code) -> None:
    """Group A: supplier-{code} ning Просмотр formasida Пользователи bo'limidan
    yangi foydalanuvchi yaratadi (run_supplier dan keyin ishlaydi)."""
    m = BasePage(page)
    supplier_name = f"supplier-{code}"
    user_name = f"supplier_user-{code}"
    phone = f"+998(99)-{random.randint(100, 999)}-{random.randint(10, 99)}-{random.randint(10, 99)}"

    with allure.step("Навигация: Модератор → Поставщики"):
        flow_navigate(page, tab="Модератор", name="Поставщики")
        m.expect_heading("Поставщики")

    with allure.step(f"'{supplier_name}' ni topib Просмотр formasini ochish"):
        m.search(supplier_name)
        m.click_grid_row(supplier_name)
        m.click_button("Просмотреть")
        m.expect_heading("Поставщик (Просмотр)")

    with allure.step("Пользователи bo'limida Создать formasini ochish"):
        m.click_button("Пользователи")
        m.open_create()
        m.expect_heading("Пользователь (Создания)")

    with allure.step(f"Форма: ФИО = {user_name}, Логин, Пароль, Номер телефона = {phone}"):
        m.input(label="ФИО", value=user_name)
        m.input(label="Логин", value=user_name)
        m.input(label="Пароль", value="1")
        m.input(label="Номер телефона", value=phone)

    with allure.step("Роли: Админ (Поставщик)"):
        # Rolsiz foydalanuvchi login qilolmaydi — "Пользователь не прикреплен
        # ни к одному филиалу или проекту" (client user bilan bir xil qoida).
        # Variantlar: Админ/Менеджер/Оператор (Поставщик) — MCP tasdiqlangan 2026-07-13.
        m.select("Админ (Поставщик)", label="Роли", search="Админ")

    with allure.step("Сохранить va Просмотр formasiga qaytish"):
        m.save_and_expect_heading("Поставщик (Просмотр)")

    with allure.step(f"Пользователи ro'yxatida '{user_name}' tekshirish"):
        m.click_button("Пользователи")
        m.search(user_name)
        m.grid_row(user_name)


@allure.epic("Модератор")
@allure.feature("Group A")
@allure.story("Пользователь поставщика")
@allure.title("Group A: Поставщик uchun yangi foydalanuvchi yaratish")
def test_supplier_user(page: Page, code) -> None:
    with allure.step("Tizimga kirish"):
        authorization(page)
    run_supplier_user(page, code)
