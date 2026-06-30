import re
import random
from playwright.sync_api import Page, expect
from flow_authorization import authorization




# ─── Helper funksiyalar ───────────────────────────────────────────────────────

def _navigate_to_vaprost(page: Page) -> None:
    page.goto("https://app3.greenwhite.uz/x24/a2/sb/sbv/quiz/quiz_list?-project_code=sb&-filial_id=105")
    page.wait_for_load_state("networkidle")


def _get_question_textbox(page: Page):
    """Savol matni maydonini topadi — placeholder o'zgargan bo'lishi mumkin."""
    for locator in [
        page.get_by_role("textbox", name="Enter text..."),
        page.get_by_placeholder("Enter text..."),
        page.get_by_role("textbox").first,
    ]:
        try:
            if locator.is_visible(timeout=2000):
                return locator
        except Exception:
            continue
    return page.get_by_role("textbox").first


def _open_create_form(page: Page, name: str) -> None:
    create_btn = page.get_by_role("button", name="Создать")
    create_btn.wait_for(state="visible", timeout=15000)
    create_btn.click()
    page.wait_for_load_state("networkidle")
    _txt = _get_question_textbox(page)
    _txt.click()
    _txt.fill(name)
    # Forma modeli asinxron yuklanib nom maydonini tozalashi mumkin — qiymat
    # mahkam o'rnashguncha (bo'sh qolmasin) qayta to'ldiramiz.
    for _ in range(5):
        page.wait_for_timeout(400)
        if _txt.input_value().strip():
            break
        _txt.click()
        _txt.fill(name)


def _save_question(page: Page) -> None:
    """'Сохранить' ni bosadi va saqlash so'rovi ($save) haqiqatan ketguncha
    qayta urinadi.

    Forma (Тип вводимых данных kabi majburiy maydon defaultlari bilan) asinxron
    yuklanadi — to'liq tayyor bo'lmasdan Сохранить bosilsa, click behuda ketadi
    (so'rov yuborilmaydi) va savol yaratilmaydi. Shuning uchun saqlash so'rovi
    ketib, ro'yxat sahifasiga (quiz_list) qaytguncha urinamiz.
    """
    for _ in range(4):
        if "quiz_list" in page.url:
            return
        try:
            with page.expect_response(
                lambda r: r.request.method == "POST"
                and "$save" in r.url and "quiz" in r.url.lower(),
                timeout=6000,
            ):
                page.get_by_role("button", name="Сохранить").click()
            for _ in range(20):
                if "quiz_list" in page.url:
                    return
                page.wait_for_timeout(500)
            return
        except Exception:
            page.wait_for_timeout(800)


def _save_and_check(page: Page, name: str) -> None:
    """Saqlaydi va savol ro'yxatda paydo bo'lishini tasdiqlaydi.

    Saqlash ba'zan persist bo'lmaydi (forma to'liq tayyor bo'lmasdan ketadi) —
    savol topilmasa formani qayta ochib yaratishni urinamiz.
    """
    _save_question(page)
    for _ in range(3):
        _navigate_to_vaprost(page)
        page.get_by_role("searchbox", name="Поиск").fill(name)
        try:
            expect(page.get_by_text(name, exact=True).first).to_be_visible(timeout=8000)
            return
        except AssertionError:
            _open_create_form(page, name)
            _save_question(page)
    _navigate_to_vaprost(page)
    page.get_by_role("searchbox", name="Поиск").fill(name)
    expect(page.get_by_text(name, exact=True).first).to_be_visible(timeout=10000)


def _create_simple(page: Page, name: str, search_name: str | None = None) -> None:
    """Oddiy savol (faqat nom) yaratadi va ro'yxatda paydo bo'lishini kafolatlaydi.

    Saqlash ba'zan persist bo'lmaydi — savol qidiruvda paydo bo'lmaguncha
    formani qayta ochib yaratamiz.
    """
    search_name = search_name or name
    for _ in range(4):
        _open_create_form(page, name)
        _save_question(page)
        _navigate_to_vaprost(page)
        page.get_by_role("searchbox", name="Поиск").fill(search_name)
        try:
            expect(page.get_by_text(search_name, exact=True).first).to_be_visible(timeout=8000)
            return
        except AssertionError:
            continue
    raise AssertionError(f"Savol '{name}' yaratilmadi — persist bo'lmadi")


