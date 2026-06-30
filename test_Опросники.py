import re
import random
import traceback
from datetime import datetime
from playwright.sync_api import Page, expect
from flow_authorization import authorization

OPROSNIKI_URL = "https://app3.greenwhite.uz/x24/a2/sb/sbv/quiz/quiz_set_list?-project_code=sb&-filial_id=105"


# ─── Debug logging ────────────────────────────────────────────────────────────

def log(msg: str) -> None:
    """Debug log — pytest -s bilan terminalda ko'rinadi.

    Windows konsoli (cp1252) kirill harflarini chiqara olmasligi mumkin,
    shu sabab encode xatosida o'qib bo'lmaydigan belgilarni ? ga almashtiramiz.
    """
    line = f"[{datetime.now():%H:%M:%S}] {msg}"
    try:
        print(line, flush=True)
    except UnicodeEncodeError:
        print(line.encode("ascii", "replace").decode("ascii"), flush=True)


# ─── Helper funksiyalar ───────────────────────────────────────────────────────

def _go_to_oprosniki(page: Page) -> None:
    log(f"goto {OPROSNIKI_URL}")
    page.goto(OPROSNIKI_URL)
    page.wait_for_load_state("networkidle")


def _wait_form_ready(page: Page) -> None:
    """Forma ochilib, orqadagi ro'yxat DOM'dan chiqishini kutadi, so'ng nom
    maydonini aktivlashtiradi.

    Ro'yxat hali turgan bo'lsa, `#null` va `.bg-white...` selektorlari ro'yxat
    elementlariga (qidiruv input, satr checkboxlari) to'g'ri kelib qoladi —
    strict mode violation yoki noto'g'ri joyga click bo'ladi. Ro'yxatdagi
    qidiruv input yo'qolishi — forma to'liq ochilganining ishonchli belgisi.
    """
    page.get_by_role("searchbox", name="Поиск").wait_for(state="detached", timeout=15000)
    page.locator(".bg-white.box-border.duration-100").first.click()


def _save_form(page: Page) -> None:
    """«Сохранить»ni bosib, forma haqiqatan yopilganini tekshiradi.

    Saqlash jim muvaffaqiyatsiz bo'lsa (validatsiya/server xatosi), forma ochiq
    qoladi va keyingi qidiruv "topilmadi" bilan yiqiladi — sababi yashirinadi.
    Shu sabab xatoni shu yerda, overlay matni bilan birga ushlaymiz.
    """
    page.get_by_role("button", name="Сохранить").click()
    page.wait_for_load_state("networkidle")
    try:
        expect(page.get_by_role("button", name="Сохранить")).to_be_hidden(timeout=10000)
    except AssertionError:
        err = ""
        try:
            err = page.locator(".cdk-overlay-container").inner_text(timeout=1000).strip()
        except Exception:
            pass
        log(f"save xatosi: forma yopilmadi, overlay={err!r}")
        raise AssertionError(f"Saqlash muvaffaqiyatsiz — forma ochiq qoldi: {err or 'xato matni topilmadi'}")
    log("save OK — forma yopildi")


def _create_oprosniki(page: Page, name: str, status: str = "active") -> None:
    """Oprosniki yaratadi."""
    log(f"create oprosnik: name={name!r}, status={status}")
    _go_to_oprosniki(page)
    page.get_by_role("button", name="Создать").click()
    _wait_form_ready(page)
    page.locator("#null").fill(name)
    if status == "inactive":
        page.get_by_role("radio").nth(3).click()
    _save_form(page)


def _search_and_open(page: Page, name: str) -> None:
    """Ro'yxatda qidirib, kartani ochadi.

    Angular qatorni qayta render qilgani uchun bitta click ba'zan "tegmaydi" —
    action tugmalari (Просмотр/Изменить) paydo bo'lguncha qayta qidirib bosamiz.
    """
    action_btn = page.locator("button").filter(
        has_text=re.compile(r"Просмотр|Изменить|Удалить|Открыть")
    ).first

    last_error: Exception | None = None
    for attempt in range(1, 5):
        log(f"search_and_open {name!r}: urinish {attempt}/4")
        _go_to_oprosniki(page)
        search = page.get_by_role("searchbox", name="Поиск")
        search.click()
        search.fill("")
        # fill() o'rniga haqiqiy yozish — Angular'ning debounce qidiruvi
        # ba'zan fill'dagi bitta input eventiga reaksiya qilmaydi.
        search.press_sequentially(name, delay=40)
        page.wait_for_timeout(1500)  # qidiruv natijasi + Angular render
        try:
            # Qisqa timeout — yozuv hali indekslanmagan bo'lsa, default 30s
            # kutib retry'ni yutib yubormasin, tezroq qayta qidiraylik.
            page.get_by_text(name, exact=True).first.click(timeout=7000)
        except Exception as e:
            last_error = e
            try:
                rows = page.locator("smt-cell-content").all_inner_texts()
                log(f"search_and_open {name!r}: topilmadi. Ro'yxat ({len(rows)} ta): {rows[:8]}")
            except Exception:
                log(f"search_and_open {name!r}: topilmadi, ro'yxatni o'qib bo'lmadi")
            continue
        page.wait_for_timeout(1200)  # panel ochilish animatsiyasi
        try:
            action_btn.wait_for(state="visible", timeout=5000)
            log(f"search_and_open {name!r}: panel ochildi")
            return
        except Exception as e:
            last_error = e
            log(f"search_and_open {name!r}: panel ochilmadi, qayta urinamiz")
            continue  # click panel ochmadi — qayta urinamiz

    raise AssertionError(
        f"search_and_open {name!r}: 4 urinishda ham ro'yxatdan ochilmadi"
    ) from last_error





