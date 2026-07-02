from playwright.sync_api import Page

from flows.flow_authorization import authorization
from tests.test_manufacturer import run_manufacturer
from tests.test_industry import run_industry
from tests.test_category import run_category
from tests.test_product import run_product
from tests.test_region import run_region
from tests.test_form_of_ownership import run_form_of_ownership
from tests.test_supplier import run_supplier


def test_all(page: Page, code) -> None:
    """Barcha moderator testlarini bitta seansda ketma-ket ishga tushiradi.

    Login bir marta qilinadi; keyin manufacturer -> industry -> category -> product
    zanjiri bir xil `page` va `code` bilan yuradi (product oldingi qadamlarda
    yaratilgan Производитель va Отрасль qiymatlariga bog'liq). Region mustaqil.
    """
    authorization(page)
    run_manufacturer(page, code)
    run_industry(page, code)
    run_category(page, code)
    run_region(page, code)
    run_product(page, code)

    run_form_of_ownership(page, code)
    run_supplier(page, code)
