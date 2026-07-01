from playwright.sync_api import Page, expect

from flows.flow_navbar import flow_navigate


def test_industry(page: Page) -> None:
    flow_navigate(page, tab="Модератор", name="Товары")

    expect(page.locator("app-form-stack-widget")).to_contain_text("Товары")
    page.get_by_role("link", name="Характеристика товаров").click()
    expect(page.locator("app-form-stack-widget")).to_contain_text("Характеристика товаров")
    page.get_by_role("searchbox", name="Поиск").click()
    page.get_by_role("searchbox", name="Поиск").fill("Отрасль")
    page.get_by_role("searchbox", name="Поиск").press("Enter")
    page.get_by_text("Отрасль").click()
    page.get_by_role("button", name="Подтипы").click()
    expect(page.locator("app-form-stack-widget")).to_contain_text("Отрасль")
    page.get_by_role("button", name="Создать").click()
    expect(page.locator("app-form-stack-widget")).to_contain_text("Характеристика товаров (создание)")
    page.locator("input[name=\"ng.form10.name\"]").click()
    page.locator("input[name=\"ng.form10.name\"]").fill("Industry-1")
    page.get_by_role("button", name="Сохранить").click()
    expect(page.locator("#cdk-drop-list-19")).to_contain_text("Industry-1")