# ─── Testlar ──────────────────────────────────────────────────────────────────

def test_oprosniki_create_full(page: Page, code) -> None:
    """To'liq ma'lumotlar bilan oprosnik yaratish."""
    a = random.randint(1000, 9999)
    name = f"test_oprosniki{a}"

    _go_to_oprosniki(page)
    page.get_by_role("button", name="Создать").click()
    _wait_form_ready(page)
    page.locator("#null").fill(name)

    # Identificator tanlash — variant ro'yxati chiqquncha kutib, birinchisini bosamiz.
    # Option roli topilmasa eski (klaviatura) usulga qaytamiz.
    page.get_by_role("textbox", name="Выбрать").click()
    option = page.get_by_role("option").first
    try:
        option.wait_for(state="visible", timeout=3000)
        option.click()
        log("identificator: birinchi option bosildi")
    except Exception:
        log("identificator: option topilmadi, klaviatura bilan tanlaymiz")
        page.keyboard.press("ArrowDown")
        page.keyboard.press("Enter")

    # Qo'shimcha matn
    page.get_by_role("textbox", name="Enter text...").click()
    page.get_by_role("textbox", name="Enter text...").fill("test uchun yaratildi")

    _save_form(page)

    _search_and_open(page, name)
    expect(page.get_by_text(name).first).to_be_visible()



def test_oprosniki_create_mini(page: Page, code) -> None:
    """Minimal maydonlar bilan oprosnik yaratish."""
    a = random.randint(1000, 9999)
    name = f"test_oprosniki{a}"

    _create_oprosniki(page, name)
    _search_and_open(page, name)
    expect(page.get_by_text(name).first).to_be_visible()


def test_oprosniki_view(page: Page, code) -> None:
    """Oprosnikni ko'rish testi."""
    a = random.randint(1000, 9999)
    name = f"test_oprosniki{a}"

    _create_oprosniki(page, name)
    _search_and_open(page, name)

    # View tugmasi "Просмотр" yoki "Открыть" bo'lishi mumkin
    view_btn = page.locator("button").filter(
        has_text=re.compile(r"Просмотр|Открыть")
    ).first
    view_btn.wait_for(state="visible", timeout=10000)
    view_btn.click()
    page.wait_for_timeout(800)

    voprosy_btn = page.locator("button").filter(has_text="Вопросы").first
    voprosy_btn.wait_for(state="visible", timeout=10000)
    voprosy_btn.click()



def test_oprosniki_edit(page: Page, code) -> None:
    """Oprosnikni tahrirlash."""
    a = random.randint(1000, 9999)
    name = f"test_oprosniki{a}"
    edited_name = f"test_oprosniki{a}edit"

    _create_oprosniki(page, name)
    _search_and_open(page, name)

    edit_btn = page.get_by_role("button", name="Изменить", exact=True)
    edit_btn.wait_for(state="visible", timeout=5000)
    edit_btn.click()
    page.wait_for_load_state("networkidle")
    _wait_form_ready(page)
    page.locator("#null").clear()
    page.locator("#null").fill(edited_name)
    _save_form(page)

    _search_and_open(page, edited_name)
    expect(page.get_by_text(edited_name).first).to_be_visible()





def test_oprosniki_neaktive(page: Page, code) -> None:
    """Oprosnikni nofaol qilish."""
    a = random.randint(1000, 9999)
    name = f"test_oprosniki{a}"

    _create_oprosniki(page, name)
    _search_and_open(page, name)

    neaktiv_btn = page.get_by_role("button", name="Неактивный")
    neaktiv_btn.wait_for(state="visible", timeout=5000)
    neaktiv_btn.click()
    confirm = page.get_by_role("button", name="да", exact=True)
    confirm.wait_for(state="visible", timeout=5000)
    confirm.click()
    page.wait_for_load_state("networkidle")

    expect(page.get_by_text("Неактивный").first).to_be_visible(timeout=5000)



