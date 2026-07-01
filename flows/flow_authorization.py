from playwright.sync_api import Page, expect


def authorization(page: Page, email="admin@autotest", password="greenwhite") -> None:
    page.goto("https://app3.greenwhite.uz/x24/a2/auth/login")
    page.get_by_role("textbox", name="Логин").fill(email)
    page.get_by_role("textbox", name="Введите пароль").fill(password)
    page.get_by_role("button", name="Войти").click()
    expect(page.locator("app-form-stack-widget")).to_contain_text("Smartup24")

