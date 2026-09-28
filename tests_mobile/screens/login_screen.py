"""LoginScreen — login / logout.

Oqim: Профиль -> "Вход" -> forma (Логин, Пароль, Войти). Forma inputlarida
id ham matn ham yo'q -> EditText tartibi: 1-chi Логин, 2-chi Пароль.
Login formasi to'liq modal: ochiq turganda pastki "Профиль" tab ko'rinmaydi.

DIQQAT: ilova qayta ochilganda saqlangan sessiya yuklanguncha (sekin internetda
bir necha soniya) Профиль "login qilinmagan" ko'rinishda chiziladi — "Вход"
VAQTINCHA paydo bo'ladi. Shuning uchun holat "Вход" bilan emas, ishonchli belgi
("Логин: ..." = login qilingan) va barqarorlik bilan aniqlanadi: profile_state().
"""
from __future__ import annotations

import time

from tests_mobile.screens.base_screen import BaseScreen, contains, desc, xpath

LOGIN_FIELD = xpath("(//android.widget.EditText)[1]")
PASSWORD_FIELD = xpath("(//android.widget.EditText)[2]")
SUBMIT = desc("Войти")

PROFILE_TAB = desc("Профиль")
LOGIN_ENTRY = desc("Вход")                 # faqat login QILINMAGAN holatda bor
LOGOUT = desc("Выйти")                     # menyuda ham, tasdiqlash dialogida ham
LOGOUT_CANCEL = desc("Отмена")             # tasdiqlash dialogi belgisi
USER_INFO = contains("Логин:")             # Профиль: "Логин: sanobar" — faqat login QILINGANDA
LOGGED_OUT_STABLE_S = 5                    # "Вход" shuncha turib qolsa — haqiqatan chiqilgan


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
        if self.profile_state() != "out":
            raise AssertionError("Logoutdan keyin ilova login qilingan holatda qoldi")

    # ── yordamchilar ─────────────────────────────────────────────────
    def ensure_logged_out(self) -> None:
        """Boshlang'ich holat har xil bo'lishi mumkin: ochiq dialog, login forma,
        Профиль yoki boshqa tab — hammasidan login qilinmagan holatga o'tadi."""
        if self.exists(LOGOUT_CANCEL, timeout=2):
            self.tap(LOGOUT_CANCEL)
        if self.on_login_form():
            return
        self.tap(PROFILE_TAB)
        if self.profile_state() == "in":
            self.logout()

    def open_login_form(self) -> None:
        if self.on_login_form():
            return
        self.tap(PROFILE_TAB)
        if self.profile_state() == "in":
            raise AssertionError("Login formasini ochib bo'lmaydi: ilova login qilingan holatda")
        self.tap(LOGIN_ENTRY)
        self.wait_for(LOGIN_FIELD, error="Login formasi ochilmadi")

    # ── holat ────────────────────────────────────────────────────────
    def on_login_form(self, timeout: float = 5) -> bool:
        return self.exists(LOGIN_FIELD, timeout=timeout)

    def profile_state(self, timeout: float = 30) -> str:
        """Профиль ochiq turganda: "in" (login qilingan) yoki "out".
        "Логин:" chiqsa darhol "in"; "Вход" esa LOGGED_OUT_STABLE_S turib qolsagina "out"
        (sessiya yuklanayotganda "Вход" vaqtincha ko'rinadi)."""
        end = time.time() + timeout
        out_since = None
        while time.time() < end:
            if self.exists(USER_INFO, timeout=0.5):
                return "in"
            if self.exists(LOGIN_ENTRY, timeout=0.5):
                out_since = out_since or time.time()
                if time.time() - out_since >= LOGGED_OUT_STABLE_S:
                    return "out"
            else:
                out_since = None
        raise AssertionError(f"Профиль holati {timeout}s ichida aniqlanmadi (na 'Логин:', na 'Вход')")

    def is_logged_in(self, timeout: float = 20) -> bool:
        """Login'dan keyin: "Логин:" (Профиль) chiqsa True. Forma yopilgan bo'lsa
        Профиль tabiga o'tib qaraydi; forma yopilmasa (xato parol) — False."""
        end = time.time() + timeout
        while time.time() < end:
            if self.exists(USER_INFO, timeout=1):
                return True
            if not self.on_login_form(timeout=0.5) and self.exists(PROFILE_TAB, timeout=0.5):
                self.tap(PROFILE_TAB)
        return False

    def is_logged_out(self) -> bool:
        self.tap(PROFILE_TAB)
        return self.profile_state() == "out"
