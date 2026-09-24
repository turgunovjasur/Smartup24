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
```powershell
# 1) Appium — ALOHIDA terminalda (Claude/IDE fon jarayoni xotira kam bo'lsa o'ldiriladi):
appium --address 127.0.0.1 --port 4723 --use-plugins=inspector --allow-cors

# 2) Testlar (default user config.py da; env bilan almashtirsa bo'ladi: MOBILE_LOGIN/MOBILE_PASSWORD)
.venv\Scripts\python -m pytest tests_mobile/tests/test_login.py -v --alluredir=test-results/allure-results
.venv\Scripts\python -m pytest tests_mobile/tests/test_order_smoke.py -v   # ~2-3 min, tayyor data
.venv\Scripts\python -m pytest tests_mobile/tests/test_order_e2e.py -v     # ~6 min, web+mobil
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
└── tools/explore.py      # locator kashfiyoti (test emas); Appium Inspector — muqobil
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