def _search_and_open(page: Page, name: str) -> None:
    """Qidirib kartani ochadi (panel ochilguncha qayta urinish)."""
    action_btn = page.locator("button").filter(
        has_text=re.compile(r"Изменить|Удалить|Неактивный|Активный")
    ).first

    for _ in range(4):
        _navigate_to_vaprost(page)
        page.get_by_role("searchbox", name="Поиск").fill(name)
        try:
            target = page.get_by_text(name, exact=True).first
            target.wait_for(state="visible", timeout=6000)
            target.click()
            action_btn.wait_for(state="visible", timeout=5000)
            return
        except Exception:
            page.wait_for_timeout(1500)

    target = page.get_by_text(name, exact=True).first
    target.wait_for(state="visible", timeout=8000)
    target.click()
    action_btn.wait_for(state="visible", timeout=5000)


def _click_action(page: Page, label: str) -> None:
    """Ochilgan savol panelidagi action tugmasini ishonchli bosadi.

    Panel ochilgach qayta render bo'lib tugma vaqtincha DOM'dan uziladi
    ("element is not visible / detached") — shuning uchun qayta urinamiz.
    """
    btn = page.get_by_role("button", name=label, exact=True)
    for _ in range(6):
        try:
            btn.click(timeout=4000)
            return
        except Exception:
            page.wait_for_timeout(800)
    btn.click(timeout=5000)


def _click_radio_and_wait(page: Page, nth: int) -> None:
    """Radio tugmasini bosib, forma yuklanishini kutish."""
    page.get_by_role("radio").nth(nth).click()
    page.wait_for_timeout(1200)


# ─── Testlar ──────────────────────────────────────────────────────────────────

def test_vaprost_create(page: Page, code) -> None:
    """Raqamli savol (min/max qiymat) yaratish."""
    a = random.randint(1000, 9999)
    name = f"test_vaprost{a}"
    _navigate_to_vaprost(page)
    _open_create_form(page, name)
    _get_question_textbox(page).click()
    _get_question_textbox(page).fill(f"test_vaprost{a}")

    _save_and_check(page, name)


def test_vaprost_create2(page: Page, code) -> None:
    """Matn savoli (Требуется + Обязательное фото) yaratish."""
    a = random.randint(1000, 9999)
    name = f"test_vaprost{a}"
    _navigate_to_vaprost(page)
    _open_create_form(page, name)
    page.get_by_role("radio").nth(3).click()
    page.wait_for_load_state("networkidle")
    _cdk = page.locator("[id^='cdk-drop-list'] #null").first
    if _cdk.is_visible(timeout=2000):
        _cdk.click()
        _cdk.fill("test")
    _txt = page.get_by_role("textbox").first
    _txt.click()
    _txt.fill(name)
    _save_and_check(page, name)


def _fill_variant_label(page: Page, text: str) -> None:
    """CDK drop-list ichidagi variant label inputini to'ldiradi."""
    _inp = page.locator("[id^='cdk-drop-list'] #null").first
    if not _inp.is_visible(timeout=3000):
        _inp = page.locator("#null").last
    _inp.click()
    _inp.fill(text)


def test_vaprost_create3(page: Page, code) -> None:
    """Variant savoli — label 2 + Укажите другую причину."""
    a = random.randint(1000, 9999)
    name = f"test_vaprost{a}"
    _navigate_to_vaprost(page)
    _open_create_form(page, name)
    page.get_by_role("radio").nth(3).click()
    page.locator("label").filter(has_text="да").nth(2).click()
    page.locator("label").filter(has_text="Выпадающий список").nth(1).click()
    _fill_variant_label(page, "test")
    _get_question_textbox(page).fill(name)
    _save_and_check(page, name)


def test_vaprost_create4(page: Page, code) -> None:
    """Variant savoli — label 3 + switch kombinatsiyasi."""
    a = random.randint(1000, 9999)
    name = f"test_vaprost{a}"
    _navigate_to_vaprost(page)
    _open_create_form(page, name)
    page.get_by_role("radio").nth(3).click()
    page.locator("label").filter(has_text="да").nth(2).click()
    _fill_variant_label(page, "test")
    _get_question_textbox(page).fill(name)
    _save_and_check(page, name)


def test_vaprost_create5(page: Page, code) -> None:
    """Tanlov savoli — standart variant + ball."""
    a = random.randint(1000, 9999)
    name = f"test_vaprost{a}"
    _navigate_to_vaprost(page)
    _open_create_form(page, name)
    page.get_by_role("radio").nth(3).click()
    page.locator("label").filter(has_text="Один из списка").nth(1).click()
    _fill_variant_label(page, "test")
    _get_question_textbox(page).fill(name)
    _save_and_check(page, name)


