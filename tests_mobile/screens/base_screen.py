"""BaseScreen — barcha ekranlar uchun umumiy amallar (web BasePage ekvivalenti).

Flutter ilovada resource-id YO'Q: ko'rinadigan matn `content-desc` ga yoziladi.
Locator — oddiy (by, value) tuple, quyidagi yasovchilar bilan quriladi:

    desc("Войти")                  aniq content-desc
    contains("Тип оплаты")         content-desc ichida matn bor ("Тип оплаты*\\nНе выбран")
    xpath("(//...)[last()]")       qolgan hamma holat (nomga bog'lash, tartib)

Hamma kutish explicit (WebDriverWait); implicit wait ishlatilmaydi.
"""
from __future__ import annotations

from appium.webdriver.common.appiumby import AppiumBy
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

Locator = tuple[str, str]


def desc(text: str) -> Locator:
    return (AppiumBy.ACCESSIBILITY_ID, text)


def contains(text: str) -> Locator:
    return (AppiumBy.XPATH, f"//*[contains(@content-desc, '{text}')]")


def xpath(expr: str) -> Locator:
    return (AppiumBy.XPATH, expr)


class BaseScreen:
    TIMEOUT = 15   # sekund

    def __init__(self, driver):
        self.driver = driver

    # ── kutish / tekshirish ──────────────────────────────────────────
    def exists(self, loc: Locator, timeout: float = 3) -> bool:
        """Element `timeout` ichida paydo bo'ladimi (xato bermaydi)."""
        try:
            WebDriverWait(self.driver, timeout).until(EC.presence_of_element_located(loc))
            return True
        except TimeoutException:
            return False

    def wait_for(self, loc: Locator, timeout: float = TIMEOUT, error: str | None = None):
        """Element paydo bo'lguncha kutadi; chiqmasa tushunarli AssertionError."""
        try:
            return WebDriverWait(self.driver, timeout).until(EC.presence_of_element_located(loc))
        except TimeoutException:
            raise AssertionError(error or f"Element chiqmadi ({timeout}s): {loc[1]}") from None

    def wait_gone(self, loc: Locator, timeout: float = 10, error: str | None = None) -> None:
        """Element yo'qolguncha kutadi (dialog yopildi va h.k.)."""
        try:
            WebDriverWait(self.driver, timeout).until(EC.invisibility_of_element_located(loc))
        except TimeoutException:
            raise AssertionError(error or f"Element yo'qolmadi ({timeout}s): {loc[1]}") from None

    # ── amallar ──────────────────────────────────────────────────────
    def tap(self, loc: Locator, timeout: float = TIMEOUT) -> None:
        try:
            WebDriverWait(self.driver, timeout).until(EC.element_to_be_clickable(loc)).click()
        except TimeoutException:
            raise AssertionError(f"Bosib bo'lmadi ({timeout}s): {loc[1]}") from None

    def tap_last(self, loc: Locator) -> None:
        """Bir nechta mos element bo'lsa OXIRGISINI bosadi (dialog tugmasi odatda oxirgi)."""
        els = self.driver.find_elements(*loc)
        assert els, f"Element topilmadi: {loc[1]}"
        els[-1].click()

    def type(self, loc: Locator, text: str) -> None:
        """Maydonni TOZALAB yozadi (no_reset tufayli eski matn qolgan bo'lishi mumkin)."""
        el = self.wait_for(loc)
        el.click()
        el.clear()
        el.send_keys(text)

    def open_overlay(self, trigger: Locator, marker: Locator, taps: int = 2, wait_s: float = 12) -> bool:
        """Dialog/kalendar ochadi. Ilova 1-bosishda ochmasligi mumkin, lekin tez
        qayta bosish ochilgan dialogni YOPADI — shuning uchun har bosishdan keyin
        `marker` ni `wait_s` kutamiz, chiqmasagina qayta bosamiz."""
        for _ in range(taps):
            self.tap(trigger)
            if self.exists(marker, timeout=wait_s):
                return True
        return False

    def scroll_down(self, times: int = 1) -> None:
        size = self.driver.get_window_size()
        w, h = size["width"], size["height"]
        for _ in range(times):
            self.driver.swipe(w // 2, int(h * 0.8), w // 2, int(h * 0.3), 500)

    def hide_keyboard(self) -> None:
        try:
            self.driver.hide_keyboard()
        except Exception:
            pass   # klaviatura ochiq bo'lmasa xato beradi — muhim emas

