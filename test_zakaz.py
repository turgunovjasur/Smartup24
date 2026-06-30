import random
import re
from datetime import datetime, timedelta

import allure
from playwright.sync_api import Page, expect
from flow_authorization import authorization


def open_view(page: Page, row_text: str | None = None) -> None:
    view_btn = page.get_by_role("button", name="Просмотреть")
    for _ in range(6):
        try:
            view_btn.wait_for(state="visible", timeout=5000)
            view_btn.click(timeout=5000)
            return
        except Exception:
            if row_text is not None:
                try:
                    page.get_by_text(row_text).first.click(timeout=5000)
                except Exception:
                    pass
            page.wait_for_timeout(1000)
    view_btn.click(timeout=5000)


def _dismiss_overlay(page: Page) -> None:
    """Ochiq qolgan cdk overlay backdrop'ini yopadi.

    Bir dropdown tanlangach overlay ba'zan yopilmay qoladi va keyingi click'ni
    to'sadi (`cdk-overlay-backdrop ... intercepts pointer events`). Backdrop
    ko'rinib turgan bo'lsa Escape bilan yopamiz.
    """
    if page.locator(".cdk-overlay-backdrop.cdk-overlay-backdrop-showing").count() > 0:
        page.keyboard.press("Escape")
        page.wait_for_timeout(300)


def _select_field(page: Page, label: str, option: str, search: str | None = None,
                  exact: bool = True) -> None:
    _dismiss_overlay(page)  # oldingi dropdown overlay'i ochiq qolgan bo'lsa yopamiz
    ctl = page.locator("smt-control").filter(has_text=label)
    trg = ctl.locator("smt-select-trigger")
    if trg.count() > 0:
        trg.first.click()
    else:
        ph = ctl.get_by_placeholder("Выбрать")
        if ph.count() > 0:
            ph.first.click()
        else:
            ctl.get_by_text("Выбрать", exact=True).first.click()
    page.wait_for_timeout(800)
    ov = page.locator(".cdk-overlay-container")
    if search:
        sb = ov.get_by_role("textbox", name="Поиск")
        if sb.count() > 0:
            sb.first.fill(search)
            page.wait_for_timeout(500)
    ov.get_by_text(option, exact=exact).first.click()
    page.wait_for_timeout(900)
    _dismiss_overlay(page)  # bu tanlovning overlay'i ochiq qolsa, keyingisi uchun yopamiz


def _select_region_uz(page: Page) -> None:
    """Регион (ixtiyoriy) maydonida Узбекистан ni tanlaydi va overlay'ni yopadi."""
    _dismiss_overlay(page)
    page.locator("smt-select-trigger").filter(has_text="Регион").click()
    page.get_by_role("textbox", name="Поиск").fill("у")
    page.get_by_role("treeitem", name="Свернуть Узбекистан").click()
    page.wait_for_timeout(400)
    page.keyboard.press("Escape")
    page.wait_for_timeout(400)


def _select_industry_prod(page: Page) -> None:
    """'Характеристика товаров' bo'limida Отрасль = Продовольствие ni tanlaydi.

    Maydon endi 'Выбрать' textboxsiz smt-multi-data-select — input'ni bosib,
    ochilgan overlay'dan variantni tanlaymiz.
    """
    _dismiss_overlay(page)
    page.locator("button").filter(has_text="Характеристика товаров").click()
    page.wait_for_timeout(1000)
    page.locator("smt-multi-data-select input").first.click()
    page.wait_for_timeout(900)
    page.locator(".cdk-overlay-container").get_by_text(
        "Продовольствие", exact=False).first.click()
    page.wait_for_timeout(500)
    page.keyboard.press("Escape")


def _search_open(page: Page, text: str) -> None:
    """Ro'yxat qidiruvida `text` ni topib ochadi.

    `fill()` o'zi fokuslaydi — saqlashdan keyingi navigatsiya paytida osilib
    qoladigan ortiqcha `searchbox.click()` ishlatilmaydi. "1/1" natija
    ko'rsatkichini kutib, ishonchli ravishda ochamiz.
    """
    page.get_by_role("searchbox", name="Поиск").fill(text)
    expect(page.locator("text=1/1").first).to_be_visible(timeout=15000)
    page.get_by_text(text, exact=False).first.click()


