import allure
from playwright.sync_api import Page, expect
from conftest import load_data, page
from flow_authorization import authorization


@allure.title("Zakazni statusni change qilish ")
def test_order_change_status(page: Page, load_data) -> None:
    i = load_data("client_pass")
    # i = "auto_test1181"
    authorization(page, email=f"{i}@sm24", password="1")

    with allure.step("1,) zakaz statusni Новый dan Принято ga otkazish  "):
        page.get_by_role("link", name="Поставщик").click()
        page.get_by_role("link", name="Заказы").click()
        i = load_data("client_pass")
        page.locator(".w-100.alert").click()
        page.get_by_role("button", name=" Принято").click()
        page.get_by_role("button", name="да").click()



    with allure.step("8 ) zakaz statusni Принято dan Выполняется ga o`tkazish  "):
        page.get_by_role("link", name="Поставщик").click()
        page.get_by_role("link", name="Заказы").click()
        page.locator(".w-100.alert").click()
        page.get_by_role("button", name=" Выполняется").click()
        page.get_by_role("button", name="да").click()


    with allure.step("9 ) zakaz statusni Выполняется dan В сборке ga o`tkazish  "):
        page.get_by_role("link", name="Поставщик").click()
        page.get_by_role("link", name="Заказы").click()
        page.locator(".w-100.alert").first.click()
        page.get_by_text("В сборке", exact=True).first.click()
        page.get_by_role("button", name="да").click()
        page.locator(".tbl-row").first.click()


    with allure.step("10 ) zakaz statusni В сборке dan В пути ga o`tkazish"):
        page.get_by_role("link", name="Поставщик").click()
        page.get_by_role("link", name="Заказы").click()
        page.locator(".w-100.alert").first.click()
        page.get_by_role("button", name=" В пути").click()
        page.get_by_role("button", name="да").click()
        page.locator(".tbl-row").first.click()


    with allure.step("11 ) zakaz statusni В пути dan Доставлено ga o`tkazish"):
        page.get_by_role("link", name="Поставщик").click()
        page.get_by_role("link", name="Заказы").click()
        page.wait_for_load_state("networkidle")
        page.locator(".w-100.alert").click()
        page.get_by_role("button", name=" Доставлено").click()
        page.get_by_role("button", name="да").click()
        page.locator(".tbl-row").first.click()


    with allure.step("14 ) zakaz statusni Доставлено dan Завершен ga o`tkazish"):
        page.get_by_role("link", name="Поставщик").click()
        page.get_by_role("link", name="Заказы").click()
        page.locator(".w-100.alert").click()
        page.get_by_role("button", name=" Завершен").click()
        page.get_by_role("button", name="да").click()
        page.locator(".tbl-row").first.click()


    # with allure.step("sm24 da urulgan zakazni view tugmasni bosib kirib malumotlarni tekshirish"):
    #     page.get_by_role("link", name="Поставщик").click()
    #     page.get_by_role("link", name="Заказы").click()
    #     page.get_by_text("Узбекский сум").click()
    #     page.get_by_role("button", name="Просмотреть").click(force=True)





#     with allure.step("sm24 da urulgan zakazni edit qilish"):
#         page.get_by_role("link", name="Поставщик").click()
#         page.get_by_role("link", name="Заказы").click()
#         page.get_by_text("Узбекский сум").click()
#         page.get_by_role("button", name="Изменить", exact=True).click()
#         page.get_by_role("button", name=" Далее").click()
#         expect(page.locator("#kt_content")).to_contain_text("Заказ (изменение)")
#         page.get_by_role("textbox").nth(2).click()
#         page.get_by_role("textbox").nth(2).press("ArrowRight")
#         page.get_by_role("textbox").nth(2).fill("2")
#         page.get_by_role("button", name=" Далее").click()
#         expect(page.locator("#payment")).to_contain_text("Оплата")
#         page.locator(".edit").click()
#         page.get_by_text("Перечисление").click()
#         page.get_by_role("button", name=" Сохранить").click()




