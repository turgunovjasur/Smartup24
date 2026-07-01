from playwright.sync_api import Page, expect

from flows.flow_navbar import flow_navigate


def test_manufacturer(page: Page) -> None:
    flow_navigate(page, tab="Модератор", name="Товары")

    expect(page.locator("app-form-stack-widget")).to_contain_text("Товары")
    page.get_by_role("link", name="Производители").click()
    expect(page.locator("app-form-stack-widget")).to_contain_text("Производители")
    page.get_by_role("button", name="Создать").click()
    expect(page.locator("app-form-stack-widget")).to_contain_text("Производитель (Создание)")
    page.locator("input[name=\"ng.form5.name\"]").click()
    page.locator("input[name=\"ng.form5.name\"]").click()
    page.locator("input[name=\"ng.form5.name\"]").fill("Manufacturer-1")
    page.get_by_role("button", name="Сохранить").dblclick()
    expect(page.locator("app-form-stack-widget")).to_contain_text("Производители")
    expect(page.locator("#cdk-drop-list-6")).to_contain_text("Manufacturer-1")
