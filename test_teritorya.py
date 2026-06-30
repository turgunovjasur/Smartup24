import re
import random
from playwright.sync_api import Page, expect
from flow_authorization import authorization

TERRITORY_URL = "https://app3.greenwhite.uz/x24/a2/sb/sbr/moderator/territory_list"


# ─── Helper funksiyalar ───────────────────────────────────────────────────────

def _navigate_to_territory(page: Page) -> None:
    page.goto(TERRITORY_URL)
    page.wait_for_load_state("networkidle")


def _fill_search(page: Page, name: str):
    """Qidiruvni yuboradi va natija ro'yxatda paydo bo'lmaguncha qayta urinadi.

    Server qidiruv natijasini kech qaytarishi yoki re-render qidiruv maydonini
    tozalashi mumkin — shuning uchun natija ko'rinmasa, qidiruv qayta yuboriladi.
    Topilgan elementning locatorini qaytaradi.
    """
    searchbox = page.get_by_role("searchbox", name="Поиск")
    target = page.get_by_text(name, exact=True).first

    for _ in range(4):
        searchbox.click()
        searchbox.fill("")
        searchbox.fill(name)
        try:
            target.wait_for(state="attached", timeout=5000)
            page.wait_for_timeout(300)  # natija ro'yxati barqarorlashishi uchun
            return target
        except Exception:
            page.wait_for_timeout(1000)

    # oxirgi urinish — muvaffaqiyatsiz bo'lsa xato chiqaradi
    target.wait_for(state="attached", timeout=5000)
    return target


def _type_name(page: Page, value: str) -> None:
    """Nom maydonini haqiqiy klaviatura bosilishlari bilan to'ldiradi.

    `fill()` qiymatni o'rnatadi-yu, lekin Angular forma modeliga nomni har doim
    ham registratsiya qilavermaydi — natijada saqlash bo'sh forma deb bloklanadi.
    `press_sequentially` + Tab (blur) bilan bog'lanish ishonchli bo'ladi.
    """
    tb = page.get_by_role("textbox").first
    tb.wait_for(state="visible", timeout=15000)
    tb.click()
    tb.fill("")
    tb.press_sequentially(value, delay=30)
    tb.press("Tab")


def _save_territory_form(page: Page) -> None:
    """'Сохранить' ni bosadi va saqlash so'rovi ketib, ro'yxatga qaytguncha kutadi.

    Forma xaritasi (Leaflet) va ma'lumotlari asinxron yuklanadi; forma to'liq
    tayyor bo'lmasdan Сохранить bosilsa, bosish behuda ketadi — saqlash so'rovi
    ($save) umuman yuborilmaydi va yozuv yaratilmaydi. Shuning uchun avval xarita
    ko'rinishini kutamiz, so'ng saqlash so'rovi haqiqatan ketguncha qayta urinamiz.
    """
    # forma to'liq tayyor bo'lishi uchun xarita ko'rinishini kutamiz
    try:
        page.locator(".leaflet-container").first.wait_for(state="visible", timeout=15000)
    except Exception:
        pass
    page.wait_for_timeout(700)

    for _ in range(4):
        if "territory_list" in page.url:
            page.wait_for_load_state("networkidle")
            return
        try:
            with page.expect_response(
                lambda r: r.request.method == "POST"
                and "$save" in r.url
                and "territor" in r.url.lower(),
                timeout=6000,
            ):
                page.get_by_role("button", name="Сохранить").first.click()
            # saqlash so'rovi ketdi — ro'yxatga qaytishini kutamiz
            for _ in range(20):
                if "territory_list" in page.url:
                    page.wait_for_load_state("networkidle")
                    return
                page.wait_for_timeout(500)
            return
        except Exception:
            # so'rov ketmadi — forma hali tayyor emas, biroz kutib qayta urinamiz
            page.wait_for_timeout(800)

    raise AssertionError(
        f"Territoriya saqlanmadi — saqlash so'rovi yuborilmadi (joriy url={page.url})"
    )


def _create_territory(page: Page, name: str, inactive: bool = False) -> None:
    """Territoriya yaratadi va ro'yxat sahifasiga qaytguncha kutadi."""
    page.get_by_role("button", name="Создать", exact=True).click()
    _type_name(page, name)
    if inactive:
        page.get_by_role("switch").click()
    _save_territory_form(page)


def _search_and_open(page: Page, name: str) -> None:
    """Ro'yxatda qidirib, kartani ochadi (panel ochilguncha qayta urinish)."""
    action_btn = page.locator("button").filter(
        has_text=re.compile(r"Изменить|Удалить|Неактивный|Активный")
    ).first

    for _ in range(3):
        _navigate_to_territory(page)
        try:
            target = _fill_search(page, name)
            target.click()
            action_btn.wait_for(state="visible", timeout=5000)
            page.wait_for_timeout(800)  # panel re-render barqarorlashishi uchun
            return
        except Exception:
            continue

    # oxirgi urinish — muvaffaqiyatsiz bo'lsa xato chiqaradi
    _navigate_to_territory(page)
    _fill_search(page, name).click(timeout=8000)
    action_btn.wait_for(state="visible", timeout=5000)


