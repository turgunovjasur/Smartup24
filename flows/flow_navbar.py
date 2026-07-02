from playwright.sync_api import expect
from playwright.sync_api import Page


def flow_menu(page) -> None:
    page.locator('//smt-button-group-item[@smtvalue="menu"]').click()
    page.get_by_role("menuitem", name="Настройки поиска").click()
    checkbox = page.get_by_role("checkbox").nth(1)
    if not checkbox.is_checked():
        page.get_by_role("checkbox").nth(1).click()
    page.get_by_role("button", name="Сохранить").click()


def flow_search(page: Page, name) -> None:
    page.get_by_role("searchbox", name="Поиск").click()
    page.get_by_role("searchbox", name="Поиск").fill(name)
    page.get_by_role("searchbox", name="Поиск").press("Enter")
    expect(page.locator("#cdk-drop-list-1")).to_contain_text(name)


def flow_navigate(page: Page, tab, name) -> None:
    page.get_by_role("button", name=tab).click()
    page.get_by_role("menuitem", name=name).click()
