"""CatalogScreen — Постав. -> supplier katalogi -> kategoriya -> savatga qo'shish.

Bir xil tugma ko'p joyda bor (har supplierda "Показать каталог", har tovarda
"В корзину") — shuning uchun tugma NOMGA bog'lab olinadi:
    //*[contains(@content-desc, '<nom>')]//*[@content-desc='<tugma>']
"""
from __future__ import annotations

import re
import time

import allure
from selenium.webdriver.support.ui import WebDriverWait

from tests_mobile.screens.base_screen import BaseScreen, contains, desc, xpath

SUPPLIERS_TAB = desc("Постав.")
SHOW_CATALOG = "Показать каталог"
ADD_TO_CART = "В корзину"        # "В корзину 1 шт" / "В корзину 1 кг" (birlik tovarga bog'liq)
PLUS = "+"                       # savatdagi tovar: "+ / N <birlik>" boshqaruvi
CATEGORIES_MARKER = contains("Категории")
# Supplier sahifasi tablari: "Категории | Вкладка 1 из 2", "Контакты | Вкладка 2 из 2".
# Supplierning HECH BIR omborida tovar bo'lmasa "Категории" tabi YO'Q — faqat
# "Контакты | Вкладка 1 из 1" (emulyatorda tasdiqlangan 2026-10-15).
SUPPLIER_TABS = contains("Вкладка")
# Tab content-desc'lari (real ekran, 2026-10-15; bo'shliqlar NBSP \xa0):
#   "Категории\nВкладка\xa01\xa0из\xa02" / "Контакты\nВкладка\xa02\xa0из\xa02"
#   tovarsiz supplier: FAQAT "Контакты\nВкладка\xa01\xa0из\xa01"
CATEGORIES_TAB = xpath("//*[contains(@content-desc, 'Категории') and contains(@content-desc, 'Вкладка')]")
CONTACTS_ONLY_TAB = xpath("//*[contains(@content-desc, 'Контакты') "
                          "and contains(@content-desc, 'Вкладка 1 из 1')]")
# Kategoriya ichida mijoz regionidagi omborda tovar bo'lmasa (2026-10-15 tasdiqlangan)
NOTHING_FOUND = desc("Ничего не найдено!")
ANY_PRODUCT = xpath(f"//*[contains(@content-desc, '{ADD_TO_CART}') or @content-desc='{PLUS}']")
# Tovar sahifasi → "Другие поставщики" → "Изменить поставщика" varag'i (c:exp_product_supplier_list):
# har taklif qatori "[Самое выгодное |] <supplier> | <narx> сум/<birlik> | <regionlar>",
# pastida "Отменить" (emulyatorda tasdiqlangan 2026-10-16).
OTHER_SUPPLIERS = desc("Другие поставщики")
CHANGE_SUPPLIER_SHEET = desc("Изменить поставщика")
SHEET_CANCEL = desc("Отменить")
# Qoldiq (stock_quantity) — faqat supplier «Кому показывать остатки» ro'yxatidagi mijozga
# (emulyatorda tasdiqlangan 2026-10-19; bo'shliqlar oddiy probel):
#   karta desc 1-qatori "2 000 000 кг\nНовинка\n<nom>\n\n<narx> сум/кг\n<supplier>";
#   tovar sahifasida alohida element "В наличии: 2 000 000 кг". Ruxsatsiz mijozda ikkalasi YO'Q.
STOCK_ON_PAGE = xpath("//*[starts-with(@content-desc, 'В наличии:')]")
_QTY = re.compile(r"^(\d[\d ]*)\s+\S+$")      # "2 000 000 кг"


def _qty(text: str) -> int | None:
    m = _QTY.match(text.strip())
    return int(m.group(1).replace(" ", "")) if m else None


