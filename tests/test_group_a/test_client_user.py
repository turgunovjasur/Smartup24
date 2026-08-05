import random

import allure
from playwright.sync_api import Page

from flows.flow_authorization import authorization
from flows.flow_navbar import flow_navigate
from utils.base_page import BasePage


def run_client_user(page: Page, code) -> None:
    """Group A: client-{code} ning Просмотр formasida Пользователи bo'limidan
    yangi foydalanuvchi yaratadi va uni klient savdo nuqtasiga bog'laydi
    (run_client dan keyin ishlaydi)."""
    m = BasePage(page)
    client_name = f"client-{code}"
    user_name = f"client_user-{code}"
    phone = f"+998(99)-{random.randint(100, 999)}-{random.randint(10, 99)}-{random.randint(10, 99)}"

    with allure.step("Навигация: Модератор → Клиенты"):
        flow_navigate(page, tab="Модератор", name="Клиенты")
        m.expect_heading("Клиенты")

    with allure.step(f"'{client_name}' ni topib Просмотр formasini ochish"):
        m.search(client_name)
        m.click_grid_row(client_name)
        m.click_button("Просмотреть")
        m.expect_heading("Клиент (Просмотр)")

    with allure.step("Пользователи bo'limida Создать formasini ochish"):
        m.click_button("Пользователи")
        m.open_create()
        m.expect_heading("Пользователь (Создания)")

    with allure.step(f"Форма: ФИО = {user_name}, Логин, Пароль, Номер телефона = {phone}"):
        m.input(label="ФИО", value=user_name)
        m.input(label="Логин", value=user_name)
        m.input(label="Пароль", value="1")
        m.input(label="Номер телефона", value=phone)

    with allure.step("Роли: Админ (Клиент)"):
        # Rolsiz foydalanuvchi login qilolmaydi — "Пользователь не прикреплен
        # ни к одному филиалу или проекту" (MCP tasdiqlangan 2026-07-06)
        m.select("Админ (Клиент)", label="Роли", search="Админ")

    with allure.step(f"Торговые точки: '{client_name}' savdo nuqtasini tanlash"):
        # Klient yaratilganda shu nom bilan savdo nuqtasi avtomatik ochiladi
        m.select(client_name, label="Торговые точки", exact=False)

    with allure.step("Сохранить va Просмотр formasiga qaytish"):
        m.save_and_expect_heading("Клиент (Просмотр)")

    with allure.step(f"Пользователи ro'yxatida '{user_name}' tekshirish"):
        m.click_button("Пользователи")
        m.search(user_name)
        m.grid_row(user_name)


@allure.epic("Модератор")
@allure.feature("Group A")
@allure.story("Пользователь клиента")
@allure.title("Group A: Клиент uchun yangi foydalanuvchi yaratish")
def test_client_user(page: Page, code) -> None:
    with allure.step("Tizimga kirish"):
        authorization(page)
    run_client_user(page, code)
