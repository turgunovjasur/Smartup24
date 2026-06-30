from test_all_product import test_all_product
from test_bonus_system_runner import test_bonus_system_runner
from test_client import test_client_all_runner
from test_konkurs import test_konkurs_all_runner
from test_legal_person import test_legal_person_runner
from test_region import test_region_all_runner
from test_supplier import test_supplier_all_runner
from test_teritorya import test_territory_all
from test_Вопросы import test_all_vaprost
from test_Опросники import test_oprosniki_all_runner
from test_Шаблоны_отчетов import test_shablon_all_runner


def test_all_runner(page,code):
    test_legal_person_runner(page,)
    test_supplier_all_runner(page,code)
    test_client_all_runner(page,code)
    test_all_product(page,code)
    test_bonus_system_runner(page,)
    test_region_all_runner(page,code)
    test_konkurs_all_runner(page,code)
    test_territory_all(page,code)
    test_all_vaprost(page,code)
    test_oprosniki_all_runner(page,code)
    test_shablon_all_runner(page,code)



