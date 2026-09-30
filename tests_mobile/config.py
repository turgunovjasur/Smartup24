"""Mobil testlar sozlamalari — YAGONA joy (server, ilova, qurilma, userlar).

Hammasini env bilan almashtirish mumkin; default qiymatlar dev (sm24) uchun.
"""
import os

# --- Appium server / qurilma ---
APPIUM_SERVER = os.getenv("APPIUM_SERVER", "http://127.0.0.1:4723")
DEVICE_UDID = os.getenv("ANDROID_UDID") or None   # bir nechta telefon bo'lsa

# --- Sinaladigan ilova ---
APP_PACKAGE = "uz.greenwhite.smartup24"
APP_ACTIVITY = "uz.greenwhite.smartup24.MainActivity"

# --- Test oldidan ilovani Play Market'dan qayta o'rnatish ---
# INSTALL_APP=1 -> telefonda bor bo'lsa o'chirib, Play Market'dan o'rnatadi (yo'q bo'lsa
# shunchaki o'rnatadi); 0 yoki berilmagan -> telefondagi ilovaga tegmaydi.
INSTALL_APP = os.getenv("INSTALL_APP", "0").strip() == "1"
PLAY_INSTALL_TIMEOUT = 300   # sekund: yuklab olish + o'rnatish (4G'da sekin bo'lishi mumkin)
APP_LANGUAGE = "Ru"          # 1-ochilishdagi "Til tanlang": testlar ruscha UI'ga yozilgan

# Toza o'rnatilgan ilova PROD'ga ulanadi — o'rnatishdan keyin "Для разработчиков"
# orqali shu serverga o'tkaziladi (web testlar bilan bir xil TEST_ENV).
TEST_ENV = (os.getenv("TEST_ENV") or "dev").strip().lower()
SERVER_HOSTS = {"dev": "app2.greenwhite.uz/x24", "prod": "app.smartup24.com"}
APP_SERVER_HOST = SERVER_HOSTS.get(TEST_ENV, SERVER_HOSTS["dev"])

# --- Tayyor klient (dev sm24 da hamkorlik va tovarlari bor) ---
MOBILE_LOGIN = os.getenv("MOBILE_LOGIN", "sanobar@sm24")
MOBILE_PASSWORD = os.getenv("MOBILE_PASSWORD", "1")

# Tayyor klientning zakaz ma'lumotlari (test_order_smoke)
SMOKE_SUPPLIER = "Sanobar Distir"
SMOKE_CATEGORY = "Oziq-ovqat"
SMOKE_PRODUCT = "Saber Energy Drink Maximum Power"

# --- Web yaratgan userlar paroli (group_a run_*_user shu parol bilan yaratadi) ---
WEB_USER_PASSWORD = "1"
