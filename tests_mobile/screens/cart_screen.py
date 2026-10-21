"""CartScreen — Корзина: to'lov turi, yetkazish sanasi, Оформить."""
from __future__ import annotations

import re
from datetime import date, timedelta

import allure
from appium.webdriver.common.appiumby import AppiumBy

from tests_mobile.screens.base_screen import BaseScreen, contains, desc, xpath

# "Корзина" bir necha joyda bor (suzuvchi panel, sarlavha) -> pastki nav = oxirgisi
CART_TAB = xpath("(//*[contains(@content-desc, 'Корзина')])[last()]")
CHECKOUT = desc("Оформить")
PAYMENT_FIELD = contains("Тип оплаты")        # desc: "Тип оплаты*\nНе выбран"
PAYMENT_APPLY = desc("Применить")
DATE_FIELD = contains("Дата доставки")
DATE_ACCEPT = desc("Принять")
NOTHING_SELECTED = desc("0 товаров")          # "Итого: 0 товаров"
ORDERS_MARKER = contains("Заказы")
# Savat qatori va tozalash (emulyatorda tasdiqlangan 2026-10-19):
#   qator desc "<nom>\n100 000 сум\n100 000 сум/кг[\nВ наличии: 2 000 000 кг]" — qoldiq qatori
#   faqat «Кому показывать остатки»dagi mijozda; «Удалить выбранные» → dialog «Удалить
#   выбранные товары?» → «Удалить» → «В корзине пусто!». Bo'sh savatda «Оформить» YO'Q.
DELETE_SELECTED = desc("Удалить выбранные")
DELETE_CONFIRM = desc("Удалить")
SELECT_ALL = desc("Выбрать все")
CART_EMPTY = desc("В корзине пусто!")
# DIQQAT: tovarli savatda ham tab bosilgach ro'yxat yuklanguncha «В корзине пусто!» (+ spinner)
# ko'rinadi — tez tarmoqda ~4.5 s, VPN'da undan uzoq; pastki tab esa darhol "1\nКорзина"
# (badge). Savat HAQIQATAN bo'sh = placeholder + badge'siz pastki tab (ImageView "Корзина";
# sarlavhadagi "Корзина" — View). Emulyatorda tasdiqlangan 2026-10-21.
CART_EMPTY_REAL = xpath("//*[@content-desc='В корзине пусто!']"
                        # ichki predikat ataylab global (document-root'dan): badge'siz Корзина tab
                        "[//android.widget.ImageView[@content-desc='Корзина']]")
_STOCK_LINE = re.compile(r"^В наличии:\s*(\d[\d ]*)\s+\S+$")

_RU_WEEKDAYS = ["понедельник", "вторник", "среда", "четверг", "пятница", "суббота", "воскресенье"]
_RU_MONTHS = ["января", "февраля", "марта", "апреля", "мая", "июня",
              "июля", "августа", "сентября", "октября", "ноября", "декабря"]


def ru_date_desc(d: date) -> str:
    """Kalendar kunining content-desc'i: "четверг, 24 сентября 2026 г."."""
    return f"{_RU_WEEKDAYS[d.weekday()]}, {d.day} {_RU_MONTHS[d.month - 1]} {d.year} г."


