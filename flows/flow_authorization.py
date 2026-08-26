import os

from playwright.sync_api import Page, expect

# Muhitni TEST_ENV environment variable tanlaydi: "dev" (default) yoki "prod".
# Telegram bot (tg_bot_runner.py) "start prod" / "start dev" bilan aynan shu
# env'ni beradi — endi faylni qo'lda tahrirlash SHART EMAS. Berilmasa yoki
# noto'g'ri qiymatда DEV (sm24) ishlatiladi (avvalgi default xatti-harakat).
# URL va COMPANY_CODE DOIM birga keladi. Parol ikkala muhitda ham greenwhite.
# DIQQAT: production yangi UI /a2/... da (prefiks yo'q), dev /x24/a2/... da;
# app.smartup24.com/login.html — ESKI biruni UI, testlar u yerda ishlamaydi.
_ENVIRONMENTS = {
    # env kaliti: (LOGIN_URL, COMPANY_CODE)
    "prod": ("https://app.smartup24.com/a2/auth/login", "test"),
    "dev":  ("https://app3.greenwhite.uz/x24/a2/auth/login", "sm24"),
}

TEST_ENV = (os.getenv("TEST_ENV") or "dev").strip().lower()
if TEST_ENV not in _ENVIRONMENTS:
    TEST_ENV = "dev"
LOGIN_URL, COMPANY_CODE = _ENVIRONMENTS[TEST_ENV]


def authorization(page: Page, email=None, password="greenwhite") -> None:
    """Smartup24 ga login qiladi va ilova ochilishini kutadi.

    Login tugaganini **rolga/sahifaga bog'liq bo'lmagan** universal signal bilan
    tasdiqlaymiz: login sahifasidan chiqish (URL) + har login qilingan sahifada
    bo'ladigan header avatar (``app-user-dropdown``). "Модератор" kabi aniq navbar
    tugmasini kutmaymiz — u faqat ma'lum rol/bo'limlarda bo'ladi."""
    if email is None:
        email = f"admin@{COMPANY_CODE}"
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
