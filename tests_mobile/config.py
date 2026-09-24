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

# --- Tayyor klient (dev sm24 da hamkorlik va tovarlari bor) ---
MOBILE_LOGIN = os.getenv("MOBILE_LOGIN", "sanobar@sm24")
MOBILE_PASSWORD = os.getenv("MOBILE_PASSWORD", "1")

# Tayyor klientning zakaz ma'lumotlari (test_order_smoke)
SMOKE_SUPPLIER = "Sanobar Distir"
SMOKE_CATEGORY = "Oziq-ovqat"
SMOKE_PRODUCT = "Saber Energy Drink Maximum Power"

# --- Web yaratgan userlar paroli (group_a run_*_user shu parol bilan yaratadi) ---
WEB_USER_PASSWORD = "1"
