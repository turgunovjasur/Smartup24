import random

from playwright.sync_api import Page, expect

from flow_navbar import flow_menu, flow_search


def test_example(page: Page) -> None:
    page.goto("https://app3.greenwhite.uz/x24/a2/auth/login")

    page.get_by_role("textbox", name="Логин").fill("admin@sm24")
    page.get_by_role("textbox", name="Введите пароль").fill("greenwhite")
    page.get_by_role("button", name="Войти").click()
    expect(page.locator("app-form-stack-widget")).to_contain_text("Smartup24")
    page.get_by_role("button", name="Модератор").click()
    page.get_by_role("menuitem", name="Бонусная система").click()
    expect(page.locator("app-form-stack-widget")).to_contain_text("Бонусная система")
    page.get_by_role("button", name="Создать").click()
    expect(page.get_by_role("heading")).to_contain_text("Основная информация")

    i = random.randint(1000, 9999)
    page.locator("//label[contains(text(),'Название')]/..//input").fill(f"bonus-{i}")

    page.get_by_role("spinbutton").fill("1")
    page.get_by_text("Процент скидки").first.click()
    page.get_by_role("button", name="Сохранить").click()

    # flow_menu(page)
    # flow_search(page, name=f"bonus-{i}")

