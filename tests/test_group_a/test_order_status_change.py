import allure
from playwright.sync_api import Page

from flows.flow_authorization import COMPANY_CODE, authorization
from flows.flow_navbar import flow_navigate
from utils.base_page import BasePage

# Order hayot sikli — "Изменить статус" menyusida har safar joriy statusdan
# keyingi bosqich tanlanadi; order run_order da ЧЕРНОВИК statusida yaratiladi
# (create formasida status endi tanlanmaydi), Завершен yakuniy. "Принято"
# UI'dan olib tashlangan, "Отменён" qo'shilgan (menyuda bor, zanjirda
# ishlatilmaydi) — MCP tasdiqlangan 2026-07-17.
STATUS_CHAIN = ("Черновик", "Новый", "Выполняется", "В сборке", "В пути", "Доставлено", "Завершен")


def run_order_status_change(page: Page, code) -> None:
    """Group A: postavshik foydalanuvchisi nomidan run_order yaratgan Заказ
    statusini to'liq hayot sikli bo'ylab o'zgartiradi:
    Черновик → Новый → Выполняется → В сборке → В пути → Доставлено → Завершен.

    supplier_user-{code} bilan login qilingan bo'lishi kerak (run_supplier_user
    yaratadi va "Админ (Поставщик)" rolini beradi); order qatori ro'yxatda
    client-{code} (savdo nuqtasi) nomi bilan topiladi va Черновик statusda
    turishi kutiladi (run_order statusga tegmaydi)."""
    m = BasePage(page)
    client_name = f"client-{code}"

    with allure.step("Навигация: Поставщик → Заказы"):
        flow_navigate(page, tab="Поставщик", name="Заказы")
        m.expect_heading("Заказы")

    for current, target in zip(STATUS_CHAIN, STATUS_CHAIN[1:]):
        with allure.step(f"Статус: {current} → {target}"):
            # Bu ro'yxatda qatordagi klient/savdo nuqtasi kataklari BUTTON —
            # bosilsa "Клиент (Просмотр)" sahifasiga olib ketadi, shuning uchun
            # click_grid_row (chap katak x=120 — aynan shu tugma ustiga tushadi)
            # ISHLATILMAYDI; qator JORIY status katagi (oddiy matn, qatorda
            # yagona) orqali tanlanadi (MCP tasdiqlangan 2026-07-13).
            m._settle()
            row = m.grid_row(client_name, current)
            cell = row.get_by_text(current, exact=True)
            cell.click()
            # click_grid_row dagi kabi tanlov toggle himoyasi: action panel
            # ochilmagan bo'lsa bir marta qayta bosamiz.
            for _ in range(10):
                if m._grid_row_selected(row):
                    break
                page.wait_for_timeout(300)
            else:
                cell.click()
            m.change_status(target)
            m.grid_row(client_name, target)


@allure.epic("Поставщик")
@allure.feature("Group A")
@allure.story("Изменение статуса заказа")
@allure.title("Group A: Заказ statusini Новый dan Завершен gacha o'tkazish")
def test_order_status_change(page: Page, code) -> None:
    with allure.step("Tizimga kirish (postavshik foydalanuvchisi)"):
        # To'liq login = "<Логин>@<kompaniya kodi>" (admin@sm24 bilan bir xil format)
        authorization(page, email=f"supplier_user-{code}@{COMPANY_CODE}", password="1")
    run_order_status_change(page, code)
