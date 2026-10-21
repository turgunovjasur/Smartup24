# tests_mobile — Smartup24 Android (Appium) testlari

Web (Playwright) testlaridan **ALOHIDA** stack. Bir-biriga aralashmaydi:
`pytest.ini` da `tests_mobile` `norecursedirs` da — web `pytest` uni yig'maydi.
Mobil testlar faqat aniq chaqirilganda ishlaydi.

## Nima ustida
- Ilova: **Smartup24 mobil** (`uz.greenwhite.smartup24`) — **Flutter** ilova.
- Vosita: **Appium 2 + UiAutomator2 driver** + Python (`Appium-Python-Client`).
- Locator: Flutter ilova ko'rinadigan matnni **`content-desc`** (accessibility)
  sifatida beradi — element shu orqali topiladi (`resource-id` YO'Q). Matnsiz
  maydonlar (input) `android.widget.EditText` klassi bo'yicha (tartib bilan).

## Bir martalik o'rnatish (kompyuterga, repoga EMAS)
```powershell
npm install -g appium                       # Appium server
appium driver install uiautomator2          # Android driver
winget install --id Google.PlatformTools    # adb (platform-tools)
# ANDROID_HOME -> platform-tools ning ota-papkasi (doimiy):
[Environment]::SetEnvironmentVariable("ANDROID_HOME", "<...>\platform-tools ning ota-papkasi", "User")
.venv\Scripts\python -m pip install -r tests_mobile\requirements-mobile.txt
```

## Qurilma (real telefon, USB)
1. Developer options -> **USB debugging** YOQ.
2. Telefonni USB bilan ula; "USB debugging'ga ruxsat" -> "Doim ruxsat".
3. **Xiaomi/MIUI SHART:** Developer options -> **"USB debugging (Security
   settings)"** ni YOQ (Mi account + SIM kerak). Busiz MIUI tap/o'rnatishni
   bloklaydi (`INJECT_EVENTS` / `INSTALL_GRANT_RUNTIME_PERMISSIONS` xatolari).
4. Telefon qulfi ochiq tursin. Ekran o'chmasligi uchun:
   `adb shell svc power stayon true`.

## Ishga tushirish
**Emulyator bilan — mobil run oldidan bitta buyruq:**
```powershell
powershell -File tests_mobile/tools/start_emulator.ps1          # headless (-no-window, swiftshader_indirect)
powershell -File tests_mobile/tools/start_emulator.ps1 -Window  # oynali rejim (ixtiyoriy; GPU xatosi bilan qulashi mumkin)
```
Emulyator allaqachon boot bo'lgan bo'lsa qayta yoqmaydi; aks holda qotgan emulator/qemu/crashpad
jarayonlari va AVD `*.lock` larini tozalab `Medium_Phone_API_37.0` ni `ANDROID_SDK_ROOT=%LOCALAPPDATA%\Android\Sdk`
bilan yoqadi, `sys.boot_completed=1` ni kutadi (300 s; timeoutda `test-results/emulator*.log` oxiri),
Appium 4723 yo'q bo'lsa alohida "Appium — YOPMANG" oynasida ochadi, ilovani bir marta oldindan ochadi va holatni
chiqaradi (hammasi tayyor — exit 0). Shundan keyin pastdagi 2-qadam (pytest).