class CatalogScreen(BaseScreen):

    def open_supplier(self, supplier: str, require_categories: bool = True) -> None:
        """Постав. ro'yxatidan supplierni topib (scroll) katalogini ochadi.
        Ilova tabni 1-bosishda ochmasligi mumkin -> ro'yxat chiqmasa qayta bosamiz.
        ``require_categories=False`` — "Категории" tabi bo'lmasligi ham mumkin
        (tovarsiz supplier): sahifa tablari yuklanishi kutiladi."""
        any_card = desc(SHOW_CATALOG)
        card_btn = xpath(f"//*[contains(@content-desc, '{supplier}')]//*[@content-desc='{SHOW_CATALOG}']")
        for _ in range(4):
            self.tap(SUPPLIERS_TAB)
            if not self.exists(any_card, timeout=8):
                continue
            for _ in range(8):
                if self.exists(card_btn, timeout=2):
                    self.tap(card_btn)
                    marker = CATEGORIES_MARKER if require_categories else SUPPLIER_TABS
                    self.wait_for(marker, timeout=20, error="Supplier sahifasi ochilmadi")
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
        # Sekin internetda (4G) kartalar uzoq "skelet" holatida turadi -> 30s
        self.wait_for(any_product, timeout=30, error=f"'{category}' kategoriyasida tovarlar yuklanmadi (30s)")

    def supplier_has_categories(self, timeout: float = 30) -> bool:
        """Supplier sahifasi tablari TO'LIQ yuklangach: True — "Категории" tabi bor;
        False — yagona tab "Контакты | Вкладка 1 из 1" (tovarli ombor yo'q, tasdiqlangan
        fakt). Ikkalasidan biri chiqmaguncha kutadi — sekin render'da soxta "yo'q" bermaydi."""
        idx = self.wait_any(CATEGORIES_TAB, CONTACTS_ONLY_TAB, timeout=timeout,
                            error=f"Supplier sahifasi tablari yuklanmadi ({timeout}s)")
        return idx == 0

    def find_category(self, category: str, timeout: float = 15, scrolls: int = 3) -> bool:
        """"Категории" tabi BOR bo'lganda (supplier_has_categories() True) kategoriyani
        scroll bilan qidiradi. Topilmasa — bu supplierda shu kategoriya yo'q."""
        loc = desc(category)
        if self.exists(loc, timeout=timeout):
            return True
        for _ in range(scrolls):
            self.scroll_down()
            if self.exists(loc, timeout=3):
                return True
        return False

    def open_category_listing(self, category: str, timeout: float = 60) -> bool:
        """Kategoriyani ochadi va ro'yxat YUKLANGANINI kutadi (premature emas):
        True — tovar kartalari chiqdi; False — "Ничего не найдено!" (bo'sh).
        Sekin qurilmada kartalar uzoq kulrang skeleton holatida turadi (content-desc'siz,
        ANY_PRODUCT ham NOTHING_FOUND ham yo'q) — kutish davom etadi, shuning uchun 60s."""
        self.tap(xpath(f"(//*[@content-desc='{category}'])[last()]"))
        idx = self.wait_any(ANY_PRODUCT, NOTHING_FOUND, timeout=timeout,
                            error=f"'{category}' kategoriyasi yuklanmadi ({timeout}s)")
        return idx == 0

    def has_product(self, product: str, scrolls: int = 3) -> bool:
        """Yuklangan kategoriya ro'yxatida tovar kartasi bormi (pastga scroll bilan)."""
        card = contains(product)
        for i in range(scrolls + 1):
            if self.exists(card, timeout=2):
                return True
            if i < scrolls:
                self.scroll_down()
        return False

    def _card(self, product: str):
        """Yuklangan ro'yxatdagi tovar KARTASI elementi ("В корзину" tugmasi emas)."""
        return self.wait_for(xpath(f"//*[contains(@content-desc, '{product}') and contains(@content-desc, 'сум')"
                                   f" and not(contains(@content-desc, '{ADD_TO_CART}'))]"),
                             error=f"'{product}' kartasi topilmadi")

    def card_stock(self, product: str) -> int | None:
        """Kartadagi qoldiq (desc'da tovar nomidan OLDINGI "2 000 000 кг" qatori);
        qoldiq ko'rsatilmasa None. Karta o'zi yuklangan — soxta "yo'q" bo'lmaydi."""
        raw = self._card(product).get_attribute("content-desc") or ""
        allure.attach(raw, name=f"karta desc: {product}", attachment_type=allure.attachment_type.TEXT)
        lines = raw.split("\n")
        # Format o'zgarsa jim None (soxta "qoldiq yo'q") bo'lmasin — yiqilamiz
        assert product in lines, f"Karta desc kutilgan formatda emas (nom alohida qator emas): {raw!r}"
        head = [ln for ln in lines[:lines.index(product)] if ln.strip() and ln.strip() != "Новинка"]
        qtys = [_qty(ln) for ln in head]
        assert None not in qtys and len(qtys) <= 1, f"Karta desc'ida nomdan oldin noma'lum qator: {raw!r}"
        return qtys[0] if qtys else None

    def page_stock(self, timeout: float = 5) -> int | None:
        """Tovar sahifasida (open_product'dan keyin) "В наличии: N <birlik>"; yo'q bo'lsa None.
        Element narx bilan bir modeldan chiziladi — sahifa ochilgach ``timeout`` ichida
        chiqmasa, yo'q deb hisoblanadi."""
        if not self.exists(STOCK_ON_PAGE, timeout=timeout):
            return None
        text = self.driver.find_element(*STOCK_ON_PAGE).get_attribute("content-desc") or ""
        qty = _qty(text.split(":", 1)[1])
        assert qty is not None, f"Qoldiq yozuvi kutilmagan formatda: {text!r}"
        return qty

    def open_product(self, product: str) -> None:
        """Yuklangan kategoriya ro'yxatida tovar KARTASINI ("В корзину" emas) bosib,
        tovar sahifasini ochadi (karta desc: "Новинка | <nom> | | <narx> сум/кг | <supplier>")."""
        card = self._card(product)
        # Karta elementi bounds'i butun qator kengligida, karta esa 2 ustunli setkada chap
        # yoki o'ng yarmida — markazga bosish bo'sh joyga tushadi (2026-10-16). Kartaning
        # rasm qismiga (chap-yuqori chorak) aniq nuqta bilan bosamiz.
        r = card.rect
        self.driver.tap([(int(r["x"] + r["width"] * 0.2), int(r["y"] + r["height"] * 0.2))])
        self.wait_for(OTHER_SUPPLIERS, timeout=60, error=f"'{product}' tovar sahifasi ochilmadi")

    def supplier_offers(self, supplier: str) -> int:
        """Tovar sahifasida "Другие поставщики" varag'ini ochib, ``supplier`` qatorlari
        sonini qaytaradi (varag' oxiridagi "Отменить" chiqqach — ro'yxat chizilgan)."""
        self.tap(OTHER_SUPPLIERS)
        self.wait_for(CHANGE_SUPPLIER_SHEET, timeout=30, error="'Изменить поставщика' varag'i ochilmadi")
        row = xpath(f"//*[contains(@content-desc, '{supplier}') and contains(@content-desc, 'сум')]")
        # Qatorlar varag'dan keyin asinxron chiziladi (emulyatorda ~3-4 s, 2026-10-16) —
        # kamida bittasi chiqqach, ketma-ket ikki o'qishda soni bir xil bo'lguncha kutamiz.
        self.wait_for(row, timeout=30, error=f"'{supplier}' qatori varag'da chiqmadi")
        last = {"n": -1}

        def _stable(drv):
            n = len(drv.find_elements(*row))
            same, last["n"] = n == last["n"], n
            return n if same else False
        return WebDriverWait(self.driver, 20, poll_frequency=2).until(_stable)

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
