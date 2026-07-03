from playwright.sync_api import Page

from flows.flow_authorization import authorization
from tests.test_Templates import run_shablon
from tests.test_Vaprost import run_vaprost
from tests.test_bonus import run_bonus
from tests.test_category import run_category
from tests.test_client import run_client
from tests.test_criterya import run_criterya
from tests.test_form_of_ownership import run_form_of_ownership
from tests.test_industry import run_industry
from tests.test_konkurs import run_konkurs
from tests.test_legal_person import run_legal_person
from tests.test_manufacturer import run_manufacturer
from tests.test_oprosniki import run_oprsoniki
from tests.test_product import run_product
from tests.test_region import run_region
from tests.test_supplier import run_supplier
from tests.test_teritory import run_territory
from tests.test_Валюты import run_valyuta


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

    run_client(page, code)

    run_legal_person(page, code)

    run_valyuta(page, code)

    run_konkurs(page, code)

    run_bonus(page, code)

    run_territory(page, code)

    run_vaprost(page, code)

    run_oprsoniki(page, code)

    run_criterya(page, code)

    run_shablon(page, code)











