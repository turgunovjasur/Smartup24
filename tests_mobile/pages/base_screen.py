"""BaseScreen — barcha mobil ekran-obyektlari uchun umumiy amallar.

Web `utils/base_page.py` (BasePage) ekvivalenti, lekin Appium/Android uchun.
FALSAFA bir xil: barqaror locator (bu Flutter ilovada — accessibility
`content-desc`) + ANIQ kutish (WebDriverWait), xom sleep/koordinata emas.

Flutter ilova ko'rinadigan matnni `content-desc` sifatida beradi -> element
ACCESSIBILITY_ID (content-desc) orqali topiladi. Matnsiz maydonlar (masalan
input) `android.widget.EditText` klassi bo'yicha olinadi.
"""
from __future__ import annotations

import time

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

    # ── XPath / contains yordamchilari ───────────────────────────────
    # Flutter content-desc ko'pincha bir nechta matnni qo'shib beradi
    # ("Тип оплаты*\nНе выбран") va bir xil desc'li elementlar ko'p bo'ladi —
    # shunday joylarda ACCESSIBILITY_ID (aniq moslik) yetmaydi.
    def _tap_xpath(self, xpath: str, *, timeout: int | None = None) -> None:
        w = WebDriverWait(self.driver, timeout) if timeout else self.wait
        w.until(EC.element_to_be_clickable((AppiumBy.XPATH, xpath))).click()

    def _exists_xpath(self, xpath: str, *, timeout: int = 3) -> bool:
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((AppiumBy.XPATH, xpath))
            )
            return True
        except Exception:
            return False

    def _tap_contains(self, needle: str, *, timeout: int | None = None) -> None:
        self._tap_xpath(f"//*[contains(@content-desc, '{needle}')]", timeout=timeout)

    def _exists_contains(self, needle: str, *, timeout: int = 3) -> bool:
        return self._exists_xpath(f"//*[contains(@content-desc, '{needle}')]", timeout=timeout)

    def _wait_marker(self, needle: str, *, timeout: int = 20) -> None:
        """Berilgan matn (content-desc contains) EKRANDA ko'ringunча kutadi —
        navigatsiya tugaganини tasdiqlaydi (ilova sekin bo'lgani uchun). Chiqмаса
        ANIQ xato beradi."""
        if not self._exists_contains(needle, timeout=timeout):
            raise AssertionError(f"Kutilgan belgi ko'rinmadi (navigatsiya tugamadi?): {needle!r}")

    def _open_overlay(self, field_needle: str, marker_desc: str,
                      *, taps: int = 2, poll_s: int = 12) -> bool:
        """Maydonни bosib overlay (dialog/kalendar) ochadi. Ilova quirk: 1-bosishда
        ochilmasligi mumkin. LEKIN tez qayta bosиш ochilган dialogни YOPADI — shuning
        uchun bir bosгач ``marker_desc`` chiqишини ``poll_s`` sekund KUTAMIZ, faqat
        rostan chiqмаса qayta bosamiz (``taps`` marta)."""
        xp = f"//*[@content-desc='{marker_desc}']"
        for _ in range(taps):
            self._tap_contains(field_needle)
            end = time.time() + poll_s
            while time.time() < end:
                if self._exists_xpath(xp, timeout=1):
                    return True
        return False

    def scroll_down(self, times: int = 3) -> None:
        """Ekranni pastga suradi (yashirin pastki elementlarni ko'rsatish uchun)."""
        size = self.driver.get_window_size()
        w, h = size["width"], size["height"]
        for _ in range(times):
            self.driver.swipe(w // 2, int(h * 0.8), w // 2, int(h * 0.3), 500)

    def screenshot(self, path: str) -> None:
        self.driver.get_screenshot_as_file(path)
