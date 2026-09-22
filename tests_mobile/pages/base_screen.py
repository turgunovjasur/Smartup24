"""BaseScreen — barcha mobil ekran-obyektlari uchun umumiy amallar.

Web `utils/base_page.py` (BasePage) ekvivalenti, lekin Appium/Android uchun.
FALSAFA bir xil: barqaror locator (bu Flutter ilovada — accessibility
`content-desc`) + ANIQ kutish (WebDriverWait), xom sleep/koordinata emas.

Flutter ilova ko'rinadigan matnni `content-desc` sifatida beradi -> element
ACCESSIBILITY_ID (content-desc) orqali topiladi. Matnsiz maydonlar (masalan
input) `android.widget.EditText` klassi bo'yicha olinadi.
"""
from __future__ import annotations

from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


class BaseScreen:
    DEFAULT_TIMEOUT = 15   # sekund

    def __init__(self, driver):
        self.driver = driver
        self.wait = WebDriverWait(driver, self.DEFAULT_TIMEOUT)

    # ── topish / kutish ──────────────────────────────────────────────
    def _desc(self, desc: str):
        return (AppiumBy.ACCESSIBILITY_ID, desc)

    def wait_visible(self, desc: str, *, timeout: int | None = None):
        """content-desc bo'yicha element ko'ringuncha kutadi va qaytaradi."""
        w = WebDriverWait(self.driver, timeout) if timeout else self.wait
        return w.until(EC.presence_of_element_located(self._desc(desc)))

    def is_visible(self, desc: str, *, timeout: int = 5) -> bool:
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located(self._desc(desc))
            )
            return True
        except Exception:
            return False

    # ── amallar ──────────────────────────────────────────────────────
    def tap(self, desc: str, *, timeout: int | None = None) -> None:
        """content-desc bo'yicha elementni bosadi (bosiladigan bo'lguncha kutib)."""
        w = WebDriverWait(self.driver, timeout) if timeout else self.wait
        w.until(EC.element_to_be_clickable(self._desc(desc))).click()

    def tap_last(self, desc: str) -> None:
        """content-desc bir nechta elementga to'g'ri kelsa OXIRGISINI bosadi
        (masalan tasdiqlash dialogida ekran ortidagi + dialogdagi 'Выйти')."""
        els = self.driver.find_elements(*self._desc(desc))
        assert els, f"'{desc}' elementi topilmadi"
        els[-1].click()

    def type_into(self, locator: tuple[str, str], text: str) -> None:
        """Berilgan locator (masalan EditText) maydonini TOZALAB matn yozadi.
        clear() shart — no_reset bilan maydon oldingi rundan matn saqlab qolishi
        mumkin, tozalamasa send_keys ustiga QO'SHADI (login buziladi)."""
        el = self.wait.until(EC.presence_of_element_located(locator))
        el.click()
        el.clear()
        el.send_keys(text)

    def scroll_down(self, times: int = 3) -> None:
        """Ekranni pastga suradi (yashirin pastki elementlarni ko'rsatish uchun)."""
        size = self.driver.get_window_size()
        w, h = size["width"], size["height"]
        for _ in range(times):
            self.driver.swipe(w // 2, int(h * 0.8), w // 2, int(h * 0.3), 500)

    def screenshot(self, path: str) -> None:
        self.driver.get_screenshot_as_file(path)