@allure.title("sm24 da to'liq zakaz oqimi (supplier -> client -> tavar -> zakaz)")
def test_zakaz(page: Page) -> None:
    authorization(page)
    a = random.randint(1000, 9999)
    print(f"[test_zakaz] unique suffix a={a} | supplier=test_supplier_zakaz{a} "
    f""f"client=test_client_zakaz{a} tavar=test_tavar{a} client_user=client_user{a}")
    allure.attach(str(a), name="unique_suffix_a", attachment_type=allure.attachment_type.TEXT)
    page.get_by_role("link", name="Модератор", exact=True).or_(
    page.get_by_role("button", name="Модератор", exact=True)).first.click()
    page.get_by_role("link", name="Поставщики", exact=True).or_(
    page.get_by_role("menuitem", name="Поставщики", exact=True)).first.click()
    expect(page.locator("app-form-stack-widget")).to_contain_text("Поставщики")
    page.get_by_role("button", name="Создать").click()
    page.locator("smt-input[smtid=\"name\"] input").fill(f"test_supplier_zakaz{a}")
    page.locator("smt-input[smtid=\"short_name\"] input").fill("test_supplier_zakaz")
    _select_field(page, "Форма собственности", "MCHJ", exact=False)
    page.locator("smt-input[smtid=\"tin\"] input").fill(f"85236{a}")
    page.locator("label").filter(has_text="Поставщик").nth(1).click()
    _select_region_uz(page)
    _select_industry_prod(page)
    note = page.get_by_role("textbox", name="Примечание")
    if note.count():
        note.first.fill("zakaz testlash uchun yartilndi")
    page.get_by_role("button", name="Сохранить").click()
    _search_open(page, f"test_supplier_zakaz{a}")



    with allure.step("sm24 supplierga user yaratish"):
        open_view(page, f"test_supplier_zakaz{a}")
        page.locator("button").filter(has_text="Пользователи").click()
        page.get_by_role("button", name="Создать").click()
        expect(page.locator("h1")).to_contain_text("Пользователь (Создания)")
        page.locator("smt-input[smtid=\"name\"] input").fill(f"supplier_user{a}")
        page.locator("smt-input[smtid=\"position_name\"] input").click()
        # login/parol maydonlari bosilmaguncha readonly — fill'dan oldin click shart
        page.locator("input[name=\"supplier_user_login_input\"]").click()
        page.locator("input[name=\"supplier_user_login_input\"]").fill(f"supplier_user{a}")
        page.locator("smt-phone-input input[type=\"text\"]").fill(f"+9989{a}{a}")
        page.locator("smt-multi-data-select").get_by_role("textbox", name="Поиск").click()
        page.get_by_text("Админ (Поставщик)").click()
        page.locator("input[name=\"supplier_user_password_input\"]").click()
        page.locator("input[name=\"supplier_user_password_input\"]").fill("1")
        page.get_by_role("button", name="Сохранить").click()
        page.locator("button").filter(has_text="Пользователи").click()
        expect(page.get_by_text("supplier_user")).to_be_visible()



    with allure.step("sm24 da client yartish"):
        page.get_by_role("button", name="Модератор").click()
        page.get_by_role("menuitem", name="Клиенты", exact=True).click()
        page.wait_for_url("**/moderator/client**", timeout=10000)
        expect(page.locator("h1")).to_contain_text("Клиенты", timeout=10000)
        page.get_by_role("button", name="Создать").click()
        expect(page.locator("h1")).to_contain_text("Юр. Лицо (Создания)", timeout=10000)
        page.locator("smt-input[smtid=\"name\"] input").fill(f"test_client_zakaz{a}")
        page.locator("smt-input[smtid=\"short_name\"] input").fill(f"test_client_zakaz{a}")
        _select_field(page, "Форма собственности", "MCHJ", exact=False)
        page.locator("smt-input[smtid=\"tin\"] input").fill(f"8{a}{a}")
        page.locator("label").filter(has_text="Клиент").nth(1).click()
        _select_region_uz(page)
        _select_industry_prod(page)
        note = page.get_by_role("textbox", name="Примечание")
        if note.count():
            note.first.fill("zakaz urush uchun yartilingan client")
        page.get_by_role("button", name="Сохранить").click()
        _search_open(page, f"test_client_zakaz{a}")



    with allure.step("sm24 da clientga user yaratish"):
        open_view(page, f"test_client_zakaz{a}")
        page.locator("button").filter(has_text="Пользователи").click()
        page.get_by_role("button", name="Создать").click()
        page.locator("smt-input[smtid=\"name\"] input").fill(f"client_user{a}")
        # login/parol maydonlari bosilmaguncha readonly — fill'dan oldin click shart
        page.locator("input[name=\"client_user_login_input\"]").click()
        page.locator("input[name=\"client_user_login_input\"]").fill(f"client_user{a}")
        page.locator("input[name=\"client_user_password_input\"]").click()
        page.locator("input[name=\"client_user_password_input\"]").fill("1")
        role_control = page.locator("smt-control").filter(has_text="Роли")
        role_control.get_by_placeholder("Поиск").click()
        role_control.get_by_placeholder("Поиск").fill("Админ (Клиент)")
        page.get_by_role("menuitemcheckbox", name="Админ (Клиент)").click()
        expect(role_control).to_contain_text("Админ (Клиент)")
        page.locator("smt-phone-input input[type=\"text\"]").fill(f"+9983{a}{a}")
        outlet_control = page.locator("smt-control").filter(has_text="Торговые точки")
        outlet_control.get_by_placeholder("Поиск").click()
        outlet_control.get_by_placeholder("Поиск").fill(f"test_client_zakaz{a}")
        page.get_by_role("menuitemcheckbox", name=f"test_client_zakaz{a}").click()
        page.get_by_role("button", name="Сохранить").click()
        page.wait_for_url("**/client/client_view**", timeout=10000)
        page.locator("button").filter(has_text="Пользователи").click()
        _search_open(page, f"client_user{a}")



    with allure.step("sm24 da supplierni client bilan ulash"):
        page.get_by_role("button", name="Модератор").click()
        page.get_by_role("menuitem", name="Поставщики", exact=True).click()
        _search_open(page, f"test_supplier_zakaz{a}")
        open_view(page, f"test_supplier_zakaz{a}")
        def goto_recommended() -> None:
            # Yangi UI: "Рекомендованные клиенты" endi "Получатель" tabi ostida
            page.locator("button").filter(has_text="Получатель").click()
            page.wait_for_timeout(800)
            page.locator("button").filter(has_text="Рекомендованные клиенты").click()
            page.wait_for_timeout(800)
        goto_recommended()
        rec_search = page.get_by_role("searchbox", name="Поиск")
        for _ in range(12):
            rec_search.fill(f"test_client_zakaz{a}")
            try:
                expect(page.locator("text=1/1").first).to_be_visible(timeout=5000)
                break
            except AssertionError:
                page.wait_for_timeout(5000)
                page.reload()
                page.wait_for_load_state("networkidle")
                goto_recommended()
        else:
            expect(page.locator("text=1/1").first).to_be_visible(timeout=5000)
        send_btn = page.get_by_role("button", name="Отправить запрос на сотрудничество")
        for _ in range(6):
            page.get_by_text(f"test_client_zakaz{a}").first.click()
            try:
                send_btn.click(timeout=5000)
                break
            except Exception:
                page.wait_for_timeout(1500)
        page.get_by_role("button", name="да").click()
        page.get_by_role("button", name="Модератор").click()
        page.get_by_role("menuitem", name="Клиенты", exact=True).click()
        _search_open(page, f"test_client_zakaz{a}")
        open_view(page, f"test_client_zakaz{a}")
        def goto_supplier_requests() -> None:
            page.locator("button").filter(has_text="Запросы на сотрудничество").click()
            page.wait_for_timeout(600)
            page.locator("button").filter(has_text="Запросы поставщиков").click()
            page.wait_for_timeout(600)
        goto_supplier_requests()
        # So'rov supplier tomondan endigina yuborilgan — ro'yxatda paydo bo'lishini
        # qidirib kutamiz (kechiksa, sahifani yangilab qayta urinamiz).
        sup_search = page.get_by_role("searchbox", name="Поиск")
        for _ in range(8):
            sup_search.fill(f"test_supplier_zakaz{a}")
            try:
                expect(page.locator("text=1/1").first).to_be_visible(timeout=5000)
                break
            except AssertionError:
                page.wait_for_timeout(4000)
                page.reload()
                page.wait_for_load_state("networkidle")
                goto_supplier_requests()
                sup_search = page.get_by_role("searchbox", name="Поиск")
        confirm = page.get_by_role("button", name="Подтвердить")
        for _ in range(6):
            page.get_by_text(f"test_supplier_zakaz{a}").first.click()
            try:
                confirm.click(timeout=5000)
                break
            except Exception:
                page.wait_for_timeout(1000)
        page.get_by_role("button", name="да").click()




    with allure.step("sm24 da tavar yaratish"):
        page.get_by_role("button", name="Модератор").click()
        page.get_by_role("menuitem", name="Товары", exact=True).click()
        page.get_by_role("button", name="Создать").click()
        page.wait_for_timeout(2000)
        page.locator('smt-input[smtid="name"] input').fill(f"test_tavar{a}")
        page.locator('smt-input[smtid="short_name"] input').fill(f"test_tavar{a}")

        _select_field(page, "measure *", "бл")
        _select_field(page, "Производитель", "Energy Drink")
        _select_field(page, "Регион производство", "Узбекистан", search="у")

        page.locator("button").filter(has_text="Характеристика").first.click()
        page.wait_for_timeout(1000)
        _select_field(page, "Категории", "Снеки")
        _select_field(page, "Отрасль", "Продовольствие")

        # Async-forma saqlashi flaky: majburiy maydon defaultlari yuklanmasdan
        # Сохранить bosilsa $save jim ketmaydi va sahifa product+add'da qoladi.
        # Sahifa create formadan chiqib ketgunча qayta bosamiz.
        for _ in range(4):
            page.get_by_role("button", name="Сохранить").click()
            try:
                page.wait_for_url(
                    lambda url: "product%2badd" not in url.lower()
                    and "product+add" not in url.lower(),
                    timeout=8000,
                )
                break
            except Exception:
                page.wait_for_timeout(1500)
        _search_open(page, f"test_tavar{a}")



    with allure.step("sm24 da tavarni supplierga ulash , narx biriktrish va v nalichiga o`tkazish"):
        page.get_by_role("button", name="Модератор").click()
        page.get_by_role("menuitem", name="Поставщики", exact=True).click()
        _search_open(page, f"test_supplier_zakaz{a}")
        open_view(page, f"test_supplier_zakaz{a}")
        page.locator("button").filter(has_text=re.compile(r"^Товары$")).click()
        page.get_by_role("button", name="Прикрепить").click()
        attach_search = page.get_by_role("searchbox", name="Поиск")
        attach_btn = page.locator("[id^='cdk-drop-list-']").filter(
            has_text=f"test_tavar{a}"
        ).get_by_role("button", name="Прикрепить").first
        for _ in range(6):
            attach_search.click()
            attach_search.fill("")
            attach_search.fill(f"test_tavar{a}")
            try:
                attach_btn.click(timeout=5000)
                break
            except Exception:
                page.wait_for_timeout(1500)
        else:
            attach_btn.click(timeout=5000)
        page.get_by_role("button", name="Сохранить").click()
        page.get_by_role("button", name="да").click()
        page.locator("button").filter(has_text=re.compile(r"^Товары$")).click()
        page.get_by_text(f"test_tavar{a}").click()
        page.get_by_role("button", name="В наличие").click()
        page.get_by_role("button", name="да").click()
        page.locator("button").filter(has_text="Тип цены").click()
        page.get_by_text("Цена по умолчанию").click()
        page.get_by_role("button", name="Установить цену").click()
        page.get_by_role("spinbutton").click()
        page.get_by_role("spinbutton").fill("15000")
        page.get_by_role("button", name="Сохранить").click()
        page.locator("button").filter(has_text=re.compile(r"^Товары$")).click()



    with allure.step("sm24 ga client user bob kirish va zakaz yaratish"):
        authorization(page, email=f"client_user{a}@sm24", password="1")
        page.get_by_role("link", name="Клиент", exact=True).or_( page.get_by_role("button", name="Клиент", exact=True)).first.click()
        page.get_by_role("link", name="Заказы", exact=True).or_(page.get_by_role("menuitem", name="Заказы", exact=True)).first.click()
        page.get_by_role("button", name="Создать").click()
        page.locator("smt-control").filter(has_text="Торговые точки *").get_by_placeholder("Выберите").click()
        page.get_by_text(f"test_client_zakaz{a}").click()
        page.locator("smt-control").filter(has_text="Поставщики *").get_by_placeholder("Выберите").click()
        page.get_by_text(f"test_supplier_zakaz{a}").click()
        page.locator("smt-control").filter(has_text="Время доставки *").get_by_test_id("smt-date-picker-input").click()
        # Yetkazish vaqti har doim kelajakda bo'lishi kerak — aks holda "ДАЛЕЕ" oldinga o'tmaydi.
        # Qattiq sana o'rniga dinamik (ertaga peshin) qo'yamiz, shunda test eskirmaydi.
        delivery_time = (datetime.now() + timedelta(days=1)).strftime("%d.%m.%Y 12:00")
        page.locator("smt-control").filter(has_text="Время доставки *").get_by_test_id("smt-date-picker-input").fill(delivery_time)
        page.get_by_role("button", name="ДАЛЕЕ").click()
        # Товар qidirish maydoni: yangi UI'da searchbox yoki textbox bo'lishi mumkin,
        # bosqich o'tishi esa asinxron — paydo bo'lishini kutamiz.
        tavar_search = page.get_by_role("searchbox", name="Поиск").or_(
            page.get_by_role("textbox", name="Поиск")
        ).first
        tavar_search.wait_for(state="visible", timeout=15000)
        tavar_search.click()
        page.get_by_text(f"test_tavar{a}").click()
        page.wait_for_timeout(800)
        page.locator("#null").nth(1).click()
        page.locator("#null").nth(1).fill("2")
        page.get_by_role("button", name="ДАЛЕЕ").click()
        page.wait_for_timeout(1500)
        page.get_by_role("textbox", name="Выберите").click()
        page.wait_for_timeout(800)
        page.locator("div").filter(has_text="Наличные").nth(5).click()
        page.wait_for_timeout(800)
        # to'lov turi dropdown overlay'i ba'zan ochiq qolib, keyingi trigger
        # clickini to'sadi — Escape bilan yopamiz
        page.keyboard.press("Escape")
        page.wait_for_timeout(500)
        page.locator("smt-select-trigger").filter(has_text="Черновик").first.click()
        page.wait_for_timeout(1200)
        page.locator(".cdk-overlay-container").get_by_text("Новый", exact=True).first.click()
        page.wait_for_timeout(1000)
        _save = page.get_by_role("button", name="Сохранить")
        (_save.nth(1) if _save.count() > 1 else _save.first).click()
        page.get_by_text(f"test_supplier_zakaz{a}").first.click()
        open_view(page, f"test_supplier_zakaz{a}")

    with allure.step("sm24 da urulgan zakaz moderator tomonda ko'rinishini tekshirish"):
        authorization(page)
        page.get_by_role("link", name="Модератор", exact=True).or_(page.get_by_role("button", name="Модератор", exact=True)).first.click()
        page.get_by_role("link", name="Заказы", exact=True).or_(page.get_by_role("menuitem", name="Заказы", exact=True)).first.click()
        # Zakazlar ro'yxati yuklanganini qidiruv maydoni orqali tasdiqlaymiz
        # (ro'yxat sahifasida "Заказы" sarlavhasi heading rolida emas).
        sb = page.get_by_role("searchbox", name="Поиск")
        expect(sb).to_be_visible(timeout=15000)
        sb.fill(f"test_supplier_zakaz{a}")
        # Client tomonidan yaratilgan zakaz moderator tomonda supplier nomi bilan
        # ko'rinishini tasdiqlaymiz — bu bosqichning asosiy maqsadi.
        expect(page.get_by_text(f"test_supplier_zakaz{a}").first).to_be_visible(timeout=15000)
        page.get_by_role("button", name=f"test_supplier_zakaz{a}").first.click()
        expect(page.get_by_text("Поставщик (Просмотр)").first).to_be_visible(timeout=15000)
        # yakuniy tozalash — panelni yopamiz (tekshiruv allaqachon o'tdi)
        try:
            page.get_by_role("button", name="Go back").click()
        except Exception:
            page.keyboard.press("Escape")
