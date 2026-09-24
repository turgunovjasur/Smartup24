"""Mobil biznes oqimlari — bir nechta ekranni birlashtiradi (web flows/ ekvivalenti)."""
import allure

from tests_mobile.screens.cart_screen import CartScreen
from tests_mobile.screens.catalog_screen import CatalogScreen
from tests_mobile.screens.orders_screen import OrdersScreen


def create_and_verify_order(driver, supplier: str, category: str, product: str,
                            qty: int = 1, payment: str = "Наличные") -> None:
    """Login qilingan klient nomidan zakaz beradi va tafsilotini tekshiradi."""
    catalog, cart, orders = CatalogScreen(driver), CartScreen(driver), OrdersScreen(driver)

    with allure.step(f"Katalog: {supplier} / {category} / {product} x{qty}"):
        catalog.open_supplier(supplier)
        catalog.open_category(category)
        catalog.add_to_cart(product, qty)

    with allure.step(f"Savat: {payment}, ertangi sana, Оформить"):
        cart.open()
        cart.choose_payment(payment)
        cart.choose_delivery_date(days_ahead=1)
        cart.checkout()

    with allure.step("Zakaz tafsilotini tekshirish"):
        orders.open_last()
        orders.verify(supplier, product, payment)
