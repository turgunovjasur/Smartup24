"""OrderScreen — Smartup24 mobil ilovada klient nomidan ZAKAZ berish (page object).

Web `tests/test_group_a/test_order.py` (run_order) ning MOBIL ekvivalenti, LEKIN
mobil oqim boshqacha (savat/do'kon uslubi) — real qurilmада kashf qilingan va
user tasdiglagan (2026-09-23). Oqim:

    Постав. (postavshiklar) → Поставщики ro'yxati (qidiruv YO'Q, scroll)
      → supplier kartаsидаgi "Показать каталог"
    → supplier sahifasi → "Категории" tab → kategoriya
    → tovar kartаsидаgi "В корзину 1 шт"  (+ / − bilan miqdor)
    → "Корзина" (savat)
    → "Тип оплаты" → Наличные → Применить
    → "Дата доставки" → sana → Принять
    → tovarни belgilash (Выбрать все) → "Оформить"
    → "Заказы" ro'yxatiga o'tadi; buyurtma ЧЕРНОВИК statusида tushadi
      (supplier sahifasida "Черновик(N)" bilan tasdiqlangan)

DISAMBIGUATSIYA: bir xil content-desc'li elementlar ko'p (har supplierда
"Показать каталог", har tovarда "В корзину"). Kerakli elementни NOMига BOG'LAB
(descendant XPath) bosamiz — real qurilmада tasdiqlangan pattern:
    //*[contains(@content-desc,'<nom>')]//*[@content-desc='<tugma>']
"""
from __future__ import annotations

import time
from datetime import date, timedelta

from appium.webdriver.common.appiumby import AppiumBy

from tests_mobile.pages.base_screen import BaseScreen

# Pastki navigatsiya
_SUPPLIERS_TAB = "Постав."
_HOME_TAB = "Главная"
_CATALOG_TAB = "Каталог"

# Savat / rasmiylashtirish
_SHOW_CATALOG = "Показать каталог"
_ADD_TO_CART_PREFIX = "В корзину"      # "В корзину 1 шт"
_SELECT_ALL = "Выбрать все"
_CHECKOUT = "Оформить"
_PAYMENT_FIELD = "Тип оплаты"          # "Тип оплаты*\nНе выбран"
_PAYMENT_APPLY = "Применить"
_DATE_FIELD = "Дата доставки"          # "Дата доставки*\nНе выбран"
_DATE_ACCEPT = "Принять"
_ORDERS_HEADER = "Заказы"

# Ruscha sana (date picker View desc: "четверг, 24 сентября 2026 г.")
_RU_WEEKDAYS = {
    0: "понедельник", 1: "вторник", 2: "среда", 3: "четверг",
    4: "пятница", 5: "суббота", 6: "воскресенье",
}
_RU_MONTHS_GEN = {
    1: "января", 2: "февраля", 3: "марта", 4: "апреля", 5: "мая", 6: "июня",
    7: "июля", 8: "августа", 9: "сентября", 10: "октября", 11: "ноября", 12: "декабря",
}


def ru_date_desc(d: date) -> str:
    """date → date picker'даgi content-desc ("четверг, 24 сентября 2026 г.")."""
    return f"{_RU_WEEKDAYS[d.weekday()]}, {d.day} {_RU_MONTHS_GEN[d.month]} {d.year} г."


