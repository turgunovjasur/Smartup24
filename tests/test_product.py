from playwright.sync_api import Page, expect

from flows.flow_navbar import flow_navigate


def test_product(page: Page) -> None:
    flow_navigate(page, tab="Модератор", name="Товары")

    expect(page.locator("app-form-stack-widget")).to_contain_text("Товары")
    page.get_by_role("button", name="Создать").click()
    expect(page.locator("app-form-stack-widget")).to_contain_text("Продукт (создание)")
    page.locator("input[name=\"ng.form17.name\"]").click()
    page.locator("input[name=\"ng.form17.name\"]").fill("product-1")
    page.locator("input[name=\"ng.form17.short_name\"]").click()
    page.locator("input[name=\"ng.form17.short_name\"]").fill("pr1")
    page.locator("input[name=\"ng.form17.code\"]").click()
    page.locator("input[name=\"ng.form17.code\"]").fill("code-pr1")
    page.get_by_role("article").filter(has_text="Название * Краткое название * Код Производитель * Регион производство Подбор Ста").get_by_placeholder("Подбор").click()
    page.get_by_text("Manufacturer-").click()
    page.locator("smt-control").filter(has_text="measure *").get_by_placeholder("Подбор").click()
    page.get_by_text("кг").click()
    page.locator("button").filter(has_text="Характеристика").click()
    page.get_by_text("Подбор").nth(1).click()
    page.get_by_text("Category-").click()
    page.locator("smt-control").filter(has_text="Отрасль").get_by_placeholder("Подбор").click()
    page.get_by_text("Industry-").click()
    page.get_by_role("button", name="Сохранить").click()
    expect(page.locator("app-form-stack-widget")).to_contain_text("Товары")
    expect(page.locator("#cdk-drop-list-34")).to_contain_text("product-1")