class CartScreen(BaseScreen):

    def _tab_desc(self) -> str:
        tabs = self.driver.find_elements(*CART_TAB)
        return (tabs[-1].get_attribute("content-desc") or "") if tabs else "<tab topilmadi>"

    def open(self) -> None:
        """Tovarli savatni ochadi ("Оформить" chiqquncha). Ilova tabni 1-bosishda ochmasligi
        mumkin -> qayta bosamiz. Ro'yxat yuklanguncha «В корзине пусто!» + spinner ko'rinadi
        (badge "1\\nКорзина" bilan) — bu bo'sh savat EMAS: "Оформить" yoki HAQIQIY bo'sh
        (badge'siz) holat chiqquncha kutamiz (urinish 20 s, 3 urinish; 2026-10-21, VPN)."""
        for _ in range(3):
            self.tap(CART_TAB)
            try:
                idx = self.wait_any(CHECKOUT, CART_EMPTY_REAL, timeout=20)
            except AssertionError:
                continue                      # tab ochilmadi / ro'yxat hali yuklanmoqda — qayta bosamiz
            if idx == 0:
                return
            raise AssertionError(f"Savat bo'sh («В корзине пусто!»), lekin tovar qo'shilgan edi — "
                                 f"badge: {self._tab_desc()!r}")
        if self.driver.find_elements(*CART_EMPTY):
            raise AssertionError(f"Savat ro'yxati yuklanmadi («В корзине пусто!» + spinner, 3x20 s) — "
                                 f"badge: {self._tab_desc()!r}")
        raise AssertionError("Savat ochilmadi ('Оформить' ham, «В корзине пусто!» ham chiqmadi, 3 urinish)")

    def row_stock(self, product: str) -> int | None:
        """Ochiq savatdagi ``product`` qatoridagi qoldiq ("В наличии: N <birlik>"); yo'q — None.
        Qator (nom + narx) yuklanishi kutiladi; desc formati o'zgarsa yiqiladi (soxta None emas)."""
        row = self.wait_for(xpath(f"//*[starts-with(@content-desc, '{product}') and contains(@content-desc, 'сум')]"),
                            timeout=30, error=f"Savatda '{product}' qatori chiqmadi")
        raw = row.get_attribute("content-desc") or ""
        allure.attach(raw, name=f"savat qatori: {product}", attachment_type=allure.attachment_type.TEXT)
        lines = [ln.strip() for ln in raw.split("\n")]
        assert lines[0] == product, f"Savat qatori kutilgan formatda emas: {raw!r}"
        stock = [ln for ln in lines[1:] if ln.startswith("В наличии")]
        assert all("сум" in ln for ln in lines[1:] if ln not in stock) and len(stock) <= 1, \
            f"Savat qatorida noma'lum qator: {raw!r}"
        if not stock:
            return None
        m = _STOCK_LINE.match(stock[0])
        assert m, f"Qoldiq yozuvi kutilgan formatda emas: {stock[0]!r}"
        return int(m.group(1).replace(" ", ""))

    def clear(self) -> None:
        """Savatni bo'shatadi: «Удалить выбранные» → «Удалить» → «В корзине пусто!».
        Belgilanmagan qator qolsa «Выбрать все» bilan qayta urinadi.
        Bo'shlik CART_EMPTY_REAL (badge'siz) bilan aniqlanadi — oddiy «В корзине пусто!»
        yuklanish paytida ham chiqadi va savat bo'shatilmay qolardi (2026-10-21)."""
        for attempt in range(3):
            self.tap(CART_TAB)
            try:
                idx = self.wait_any(CHECKOUT, CART_EMPTY_REAL, timeout=30)
            except AssertionError:
                raise AssertionError(f"Savat ochilmadi/yuklanmadi (30s, badge: {self._tab_desc()!r})") from None
            if idx == 1:
                return
            if attempt:
                self.tap(SELECT_ALL)
            if self.open_overlay(DELETE_SELECTED, DELETE_CONFIRM):
                self.tap(DELETE_CONFIRM)
                if self.exists(CART_EMPTY_REAL, timeout=15):
                    return
        raise AssertionError("Savat bo'shatilmadi ('В корзине пусто!' chiqmadi)")

    def choose_payment(self, payment: str = "Наличные") -> None:
        if not self.open_overlay(PAYMENT_FIELD, desc(payment)):
            raise AssertionError(f"'Тип оплаты' dialogi ochilmadi ('{payment}' chiqmadi)")
        self.tap(desc(payment))
        self.tap(PAYMENT_APPLY)
        self.wait_gone(PAYMENT_APPLY)

    def choose_delivery_date(self, days_ahead: int = 1) -> None:
        if not self.open_overlay(DATE_FIELD, DATE_ACCEPT):
            raise AssertionError("'Дата доставки' kalendari ochilmadi")
        self.tap(desc(ru_date_desc(date.today() + timedelta(days=days_ahead))))
        self.tap(DATE_ACCEPT)
        self.wait_gone(DATE_ACCEPT)

    def checkout(self) -> None:
        """Tovar belgilanganini ta'minlab "Оформить" ni bosadi.
        Yangi qo'shilgan tovar odatda AVTOMATIK belgilangan — unda hech narsa
        bosmaymiz (belgilangan checkboxni bosish uni YECHADI). Faqat "0 товаров"
        bo'lsa tovar qatori checkboxini (oxirgisi; 1-chisi "Выбрать все") bosamiz."""
        if self.exists(NOTHING_SELECTED, timeout=2):
            boxes = self.driver.find_elements(AppiumBy.CLASS_NAME, "android.widget.CheckBox")
            if boxes:
                boxes[-1].click()
            self.wait_gone(NOTHING_SELECTED, timeout=5,
                           error="Savatda tovar belgilanmadi ('Итого: 0 товаров' qoldi)")
        self.tap(CHECKOUT)
        self.wait_for(ORDERS_MARKER, timeout=20, error="Оформить'dan keyin 'Заказы' ochilmadi")