class OrderScreen(BaseScreen):
    """Klient nomidan yangi zakaz beradi. LoginScreen orqali klient
    foydalanuvchisi bilan kirilgan bo'lishi kutiladi."""

    # ── qadamlar ──────────────────────────────────────────────────────────
    def open_supplier_catalog(self, supplier_name: str) -> None:
        """Постав. → Поставщики ro'yxatida supplierni topib (scroll) uning
        'Показать каталог' tugmasini bosadi (nomга bog'langan descendant XPath)."""
        xp = (f"//*[contains(@content-desc, '{supplier_name}')]"
              f"//*[@content-desc='{_SHOW_CATALOG}']")
        # ILOVA QUIRK (user tasdiqlagan 2026-09-23): bo'lim tabini bosганда oyna
        # ba'zан 1-bosishда OCHILMAYDI — o'shani QAYTA bosиш kerak. Shuning uchun
        # supplier ro'yxati (Показать каталог) ko'rinмаса "Постав." ni qayta bosamiz;
        # ko'ringач scroll bilan supplierни topib "Показать каталог" ni bosamiz.
        for _ in range(4):
            self.tap(_SUPPLIERS_TAB)
            time.sleep(1.5)
            for _ in range(6):
                if self._exists_xpath(xp, timeout=1):
                    self._tap_xpath(xp)
                    self._wait_marker("Категории")  # supplier sahifasi ochilди
                    return
                self.scroll_down(times=1)
        self._tap_xpath(xp)  # oxirgi urinish — topilmаса aniq xato beradi
        self._wait_marker("Категории")

    def open_category(self, category: str) -> None:
        """Supplier sahifasidagi 'Категории' tab kategoriyasini bosadi. Bir xil
        nom info bo'limида ham bo'lishi mumkin — OXIRGI mos kelgani (Категории
        tabдаgi) tanlanadi."""
        self._tap_xpath(f"(//*[@content-desc='{category}'])[last()]")
        # Tovarlar ASINXRON yuklanadi — kamida bitta "В корзину" (yoki savatда
        # bo'lса "шт") ko'ringunча kutamiz, aks holда add_to_cart bo'sh ro'yxatда
        # tovarни topolmай jim o'tib ketadi.
        for _ in range(12):
            if self._exists_xpath(
                f"//*[contains(@content-desc, '{_ADD_TO_CART_PREFIX}')]", timeout=1
            ):
                break
            time.sleep(0.5)
        time.sleep(1)

    def add_to_cart(self, product_name: str, qty: int = 1) -> None:
        """Tovar kartаsидаgi 'В корзину 1 шт' ni bosadi (nomга bog'langan). qty>1
        bo'lса '+' ni (qty-1) marta bosadi."""
        xp_prod = f"//*[contains(@content-desc, '{product_name}')]"
        xp_add = f"{xp_prod}//*[contains(@content-desc, '{_ADD_TO_CART_PREFIX}')]"
        # DIQQAT: "В корзину" tugmasi karta ekranга TO'LIQ chiqгандаgina
        # renderlanadi (past tovarларники DOM'да bo'lmaydi) — shuning uchun
        # TOVARNI emas, uning "В корзину" TUGMASINI ko'ringunча scroll qilamiz.
        added = False
        for _ in range(10):
            if self._exists_xpath(xp_add, timeout=1):
                self._tap_xpath(xp_add)
                time.sleep(1)
                added = True
                break
            self.scroll_down(times=1)
        # added=False → tovar allaqachon savatда ("N шт", "В корзину" yo'q) —
        # qayta qo'shmaymiz.
        if added:
            # qty>1: qatordagi "+" tugmasi (В корзину endi "N шт" ga aylandi)
            for _ in range(max(0, qty - 1)):
                self._tap_xpath(
                    f"//*[contains(@content-desc, '{product_name}')]//*[@content-desc='+']"
                )
                time.sleep(0.5)

    def open_cart(self) -> None:
        """Pastki navigatsiyadagi 'Корзина' tabга o'tadi. "Корзина" bir necha
        joyда uchraydi (suzuvchi "Корзина\\n<summa>" paneli, sarlavha) — pastki
        nav DARAXTNING OXIRIDA bo'lgani uchun OXIRGI mos kelgani tanlanadi.

        ILOVA QUIRK: bo'lim 1-bosishда ochilmasligi mumkin — savат oynasi
        ('Оформить' belgisi) ko'rinмаса QAYTA bosamiz."""
        for _ in range(3):
            self._tap_xpath("(//*[contains(@content-desc, 'Корзина')])[last()]")
            time.sleep(1.5)
            if self._exists_xpath(f"//*[@content-desc='{_CHECKOUT}']", timeout=2):
                return

    def choose_payment(self, payment: str = "Наличные") -> None:
        """Тип оплаты → payment → Применить. Dialog 1-bosishда ochilmasligi
        mumkin (ilova quirk) — payment varianti ko'ringunча "Тип оплаты" ni
        qayta bosamiz."""
        time.sleep(1)
        self._open_overlay(_PAYMENT_FIELD, payment)
        self.tap(payment)
        self.tap(_PAYMENT_APPLY)
        time.sleep(1)

    def choose_delivery_date(self, days_ahead: int = 1) -> None:
        """Дата доставки → (bugun+days_ahead) sanani tanlash → Принять. Kalendar
        1-bosishда ochilmasligi mumkin — "Принять" ko'ringunча qayta bosamiz."""
        target = date.today() + timedelta(days=days_ahead)
        time.sleep(1)
        self._open_overlay(_DATE_FIELD, _DATE_ACCEPT)
        self.tap(ru_date_desc(target))
        self.tap(_DATE_ACCEPT)
        time.sleep(1)

    def place_order(self, supplier_name: str | None = None) -> None:
        """Tovar tanlanганини ta'minlab 'Оформить' ni bosadi.

        TANLASH: har tovar qatorida haqiqiy ``android.widget.CheckBox`` (птичка)
        bor; savatga YANGI qo'shilган tovar odatda AVTOMATIK belgilangan bo'ladi —
        shunda hech narsa bosмаймиз (allaqachon belgilanган checkboxни qayta
        bosиш uni YECHADI!). Faqat tanlanмаган bo'lса ("Итого: 0 товаров") tovar
        qatori checkboxини belgilaymiz. "Выбрать все" VIEW yoki supplier guruh
        sarlavhасини bosiш TANLAMAYDI — MCP tasdiqlangan 2026-09-23."""
        if self._exists_xpath("//*[@content-desc='0 товаров']", timeout=2):
            boxes = self.driver.find_elements(AppiumBy.CLASS_NAME, "android.widget.CheckBox")
            if boxes:
                boxes[-1].click()   # oxirgi CheckBox = tovar qatori (1-chisi "Выбрать все")
                time.sleep(1)
        self.tap(_CHECKOUT)
        # Zakaz urilгач "Заказы" ro'yxatiga o'tadi — o'sha belgini kutamiz
        self._wait_marker(_ORDERS_HEADER)

    # ── to'liq oqim ────────────────────────────────────────────────────────
    def create_order(
        self,
        supplier_name: str,
        category: str,
        product_name: str,
        qty: int = 1,
        payment: str = "Наличные",
        days_ahead: int = 1,
    ) -> None:
        self.open_supplier_catalog(supplier_name)
        self.open_category(category)
        self.add_to_cart(product_name, qty)
        self.open_cart()
        self.choose_payment(payment)
        self.choose_delivery_date(days_ahead)
        self.place_order(supplier_name)

    def is_order_created(self) -> bool:
        """Оформить'дан keyin 'Заказы' ro'yxatiga o'tганини tekshiradi (save +
        navigatsiya biroz vaqt oladi)."""
        return self.is_visible(_ORDERS_HEADER, timeout=15)

    # ── zakaz detalини ochib TEKSHIRISH ──────────────────────────────────────
    def open_last_order(self) -> None:
        """'Заказы' ro'yxatidan eng yangi (birinchi) zakazni ochadi. Zakaz kartаsи
        content-desc'i "#... Заказ для ... Черновик ..." ko'rinishida."""
        self._wait_marker(_ORDERS_HEADER)  # ro'yxat ochilганини kutamiz
        self._tap_xpath("(//*[contains(@content-desc, 'Заказ для')])[1]")
        # Detail ochilганини kutamiz — tovar jadvalidagi "Название товара" sarlavhasi
        self._wait_marker("Название товара")

    def verify_order(self, supplier_name: str, product_name: str,
                     payment: str = "Наличные") -> None:
        """Ochilган zakaz DETALIда asosiy ma'lumotlarни tekshiradi (Поставщик,
        tovar nomi, to'lov turi). Topilmаса ANIQ xato beradi — nima yetishmaganини
        aytadi."""
        checks = {
            f"Поставщик «{supplier_name}»": self._exists_contains(supplier_name, timeout=10),
            f"Товар «{product_name}»": self._exists_contains(product_name, timeout=5),
            f"Тип оплаты «{payment}»": self._exists_contains(payment, timeout=5),
        }
        missing = [k for k, ok in checks.items() if not ok]
        assert not missing, "Zakaz detalида topilmadi: " + "; ".join(missing)
