from playwright.sync_api import Page


LOGIN_URL = "https://app3.greenwhite.uz/x24/a2/auth/login"


def _do_login(page: Page, email: str, password: str) -> None:
    """Bitta login urinishi. Muvaffaqiyatsiz bo'lsa xato chiqaradi."""
    page.goto(LOGIN_URL, wait_until="domcontentloaded", timeout=60000)
    try:
        page.evaluate("() => { try { localStorage.clear(); sessionStorage.clear(); } catch (e) {} }")
    except Exception:
        pass
    page.context.clear_cookies()
    page.goto(LOGIN_URL, wait_until="domcontentloaded", timeout=60000)

    login_field = page.get_by_role("textbox", name="Логин")
    login_field.wait_for(state="visible", timeout=20000)
    # `fill()` o'zi fokuslaydi — alohida `click()` (ba'zan sekin sahifada osilib
    # qoladi) shart emas.
    login_field.fill(email, timeout=15000)
    page.get_by_role("textbox", name="Введите пароль").fill(password, timeout=15000)
    submit = page.get_by_role("button", name="Войти")
    try:
        submit.click(timeout=8000)
    except Exception:
        page.get_by_role("textbox", name="Введите пароль").press("Enter")

    page.wait_for_url(lambda url: "login" not in url, timeout=30000, wait_until="commit")
    try:
        page.wait_for_load_state("load", timeout=30000)
    except Exception:
        pass


def authorization(page: Page, email="admin@sm24", password="greenwhite") -> None:
    """Tizimga kiradi. Login sahifasi/server vaqtincha sekin bo'lsa, qayta uradi."""
    last_err = None
    for _ in range(3):
        try:
            _do_login(page, email, password)
            return
        except Exception as e:
            last_err = e
            page.wait_for_timeout(1500)
    raise last_err


