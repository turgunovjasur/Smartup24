"""OrdersScreen — Заказы ro'yxati va zakaz tafsiloti."""
from __future__ import annotations

from tests_mobile.screens.base_screen import BaseScreen, contains, xpath

ORDERS_MARKER = contains("Заказы")
FIRST_ORDER = xpath("(//*[contains(@content-desc, 'Заказ для')])[1]")   # eng yangisi tepada
DETAIL_MARKER = contains("Название товара")


class OrdersScreen(BaseScreen):

    def open_last(self) -> None:
        self.wait_for(ORDERS_MARKER, timeout=20, error="'Заказы' ro'yxati ochilmadi")
        self.tap(FIRST_ORDER)
        self.wait_for(DETAIL_MARKER, timeout=20, error="Zakaz tafsiloti ochilmadi")

    def verify(self, supplier: str, product: str, payment: str = "Наличные") -> None:
        """Ochiq zakaz tafsilotida supplier, tovar va to'lov turi borligini tekshiradi."""
        checks = {
            f"Поставщик «{supplier}»": self.exists(contains(supplier), timeout=10),
            f"Товар «{product}»": self.exists(contains(product), timeout=5),
            f"Тип оплаты «{payment}»": self.exists(contains(payment), timeout=5),
        }
        missing = [name for name, ok in checks.items() if not ok]
        assert not missing, "Zakaz tafsilotida topilmadi: " + "; ".join(missing)
