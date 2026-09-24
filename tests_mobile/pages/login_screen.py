"""LoginScreen — Smartup24 mobil ilova login oqimi (page object).

Oqim: Профиль tab -> "Вход" tugmasi -> login formasi (Логин/Пароль/Войти).
Login formasidagi maydonlarda id/desc yo'q, shuning uchun EditText tartibi
bilan olinadi: 1-EditText = Логин, 2-EditText = Пароль. Tugma = "Войти".
"""
from __future__ import annotations

from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from tests_mobile.pages.base_screen import BaseScreen

# Login formasi elementlari
_LOGIN_FIELD = (AppiumBy.XPATH, "(//android.widget.EditText)[1]")
_PASSWORD_FIELD = (AppiumBy.XPATH, "(//android.widget.EditText)[2]")
_SUBMIT = "Войти"           # content-desc (tugma)

# Ekran belgilari
_PROFILE_TAB = "Профиль"
_LOGIN_ENTRY = "Вход"       # Профиль ekranidagi "Вход" tugmasi (login qilinmagan holat)
_LOGGED_OUT_HINT = "Войдите в систему"   # login qilinmagan Профиль matni
_LOGOUT = "Выйти"           # Профиль pastidagi "Выйти" + tasdiqlash dialogidagi tugma
_LOGOUT_CANCEL = "Отмена"   # logout tasdiqlash dialogi belgisi


class LoginScreen(BaseScreen):

    def on_login_form(self, *, timeout: int = 5) -> bool:
        """Hozir login formasida turibmizmi (Логин maydoni ko'rinadimi)."""
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located(_LOGIN_FIELD)
            )
            return True
        except Exception:
            return False

    def open_login_form(self) -> None:
        """Login formasini ochadi. Boshlang'ich holatni o'zi aniqlaydi:
        - allaqachon formadamiz  -> hech nima qilmaydi,
        - Профиль'da 'Вход' bor  -> uni bosadi,
        - boshqa tabda           -> avval Профиль, keyin 'Вход'."""
        if self.on_login_form():
            return
        if not self.is_visible(_LOGIN_ENTRY, timeout=5):
            self.tap(_PROFILE_TAB)
        self.tap(_LOGIN_ENTRY)
        self.wait.until(EC.presence_of_element_located(_LOGIN_FIELD))

    def submit_login(self, username: str, password: str) -> None:
        """Логин/Пароль ni to'ldirib 'Войти' ni bosadi."""
        self.type_into(_LOGIN_FIELD, username)
        self.type_into(_PASSWORD_FIELD, password)
        # Klaviatura "Войти" tugmasini yopib turadi — yozgach uni yashiramiz
        try:
            self.driver.hide_keyboard()
        except Exception:
            pass
        self.tap(_SUBMIT)

    def login(self, username: str, password: str) -> None:
        self.open_login_form()
        self.submit_login(username, password)

    # ── logout ───────────────────────────────────────────────────────
    def logout(self) -> None:
        """Профиль -> pastga scroll -> 'Выйти' -> tasdiqlash dialogida 'Выйти'."""
        self.tap(_PROFILE_TAB)
        self.scroll_down()
        self.tap(_LOGOUT)                 # menyudagi "Выйти" (dialog ochilishidan oldin yagona)
        self.wait_visible(_LOGOUT_CANCEL)  # tasdiqlash dialogi chiqdi
        self.tap_last(_LOGOUT)             # dialogdagi tasdiq "Выйти" (oxirgisi)
        self.wait_gone(_LOGOUT_CANCEL)     # dialog yopilib logout amalga oshguncha
        self.tap(_PROFILE_TAB)             # Профиль'ga qaytamiz
        self.wait_visible(_LOGIN_ENTRY)    # login qilinmagan holat tasdig'i ('Вход')

    def ensure_logged_out(self) -> None:
        """Test boshida TOZA holat: login qilingan bo'lsa chiqadi."""
        # Ochiq qolgan logout tasdiqlash dialogi bo'lsa yopamiz
        if self.is_visible(_LOGOUT_CANCEL, timeout=2):
            self.tap(_LOGOUT_CANCEL)
        # Allaqachon login formasida bo'lsak — demak login qilinmagan (Профиль tab yo'q)
        if self.on_login_form():
            return
        self.tap(_PROFILE_TAB)
        if self.is_visible(_LOGIN_ENTRY, timeout=5):
            return                        # allaqachon chiqilgan
        self.logout()

    # ── holat tekshiruvlari ──────────────────────────────────────────
    def is_logged_out(self) -> bool:
        """Профиль ekranida 'Войдите в систему' / 'Вход' ko'rinsa — login qilinmagan."""
        return self.is_visible(_LOGGED_OUT_HINT) or self.is_visible(_LOGIN_ENTRY)

    def is_logged_in(self) -> bool:
        """Login muvaffaqiyatli bo'lsa Профиль ekranida 'Вход' YO'Q bo'ladi."""
        return not self.is_visible(_LOGIN_ENTRY, timeout=8)