**Qo'lda (real telefon):**
```powershell
# 1) Appium — ALOHIDA terminalda (Claude/IDE fon jarayoni xotira kam bo'lsa o'ldiriladi):
appium --address 127.0.0.1 --port 4723 --use-plugins=inspector --allow-cors

# 2) Testlar (default user config.py da; env bilan almashtirsa bo'ladi: MOBILE_LOGIN/MOBILE_PASSWORD)
.venv\Scripts\python -m pytest tests_mobile/tests/test_login.py -v --alluredir=test-results/allure-results
.venv\Scripts\python -m pytest tests_mobile/tests/test_order_smoke.py -v   # ~2-3 min, tayyor data
.venv\Scripts\python -m pytest tests_mobile/tests/test_order_e2e.py -v     # ~6 min, web+mobil
.venv\Scripts\python -m pytest tests_mobile/tests/warehouse/test_warehouse_delete_e2e.py -v # S-05.1.2 ombor o'chirish, web+mobil
$env:S05_MOBILE_SEED='<kod>'   # ixtiyoriy: mavjud seed'ni qayta ishlatish (web seed ~10 daq o'tkazib yuboriladi)
.venv\Scripts\python -m pytest tests_mobile/tests/warehouse/test_warehouse_catalog.py -v # S-05 mobil katalog (4.1/4.2/4.3/2.2/3.1/3.3)
```
Test boshida preflight Appium va telefonni tekshiradi; yo'q bo'lsa aniq xabar bilan to'xtaydi.
Yiqilgan testning telefon ekrani va ekran tuzilmasi Allure'ga (va `screenshots/`) tushadi.

## Tuzilma
```
tests_mobile/
├── conftest.py           # preflight, driver fixture, yiqilganda artefaktlar
├── config.py             # server, ilova, userlar, smoke ma'lumotlari — YAGONA joy
├── flows.py              # biznes oqimlar (create_and_verify_order)
├── core/driver_factory.py  # Appium sessiya sozlamalari — YAGONA joy
├── screens/              # page object'lar (har biri ilovadagi bitta ekran)
│   ├── base_screen.py    # locator: desc() / contains() / xpath(); tap / exists / wait_for / wait_gone / type
│   ├── login_screen.py
│   ├── catalog_screen.py # Постав. -> katalog -> kategoriya -> savatga
│   ├── cart_screen.py    # to'lov, sana, Оформить
│   └── orders_screen.py  # Заказы: ochish va tekshirish
├── tests/                # faqat testlar
└── tools/
    ├── explore.py        # locator kashfiyoti (test emas); Appium Inspector — muqobil
    └── start_emulator.ps1  # emulyator + Appium + ilovani tayyorlash (mobil run oldidan)
```

## Yangi test yozish qoidalari
- Locatorni taxmin qilma — Appium Inspector bilan real ekranda tasdiqla.
- Locator ekran faylining TEPASIDA konstanta; testda raw XPath yozilmaydi.
- `time.sleep` o'rniga `exists` / `wait_for` / `wait_gone`.
- Bir xil tugma ko'p joyda bo'lsa nomga bog'la: `//*[contains(@content-desc,'<nom>')]//*[@content-desc='<tugma>']`.

## Ilova xususiyatlari (Flutter)
- `resource-id` YO'Q; matn `content-desc` da; inputlar faqat `EditText` tartibi bilan.
- Tab/dialog ba'zan 1-bosishda ochilmaydi, tez qayta bosish esa ochilganini yopadi
  -> `BaseScreen.open_overlay` kutib, kerak bo'lsagina qayta bosadi.
- `no_reset=True`: login saqlanadi; har test oldidan ilova yopib qayta ochiladi.
- Savatda yangi tovar avtomatik belgilangan — belgilangan checkboxni bosish uni yechadi.
- Kamera (Штрих-код) real qurilmada ishlaydi, emulatorda cheklangan.
- Katalog (2026-10-15, emulyator): kategoriyada mijoz regionida ombor bo'lmasa `Ничего не найдено!`;
  supplierda tovarli ombor bo'lmasa "Категории" tabi yo'q (faqat `Контакты | Вкладка 1 из 1`) —
  `CatalogScreen.open_supplier(require_categories=False)`, `has_category`, `open_category_listing` (yuklanishni kutadi), `has_product`.
- Emulyator: Android Studio `emulator-5554` ham ishlaydi (MIUI cheklovi yo'q).
- Tovar sahifasi: `CatalogScreen.open_product` (karta rasmiga bosadi), `supplier_offers` («Другие поставщики» qatorlari soni, barqarorlikni kutadi).
- `core/driver_factory.py`: `new_command_timeout=1800` (web+mobil testda uzoq web qadamlar).