def test_oprosniki_neaktive2(page: Page, code) -> None:
    """Yaratishda nofaol status tanlash."""
    a = random.randint(1000, 9999)
    name = f"test_oprosniki{a}"

    _create_oprosniki(page, name, status="inactive")
    # Passiv oprosniki default listda ko'rinmaydi — "Показать все" filter kerak
    _go_to_oprosniki(page)
    page.locator(".gap-2.inline-flex").click()
    page.get_by_role("button", name="Показать все").click()
    page.wait_for_load_state("networkidle")
    page.get_by_role("searchbox", name="Поиск").fill(name)
    page.wait_for_load_state("networkidle")
    page.get_by_text(name).first.click()
    page.wait_for_timeout(800)
    expect(page.get_by_text(name).first).to_be_visible()



def test_oprosniki_copy(page: Page, code) -> None:
    """Duplicate nom bilan yaratishda xato chiqishi kerak."""
    a = random.randint(1000, 9999)
    name = f"test_oprosniki{a}"

    _create_oprosniki(page, name)

    _go_to_oprosniki(page)
    page.get_by_role("button", name="Создать").click()
    _wait_form_ready(page)
    page.locator("#null").fill(name)
    page.get_by_role("button", name="Сохранить").click()

    # Xato dialogi (cdk-overlay) ichidagi "Закрыть" — backdrop'ni e'tiborsiz qoldiramiz
    close_btn = page.locator(".cdk-overlay-container button").filter(has_text="Закрыть").first
    close_btn.wait_for(state="visible", timeout=5000)
    close_btn.click(force=True)



def test_oprosniki_trim(page: Page, code) -> None:
    """Bo'shliqli nom bilan yaratish."""
    a = random.randint(1000, 9999)
    name = f"test_oprosniki{a}"

    _go_to_oprosniki(page)
    page.get_by_role("button", name="Создать").click()
    _wait_form_ready(page)
    page.locator("#null").fill(f"   {name}   ")
    _save_form(page)

    _search_and_open(page, name)
    expect(page.get_by_text(name).first).to_be_visible()



def test_oprosniki_attache(page: Page, code) -> None:
    """Savolni oprosnikka biriktirish."""
    a = random.randint(1000, 9999)
    name = f"test_oprosniki{a}"

    _create_oprosniki(page, name)
    _search_and_open(page, name)

    attach_btn = page.get_by_role("button", name="Прикрепление вопросов")
    attach_btn.wait_for(state="visible", timeout=5000)
    attach_btn.click()
    page.wait_for_load_state("networkidle")
    page.locator("button").filter(has_text="Открепленные").first.click()
    page.wait_for_load_state("networkidle")
    page.get_by_role("checkbox").nth(3).click()
    page.wait_for_load_state("networkidle")
    prikr_btn = page.locator("button").filter(has_text=re.compile(r"Прикрепить\s+\d")).first
    prikr_btn.wait_for(state="visible", timeout=5000)
    prikr_btn.click()
    confirm = page.get_by_role("button", name="да", exact=True)
    confirm.wait_for(state="visible", timeout=5000)
    confirm.click()
    page.wait_for_load_state("networkidle")
    prikr_tab = page.locator("button").filter(has_text="Прикрепленные").first
    prikr_tab.click()
    expect(prikr_tab).to_be_visible()



def test_oprosniki_all_runner(page: Page, code) -> None:
    """Barcha testlarni bitta session da ketma-ket ishlatish.

    Har bir sub-test alohida log qilinadi; biri yiqilsa qolganlari baribir
    ishlaydi, oxirida yiqilganlar ro'yxati bilan umumiy xulosa chiqadi.
    """
    log("=== Опросники runner boshlandi: authorization ===")
    authorization(page)

    subtests = [
        test_oprosniki_create_full,
        test_oprosniki_create_mini,
        test_oprosniki_view,
        test_oprosniki_edit,
        test_oprosniki_neaktive,
        test_oprosniki_neaktive2,
        test_oprosniki_copy,
        test_oprosniki_trim,
        test_oprosniki_attache,
    ]

    failed: list[str] = []
    for subtest in subtests:
        log(f"--- {subtest.__name__} boshlandi ---")
        start = datetime.now()
        try:
            subtest(page, code)
            log(f"--- {subtest.__name__} OK ({(datetime.now() - start).seconds}s) ---")
        except Exception:
            failed.append(subtest.__name__)
            log(f"--- {subtest.__name__} FAILED ({(datetime.now() - start).seconds}s) ---")
            log(traceback.format_exc())

    log(f"=== Runner tugadi: {len(subtests) - len(failed)}/{len(subtests)} OK ===")
    assert not failed, f"Yiqilgan sub-testlar: {', '.join(failed)}"