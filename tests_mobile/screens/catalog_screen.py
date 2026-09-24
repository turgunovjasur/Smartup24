"""CatalogScreen — Постав. -> supplier katalogi -> kategoriya -> savatga qo'shish.

Bir xil tugma ko'p joyda bor (har supplierda "Показать каталог", har tovarda
"В корзину") — shuning uchun tugma NOMGA bog'lab olinadi:
    //*[contains(@content-desc, '<nom>')]//*[@content-desc='<tugma>']
"""
from __future__ import annotations

import time

from tests_mobile.screens.base_screen import BaseScreen, contains, desc, xpath

SUPPLIERS_TAB = desc("Постав.")
SHOW_CATALOG = "Показать каталог"
ADD_TO_CART = "В корзину"        # "В корзину 1 шт" / "В корзину 1 кг" (birlik tovarga bog'liq)
PLUS = "+"                       # savatdagi tovar: "+ / N <birlik>" boshqaruvi
CATEGORIES_MARKER = contains("Категории")


class CatalogScreen(BaseScreen):

    def open_supplier(self, supplier: str) -> None:
        """Постав. ro'yxatidan supplierni topib (scroll) katalogini ochadi.
        Ilova tabni 1-bosishda ochmasligi mumkin -> ro'yxat chiqmasa qayta bosamiz."""
        any_card = desc(SHOW_CATALOG)
        card_btn = xpath(f"//*[contains(@content-desc, '{supplier}')]//*[@content-desc='{SHOW_CATALOG}']")
        for _ in range(4):
            self.tap(SUPPLIERS_TAB)
            if not self.exists(any_card, timeout=8):
                continue
            for _ in range(8):
                if self.exists(card_btn, timeout=2):
                    self.tap(card_btn)
                    self.wait_for(CATEGORIES_MARKER, timeout=20, error="Supplier sahifasi ochilmadi")
                    return
                self.scroll_down()
        raise AssertionError(
            f"Поставщик '{supplier}' ro'yxatda topilmadi (yoki 'Постав.' ochilmadi) — "
            f"klient shu supplier bilan hamkorlikda ekanini tekshiring"
        )

    def open_category(self, category: str) -> None:
        # Nom info bo'limida ham bo'lishi mumkin -> oxirgisi (Категории tabdagi)
        self.tap(xpath(f"(//*[@content-desc='{category}'])[last()]"))
        # Tovarlar asinxron yuklanadi: "В корзину" yoki "+" (savatda) chiqquncha kutamiz.
        # Birlik (шт/кг) tovarga bog'liq — unga tayanmaymiz.
        any_product = xpath(f"//*[contains(@content-desc, '{ADD_TO_CART}') or @content-desc='{PLUS}']")
        self.wait_for(any_product, error=f"'{category}' kategoriyasida tovarlar yuklanmadi")

    def add_to_cart(self, product: str, qty: int = 1) -> None:
        """Tovarni savatga qo'shadi (allaqachon savatda bo'lsa tegmaydi).
        "В корзину" tugmasi karta ekranga TO'LIQ chiqqandagina renderlanadi ->
        tovarni emas, aynan shu tugmani ko'ringuncha scroll qilamiz."""
        prod = f"//*[contains(@content-desc, '{product}')]"
        add_btn = xpath(f"{prod}//*[contains(@content-desc, '{ADD_TO_CART}')]")
        plus_btn = xpath(f"{prod}//*[@content-desc='{PLUS}']")    # bor bo'lsa = allaqachon savatda
        for _ in range(10):
            if self.exists(add_btn, timeout=2):
                self.tap(add_btn)
                self.exists(plus_btn, timeout=5)      # tugma "+ / N <birlik>" ga aylanadi
                for _ in range(qty - 1):
                    self.tap(plus_btn)
                    time.sleep(0.5)                   # tez ketma-ket bosish yutiladi
                return
            if self.exists(plus_btn, timeout=1):
                return
            self.scroll_down()
        raise AssertionError(f"Tovar '{product}' katalogda topilmadi (10 marta scroll)")