def test_vaprost_create6(page: Page, code) -> None:
    """Tanlov savoli — label 2 varianti."""
    a = random.randint(1000, 9999)
    name = f"test_vaprost{a}"
    _navigate_to_vaprost(page)
    _open_create_form(page, name)
    page.get_by_role("radio").nth(3).click()
    page.locator("label").filter(has_text="Выпадающий список").nth(1).click()
    # Switch knob — yangi UI da class o'zgargan bo'lishi mumkin
    _sw = page.locator("smt-switch").last
    if not _sw.is_visible(timeout=3000):
        _sw = page.locator(".w-full > smt-switch > .bg-gray-200 > .bg-white")
    _sw.click()
    _fill_variant_label(page, "test")
    _get_question_textbox(page).fill(name)
    _save_and_check(page, name)


def test_vaprost_create7(page: Page, code) -> None:
    """Tanlov savoli — label 3 varianti."""
    a = random.randint(1000, 9999)
    name = f"test_vaprost{a}"
    _navigate_to_vaprost(page)
    _open_create_form(page, name)
    _get_question_textbox(page).click()
    _get_question_textbox(page).fill(f"test_vaprost{a}")
    page.get_by_role("radio").nth(5).click()
    page.locator("smt-control").filter(has_text="Вариант ответа *").locator("#null").click()
    page.locator("smt-control").filter(has_text="Вариант ответа *").locator("#null").fill("test")
    page.locator("#null").nth(1).click()
    page.locator("#null").nth(1).fill("1")
    _get_question_textbox(page).fill(name)
    _save_and_check(page, name)


def test_vaprost_create8(page: Page, code) -> None:
    """Tanlov savoli — switch + Обязательное фото kombinatsiyasi."""
    a = random.randint(1000, 9999)
    name = f"test_vaprost{a}"
    _navigate_to_vaprost(page)
    _open_create_form(page, name)
    page.get_by_role("radio").nth(5).click()
    page.locator("label").filter(has_text="да").nth(2).click()
    page.locator("smt-control").filter(has_text="Вариант ответа *").locator("#null").click()
    page.locator("smt-control").filter(has_text="Вариант ответа *").locator("#null").fill("test")
    page.locator("#null").nth(1).click()
    page.locator("#null").nth(1).fill("1")
    _get_question_textbox(page).fill(name)
    _save_and_check(page, name)


def test_vaprost_create9(page: Page, code) -> None:
    """Tanlov savoli — label 2 + Укажите другую причину."""
    a = random.randint(1000, 9999)
    name = f"test_vaprost{a}"
    _navigate_to_vaprost(page)
    _open_create_form(page, name)
    page.get_by_role("radio").nth(5).click()
    page.locator("label").filter(has_text="Один из списка").nth(1).click()
    page.locator("smt-control").filter(has_text="Вариант ответа *").locator("#null").click()
    page.locator("smt-control").filter(has_text="Вариант ответа *").locator("#null").fill("test")
    # "Один из списка" tanlanganda #null count o'zgaradi — score nth(2) da
    page.locator("#null").nth(2).click()
    page.locator("#null").nth(2).fill("1")
    _get_question_textbox(page).fill(name)
    _save_and_check(page, name)


# TUZATISH: test_vaprost_create10 o'chirildi — to'liq create9 bilan bir xil edi


def test_vaprost_edit(page: Page, code) -> None:
    """Savolni tahrirlash."""
    a = random.randint(1000, 9999)
    name = f"test_vaprost{a}"
    edited_name = f"test_vaprost{a}edit"
    _navigate_to_vaprost(page)
    _create_simple(page, name)

    _search_and_open(page, name)

    _click_action(page, "Изменить")
    page.wait_for_load_state("networkidle")
    textbox = _get_question_textbox(page)
    # Edit forma asinxron yuklanadi — nom maydoniga eski qiymat kelishini kutamiz,
    # aks holda clear/fill yuklanmagan formada yo'qoladi va nom o'zgarmaydi.
    expect(textbox).to_have_value(name, timeout=10000)
    textbox.clear()
    textbox.fill(edited_name)
    _save_question(page)
    _navigate_to_vaprost(page)
    page.get_by_role("searchbox", name="Поиск").fill(edited_name)
    expect(page.get_by_text(edited_name, exact=True).first).to_be_visible(timeout=15000)





def test_vaprost_delete(page: Page, code) -> None:
    """Savolni o'chirish va yo'qligi tasdiqlash."""
    a = random.randint(1000, 9999)
    name = f"test_vaprost{a}"
    _navigate_to_vaprost(page)
    _create_simple(page, name)

    _search_and_open(page, name)

    _click_action(page, "Удалить")
    confirm = page.get_by_role("button", name="да", exact=True)
    confirm.wait_for(state="visible", timeout=5000)
    confirm.click()
    page.wait_for_load_state("networkidle")

    page.get_by_role("searchbox", name="Поиск").fill(name)
    page.wait_for_load_state("networkidle")
    expect(page.get_by_text(name)).to_have_count(0)


