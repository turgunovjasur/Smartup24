from playwright.sync_api import Page, expect

from flows.flow_navbar import flow_navigate


def test_category(page: Page) -> None:
    flow_navigate(page, tab="Модератор", name="Товары")

    page.get_by_role("link", name="Характеристика товаров").click()
    expect(page.locator("app-form-stack-widget")).to_contain_text("Характеристика товаров")
    page.get_by_text("Категория").click()
    page.get_by_role("button", name="Подтипы").click()
    expect(page.locator("app-form-stack-widget")).to_contain_text("Категория")
    page.get_by_role("button", name="Создать").click()
    expect(page.locator("app-form-stack-widget")).to_contain_text("Характеристика товаров (создание)")
    page.locator("input[name=\"ng.form16.name\"]").click()
    page.locator("input[name=\"ng.form16.name\"]").fill("Category-1")
    page.get_by_role("button", name="Сохранить").click()
    expect(page.locator("app-form-stack-widget")).to_contain_text("Категория")
    expect(page.locator("#cdk-drop-list-32")).to_contain_text("Category-1")
