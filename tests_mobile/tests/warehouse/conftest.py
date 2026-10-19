"""S-05 mobil katalog guruhi seed'i (session scope, kod varianti ``{code}11``).

``S05_MOBILE_SEED=<kod>`` berilsa web seed (~10 daq) o'tkazib yuboriladi va mavjud seed
ishlatiladi. pytest muvaffaqiyatsiz fixture'ni keshlamaydi — seed xatosi bir marta
qayd qilinadi, keyingi testlar seed'ni qayta yaratmaydi.
"""
import os

import pytest
from playwright.sync_api import Page

from tests_mobile.tests.warehouse.catalog_helpers import catalog_names, create_catalog_seed

SEED_ENV = "S05_MOBILE_SEED"
_SEED_FAILED: dict = {}


@pytest.fixture(scope="session")
def catalog_seed(session_page: Page, code) -> dict:
    if _SEED_FAILED:
        pytest.fail(f"Seed oldingi testda yiqilgan ({_SEED_FAILED['c']}): {_SEED_FAILED['error']}")
    reuse = (os.getenv(SEED_ENV) or "").strip()
    d = catalog_names(reuse or f"{code}11")
    if reuse:
        print(f"\n[{SEED_ENV}] mavjud seed ishlatiladi: {d['c']}", flush=True)
        return d
    try:
        create_catalog_seed(session_page, d)
    except Exception as exc:
        _SEED_FAILED.update(c=d["c"], error=str(exc).splitlines()[0][:300])
        raise
    print(f"\n[seed] tayyor: {d['c']}  (qayta ishlatish: $env:{SEED_ENV}='{d['c']}')", flush=True)
    return d
