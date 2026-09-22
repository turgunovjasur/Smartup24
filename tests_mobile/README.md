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
# 1) Appium serverni alohida terminalda yoqib qo'y:
appium --address 127.0.0.1 --port 4723

# 2) Login ma'lumotlari env orqali (koda yozilmaydi):
$env:MOBILE_LOGIN="<login>"; $env:MOBILE_PASSWORD="<parol>"

# 3) Testni ishga tushir:
.venv\Scripts\python -m pytest tests_mobile\test_login.py -v -s
```

## Tuzilma
```
tests_mobile/
├── conftest.py            # Appium `driver` fixture (web `page` EMAS)
├── config.py             # APP_PACKAGE/ACTIVITY, server, creds (env)
├── pages/
│   ├── base_screen.py    # BaseScreen: wait_visible / tap / type_into (web BasePage ekvivalenti)
│   └── login_screen.py   # LoginScreen page-object
├── test_login.py         # pilot: valid + wrong-password
└── requirements-mobile.txt
```

## Ma'lum cheklovlar / keyingi ishlar
- `no_reset=True` — ilova holati saqlanadi; test boshlanish holatini o'zi
  aniqlaydi (`open_login_form` allaqachon formadami/Профильдами tekshiradi).
- **Repeatability:** valid login o'tgach ilova LOGIN qilingan qoladi — keyingi
  run uchun LOGOUT oqimi kerak (hali yozilmagan).
- Kamera (Штрих-код skaner) real qurilmada ishlaydi, emulatorda cheklangan.
- `adb shell input text` Kirillni yozolmaydi; Appium `send_keys` UiAutomator2
  orqali yozadi (ASCII login/parol uchun muammo yo'q).
