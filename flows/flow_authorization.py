from playwright.sync_api import Page, expect

LOGIN_URL = "https://app3.greenwhite.uz/x24/a2/auth/login"


def authorization(page: Page, email="admin@autotest", password="greenwhite") -> None:
    """Smartup24 ga login qiladi va ilova ochilishini kutadi.

    Login tugaganini **rolga/sahifaga bog'liq bo'lmagan** universal signal bilan
    tasdiqlaymiz: login sahifasidan chiqish (URL) + har login qilingan sahifada
    bo'ladigan header avatar (``app-user-dropdown``). "Модератор" kabi aniq navbar
    tugmasini kutmaymiz — u faqat ma'lum rol/bo'limlarda bo'ladi."""
    page.goto(LOGIN_URL)
    page.get_by_role("textbox", name="Логин").fill(email)
    page.get_by_role("textbox", name="Введите пароль").fill(password)
    page.get_by_role("button", name="Войти").click()
    page.wait_for_url(lambda url: "/auth/login" not in url, timeout=60_000)
    expect(page.locator("app-user-dropdown")).to_be_visible(timeout=60_000)


def logout(page: Page) -> None:
    """Avatar menyusidan "Выйти" bosib seansni yopadi (parallel seans limitini bo'shatadi).

    Teardown'da chaqiriladi — sahifa allaqachon yopilgan/xato holatda bo'lsa ham
    testni buzmasligi uchun himoya bilan o'raladi.
    """
    try:
        page.locator("app-user-dropdown button").first.click()
        page.get_by_text("Выйти", exact=True).first.click()
        page.wait_for_url("**/auth/login", timeout=15_000)
    except Exception:
        pass
