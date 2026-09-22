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


class LoginScreen(BaseScreen):

    def _on_login_form(self) -> bool:
        """Hozir login formasida turibmizmi (Логин maydoni ko'rinadimi)."""
        try:
            WebDriverWait(self.driver, 2).until(
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
        if self._on_login_form():
            return
        if not self.is_visible(_LOGIN_ENTRY, timeout=3):
            self.tap(_PROFILE_TAB)
        self.tap(_LOGIN_ENTRY)
        self.wait.until(EC.presence_of_element_located(_LOGIN_FIELD))

    def submit_login(self, username: str, password: str) -> None:
        """Логин/Пароль ni to'ldirib 'Войти' ni bosadi."""
        self.type_into(_LOGIN_FIELD, username)
        self.type_into(_PASSWORD_FIELD, password)
        self.tap(_SUBMIT)

    def login(self, username: str, password: str) -> None:
        self.open_login_form()
        self.submit_login(username, password)

    # ── holat tekshiruvlari ──────────────────────────────────────────
    def is_logged_out(self) -> bool:
        """Профиль ekranida 'Войдите в систему' / 'Вход' ko'rinsa — login qilinmagan."""
        return self.is_visible(_LOGGED_OUT_HINT) or self.is_visible(_LOGIN_ENTRY)

    def is_logged_in(self) -> bool:
        """Login muvaffaqiyatli bo'lsa Профиль ekranida 'Вход' YO'Q bo'ladi."""
        return not self.is_visible(_LOGIN_ENTRY, timeout=8)