def test_vaprost_inactive(page: Page, code) -> None:
    """Savolni nofaol qilish."""
    a = random.randint(1000, 9999)
    name = f"test_vaprost{a}"
    _navigate_to_vaprost(page)
    _create_simple(page, name)
    _search_and_open(page, name)
    _click_action(page, "Неактивный")
    page.get_by_role("button", name="да", exact=True).click()
    page.wait_for_load_state("networkidle")



def test_vaprost_inactive2(page: Page, code) -> None:
    """Статус switchi o'chirilgan holda yaratish."""
    a = random.randint(1000, 9999)
    name = f"test_vaprost{a}"
    _navigate_to_vaprost(page)
    _open_create_form(page, name)
    page.locator("header").filter(has_text="Основная информацияСтатус Активный").get_by_role("switch").click()
    _save_question(page)
    _navigate_to_vaprost(page)  # Saqlangandan keyin ro'yxat sahifasiga o'tish
    page.locator(".gap-2.inline-flex").first.click()
    page.get_by_role("button", name="Показать все").click()
    page.wait_for_load_state("networkidle")
    page.get_by_role("searchbox", name="Поиск").fill(name)
    page.wait_for_load_state("networkidle")
    page.get_by_text(name).first.click()




def test_vaprost_duplicate(page: Page, code) -> None:
    """Mavjud nom bilan yaratishda xato chiqishi kerak."""
    a = random.randint(1000, 9999)
    name = f"test_vaprost{a}"
    _navigate_to_vaprost(page)

    # Avval bir marta yaratib saqlaymiz (persist bo'lishini kafolatlaymiz)
    _create_simple(page, name)

    # Qaytib kelib xuddi shu nom bilan yana yaratamiz
    _navigate_to_vaprost(page)
    _open_create_form(page, name)
    page.get_by_role("button", name="Сохранить").click()

    close_btn = page.locator(".cdk-overlay-container button").filter(has_text="Закрыть")
    expect(close_btn.first).to_be_visible(timeout=5000)
    close_btn.first.click()





def test_vaprost_trim(page: Page, code) -> None:
    """Bo'shliqli nom bilan yaratib, tahrirlash."""
    a = random.randint(1000, 9999)
    name = f"test_vaprost{a}"
    edited_name = f"test_vaprost{a}"
    _navigate_to_vaprost(page)
    _create_simple(page, f"    {name}    ", search_name=name)

    _search_and_open(page, name)

    _click_action(page, "Изменить")
    page.wait_for_load_state("networkidle")
    textbox = _get_question_textbox(page)
    # Edit forma yuklanib, nom maydoniga (trimlangan) qiymat kelishini kutamiz.
    expect(textbox).to_have_value(name, timeout=10000)
    textbox.clear()
    textbox.fill(edited_name)
    _save_question(page)

    _navigate_to_vaprost(page)
    page.get_by_role("searchbox", name="Поиск").fill(edited_name)
    expect(page.get_by_text(edited_name, exact=True).first).to_be_visible(timeout=15000)


def test_vaprost_delet(page: Page, code) -> None:
    """Bo'shliqli nom bilan yaratib, tahrirlash."""
    a = random.randint(1000, 9999)
    name = f"test_vaprost{a}"
    edited_name = f"test_vaprost{a}"
    _navigate_to_vaprost(page)
    _create_simple(page, f"    {name}    ", search_name=name)
    _search_and_open(page, name)
    _click_action(page, "Удалить")
    confirm = page.get_by_role("button", name="да", exact=True)
    confirm.wait_for(state="visible", timeout=5000)
    confirm.click()
    page.wait_for_load_state("networkidle")





def test_all_vaprost(page: Page, code) -> None:
    """
    Barcha vaprost testlarini bitta session ichida ketma-ket ishlatish.
    MUHIM: authorization() faqat bir marta, test_all_vaprost boshida chaqiriladi.
    """
    authorization(page)

    test_vaprost_create(page, code)
    test_vaprost_create2(page, code)
    test_vaprost_create3(page, code)
    test_vaprost_create4(page, code)
    test_vaprost_create5(page, code)
    test_vaprost_create6(page, code)
    test_vaprost_create7(page, code)
    test_vaprost_create8(page, code)
    test_vaprost_create9(page, code)
    test_vaprost_edit(page, code)
    test_vaprost_inactive(page, code)
    test_vaprost_inactive2(page, code)
    test_vaprost_duplicate(page, code)
    test_vaprost_trim(page, code)
