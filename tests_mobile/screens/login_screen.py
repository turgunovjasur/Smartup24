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

from selenium.common.exceptions import StaleElementReferenceException, TimeoutException
from selenium.webdriver.support.ui import WebDriverWait

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
SUBMIT_READY_S = 10                        # yozilgandan keyin «Войти» clickable bo'lishini kutish


class LoginScreen(BaseScreen):

    # ── asosiy amallar ───────────────────────────────────────────────
    def login(self, username: str, password: str) -> None:
        """Toza holatdan login qiladi (kerak bo'lsa avval chiqadi). Natijani
        tekshirmaydi — test o'zi `is_logged_in()` / `on_login_form()` bilan tekshiradi."""
        self.ensure_logged_out()
        self.open_login_form()
        # RACE (2026-10-19, S-05.4.2): sekin emulyatorda EditText matni yozilgan, lekin
        # Flutter forma uni hali "sezmagan" — «Войти» enabled=true, ammo clickable=false
        # va tap jim no-op. Shuning uchun FAQAT bosishdan oldin tayyorlikni kutamiz;
        # bosishdan keyin qayta urinish YO'Q (noto'g'ri parolni ikki marta yubormaslik).
        self._fill_form(username, password)
        self.tap(SUBMIT)

    def ensure_logged_in_as(self, username: str, password: str) -> None:
        """Aynan shu user allaqachon kirgan bo'lsa hech narsa qilmaydi (~30-40s tejaydi);
        boshqa user yoki chiqilgan bo'lsa to'liq login(). Profile'da "Логин: <login>"
        (kompaniya kodisiz) aniq mos kelishi tekshiriladi."""
        login_name = username.split("@")[0]
        if self._form_or_tab() == 1:
            self.tap(PROFILE_TAB)
            # profile_state "in" = "Логин: ..." allaqachon chizilgan — yo'qlikni 3s kutib
            # tekshirish o'rniga joriy loginni o'qiymiz (user almashganda 3.4s tejaydi)
            if self.profile_state() == "in" and self._current_login() == login_name:
                return
        self.login(username, password)

    def logout(self) -> None:
        self.tap(PROFILE_TAB)
        self.scroll_down(3)                # "Выйти" Профиль eng pastida
        self.tap(LOGOUT)
        self.wait_for(LOGOUT_CANCEL)       # tasdiqlash dialogi
        self.tap_last(LOGOUT)              # dialogdagi "Выйти" (oxirgisi)
        self.wait_gone(LOGOUT_CANCEL)
        self.tap(PROFILE_TAB)
        # Logout hozirgina tasdiqlandi — "Вход"ning 5s barqarorligini kutish shart emas
        # (u faqat ilova qayta ochilib sessiya yuklanayotgan payt uchun), ~6.8s tejaydi.
        if self.profile_state(stable_s=0) != "out":
            raise AssertionError("Logoutdan keyin ilova login qilingan holatda qoldi")

    # ── yordamchilar ─────────────────────────────────────────────────
    def _fill_form(self, username: str, password: str) -> None:
        """Логин/Пароль yozadi va login qiymati mos hamda «Войти» clickable bo'lishini
        kutadi; bo'lmasa bir marta qayta yozadi. Ikkinchi marta ham tayyor bo'lmasa —
        aniq xato (jim bosib o'tib ketmaymiz)."""
        for _ in range(2):
            self.type(LOGIN_FIELD, username)
            self.type(PASSWORD_FIELD, password)
            self.hide_keyboard()           # klaviatura "Войти" ni yopib turadi
            if (self.wait_for(LOGIN_FIELD).get_attribute("text") == username
                    and self._submit_clickable(SUBMIT_READY_S)):
                return
        raise AssertionError(
            f"«Войти» bosiladigan holatga o'tmadi ({SUBMIT_READY_S}s x2): "
            "forma yozilgan login/parolni qabul qilmadi")

    def _submit_clickable(self, timeout: float) -> bool:
        """«Войти» semantikasi clickable=true bo'ldimi (EC.element_to_be_clickable
        faqat enabled'ni ko'radi, Flutter esa forma tayyor bo'lguncha clickable=false)."""
        def _ready(drv):
            els = drv.find_elements(*SUBMIT)
            return bool(els) and els[0].get_attribute("clickable") == "true"
        try:
            WebDriverWait(self.driver, timeout,
                          ignored_exceptions=(StaleElementReferenceException,)).until(_ready)
            return True
        except TimeoutException:
            return False

    def _form_or_tab(self) -> int:
        """0 — login formasi ochiq, 1 — pastki «Профиль» tab ko'rinadi. Forma modal
        (ochiq turganda tab YO'Q) — ikkalasi bir-birini istisno qiladi, shuning uchun
        "forma yo'qmi?"ni to'liq timeout kutib tekshirish o'rniga birinchi chiqqanini
        kutamiz (2026-10-20: yo'qlik tekshiruvlari user almashishda ~17s yeyardi)."""
        return self.wait_any(LOGIN_FIELD, PROFILE_TAB,
                             error="Na login formasi, na «Профиль» tab chiqdi")

    def _current_login(self) -> str | None:
        """Профиль'dagi "Логин: <login>" dan login (kompaniya kodisiz); topilmasa None."""
        for el in self.driver.find_elements(*USER_INFO):
            try:
                text = el.get_attribute("content-desc") or ""
            except StaleElementReferenceException:
                continue
            if text.startswith("Логин:"):
                return text.split(":", 1)[1].strip()
        return None

    def ensure_logged_out(self) -> None:
        """Boshlang'ich holat har xil bo'lishi mumkin: ochiq dialog, login forma,
        Профиль yoki boshqa tab — hammasidan login qilinmagan holatga o'tadi.
        Natija: yoki login formasi ochiq, yoki Профиль "Вход" holatida."""
        if self.wait_any(LOGOUT_CANCEL, LOGIN_FIELD, PROFILE_TAB,
                         error="Na dialog, na login formasi, na «Профиль» tab chiqdi") == 0:
            self.tap(LOGOUT_CANCEL)
        if self._form_or_tab() == 0:
            return
        self.tap(PROFILE_TAB)
        if self.profile_state() == "in":
            self.logout()

    def open_login_form(self) -> None:
        """Login qilinmagan holatdan formani ochadi. ensure_logged_out'dan keyin Профиль
        allaqachon "Вход" holatida — qayta tekshiruvlar (5s barqarorlik) takrorlanmaydi."""
        idx = self.wait_any(LOGIN_FIELD, LOGIN_ENTRY, PROFILE_TAB,
                            error="Na login formasi, na «Вход», na «Профиль» tab chiqdi")
        if idx == 0:
            return
        if idx == 2:                       # boshqa tabda turibmiz — Профиль'ga o'tib holatni aniqlaymiz
            self.tap(PROFILE_TAB)
            if self.profile_state() == "in":
                raise AssertionError("Login formasini ochib bo'lmaydi: ilova login qilingan holatda")
            if self.on_login_form(timeout=0.5):
                return                     # Профиль formani o'zi ochdi (mehmon)
        self.tap(LOGIN_ENTRY)
        self.wait_for(LOGIN_FIELD, error="Login formasi ochilmadi")

    # ── holat ────────────────────────────────────────────────────────
    def on_login_form(self, timeout: float = 5) -> bool:
        return self.exists(LOGIN_FIELD, timeout=timeout)

    def profile_state(self, timeout: float = 30, stable_s: float = LOGGED_OUT_STABLE_S) -> str:
        """Профиль ochilgandan keyin: "in" (login qilingan) yoki "out" ("Вход" yoki login forma).
        "Логин:" chiqsa darhol "in"; "Вход" esa ``stable_s`` turib qolsagina "out"
        (sessiya yuklanayotganda "Вход" vaqtincha ko'rinadi; logout'dan keyin stable_s=0)."""
        end = time.time() + timeout
        out_since = None
        blank_since = time.time()     # na "Логин:", na "Вход" — Профиль ochilmagan bo'lishi mumkin
        while time.time() < end:
            if self.exists(USER_INFO, timeout=0.5):
                return "in"
            if self.on_login_form(timeout=0.5):
                return "out"               # mehmon (toza o'rnatish): Профиль darhol login formasini ochadi
            if self.exists(LOGIN_ENTRY, timeout=0.5):
                blank_since = None
                out_since = out_since or time.time()
                if time.time() - out_since >= stable_s:
                    return "out"
            else:
                out_since = None
                blank_since = blank_since or time.time()
                # Ilova tabni 1-bosishda ochmasligi mumkin -> 8s bo'sh tursa qayta bosamiz
                if time.time() - blank_since >= 8 and self.exists(PROFILE_TAB, timeout=0.5):
                    self.tap(PROFILE_TAB)
                    blank_since = time.time()
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