def _search_and_open_inactive(page: Page, name: str) -> None:
    """Passiv territoriyani 'Показать все' filter bilan qidirib ochadi."""
    action_btn = page.locator("button").filter(
        has_text=re.compile(r"Изменить|Удалить|Неактивный|Активный")
    ).first

    for _ in range(3):
        _navigate_to_territory(page)
        page.locator(".gap-2.inline-flex").click()
        page.get_by_role("button", name="Показать все").click()
        page.wait_for_load_state("networkidle")
        try:
            target = _fill_search(page, name)
            target.click()
            action_btn.wait_for(state="visible", timeout=5000)
            page.wait_for_timeout(800)  # panel re-render barqarorlashishi uchun
            return
        except Exception:
            continue

    action_btn.wait_for(state="visible", timeout=5000)


# ─── Testlar ──────────────────────────────────────────────────────────────────

def test_territory_create(page: Page) -> None:
    """Yangi territoriya yaratish."""
    a = random.randint(1000, 9999)
    name = f"kavardan{a}"
    authorization(page)
    _navigate_to_territory(page)
    _create_territory(page, name)

    # Ko'p yozuv bo'lsa yangi territory 1-sahifada bo'lmasligi mumkin — qidirib topamiz
    target = _fill_search(page, name)
    target.click()
    expect(page.get_by_text(name, exact=True).first).to_be_visible()


def test_territory_inactive(page: Page) -> None:
    """Aktiv territoriyani nofaol qilish."""
    a = random.randint(1000, 9999)
    name = f"kavardan{a}"
    authorization(page)
    _navigate_to_territory(page)
    _create_territory(page, name)

    _search_and_open(page, name)

    page.get_by_role("button", name=re.compile(r"Неактивный")).click()
    confirm = page.get_by_role("button", name="да", exact=True)
    confirm.wait_for(state="visible", timeout=5000)
    confirm.click()
    page.wait_for_load_state("networkidle")


def test_territory_inactive_create(page: Page) -> None:
    """Nofaol holda yaratib, aktiv qilish."""
    a = random.randint(1000, 9999)
    name = f"kavardan{a}"
    authorization(page)
    _navigate_to_territory(page)
    _create_territory(page, name, inactive=True)

    # Passiv territoriya default listda ko'rinmaydi
    _search_and_open_inactive(page, name)

    page.get_by_role("button", name=re.compile(r"^Активный")).click()
    confirm = page.get_by_role("button", name="да", exact=True)
    confirm.wait_for(state="visible", timeout=5000)
    confirm.click()
    page.wait_for_load_state("networkidle")

    expect(page.get_by_text("Активный").first).to_be_visible(timeout=5000)


def test_territory_edit(page: Page) -> None:
    """Territoriyani tahrirlash."""
    a = random.randint(1000, 9999)
    name = f"kavardan{a}"
    edited_name = f"kavardan{a}edit"
    authorization(page)
    _navigate_to_territory(page)
    _create_territory(page, name)

    _search_and_open(page, name)

    page.get_by_role("button", name="Изменить", exact=True).click()
    _type_name(page, edited_name)
    _save_territory_form(page)

    # Tahrirlangan nom ro'yxatda paydo bo'lishini qidirib tasdiqlaymiz —
    # saqlashdan keyin ro'yxat eski qidiruv bilan filtrlangan bo'lishi mumkin.
    _navigate_to_territory(page)
    expect(_fill_search(page, edited_name)).to_be_visible()


def test_territory_delete(page: Page) -> None:
    """Territoriyani o'chirish va yo'qligi tasdiqlash."""
    a = random.randint(1000, 9999)
    name = f"kavardan{a}"
    authorization(page)
    _navigate_to_territory(page)
    _create_territory(page, name)

    _search_and_open(page, name)

    page.get_by_role("button", name="Удалить", exact=True).click()
    confirm = page.get_by_role("button", name="да", exact=True)
    confirm.wait_for(state="visible", timeout=5000)
    confirm.click()
    page.wait_for_load_state("networkidle")

    # O'chirilgandan keyin qidiruvda topilmasligini tasdiqlaymiz
    searchbox = page.get_by_role("searchbox", name="Поиск")
    searchbox.click()
    searchbox.fill(name)
    expect(page.get_by_text(name, exact=True)).to_have_count(0)


def test_territory_all(page: Page, code) -> None:
    authorization(page)
    test_territory_create(page)
    test_territory_inactive(page)
    test_territory_inactive_create(page)
    test_territory_edit(page)
    test_territory_delete(page)
