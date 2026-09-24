"""LoginScreen — login / logout.

Oqim: Профиль -> "Вход" -> forma (Логин, Пароль, Войти). Forma inputlarida
id ham matn ham yo'q -> EditText tartibi: 1-chi Логин, 2-chi Пароль.
Login formasi to'liq modal: ochiq turganda pastki "Профиль" tab ko'rinmaydi.
"""
from __future__ import annotations

from tests_mobile.screens.base_screen import BaseScreen, desc, xpath

LOGIN_FIELD = xpath("(//android.widget.EditText)[1]")
PASSWORD_FIELD = xpath("(//android.widget.EditText)[2]")
SUBMIT = desc("Войти")

PROFILE_TAB = desc("Профиль")
LOGIN_ENTRY = desc("Вход")                 # faqat login QILINMAGAN holatda bor
LOGGED_OUT_HINT = desc("Войдите в систему")
LOGOUT = desc("Выйти")                     # menyuda ham, tasdiqlash dialogida ham
LOGOUT_CANCEL = desc("Отмена")             # tasdiqlash dialogi belgisi


class LoginScreen(BaseScreen):

    # ── asosiy amallar ───────────────────────────────────────────────
    def login(self, username: str, password: str) -> None:
        """Toza holatdan login qiladi (kerak bo'lsa avval chiqadi). Natijani
        tekshirmaydi — test o'zi `is_logged_in()` / `on_login_form()` bilan tekshiradi."""
        self.ensure_logged_out()
        self.open_login_form()
        self.type(LOGIN_FIELD, username)
        self.type(PASSWORD_FIELD, password)
        self.hide_keyboard()               # klaviatura "Войти" ni yopib turadi
        self.tap(SUBMIT)

    def logout(self) -> None:
        self.tap(PROFILE_TAB)
        self.scroll_down(3)                # "Выйти" Профиль eng pastida
        self.tap(LOGOUT)
        self.wait_for(LOGOUT_CANCEL)       # tasdiqlash dialogi
        self.tap_last(LOGOUT)              # dialogdagi "Выйти" (oxirgisi)
        self.wait_gone(LOGOUT_CANCEL)
        self.tap(PROFILE_TAB)
        self.wait_for(LOGIN_ENTRY, error="Logoutdan keyin 'Вход' chiqmadi")

    # ── yordamchilar ─────────────────────────────────────────────────
    def ensure_logged_out(self) -> None:
        """Boshlang'ich holat har xil bo'lishi mumkin: ochiq dialog, login forma,
        Профиль yoki boshqa tab — hammasidan login qilinmagan holatga o'tadi."""
        if self.exists(LOGOUT_CANCEL, timeout=2):
            self.tap(LOGOUT_CANCEL)
        if self.on_login_form():
            return
        self.tap(PROFILE_TAB)
        if not self.exists(LOGIN_ENTRY, timeout=5):
            self.logout()

    def open_login_form(self) -> None:
        if self.on_login_form():
            return
        if not self.exists(LOGIN_ENTRY, timeout=5):
            self.tap(PROFILE_TAB)
        self.tap(LOGIN_ENTRY)
        self.wait_for(LOGIN_FIELD, error="Login formasi ochilmadi")

    # ── holat ────────────────────────────────────────────────────────
    def on_login_form(self, timeout: float = 5) -> bool:
        return self.exists(LOGIN_FIELD, timeout=timeout)

    def is_logged_in(self) -> bool:
        return not self.exists(LOGIN_ENTRY, timeout=8)

    def is_logged_out(self) -> bool:
        return self.exists(LOGGED_OUT_HINT, timeout=5) or self.exists(LOGIN_ENTRY, timeout=5)
