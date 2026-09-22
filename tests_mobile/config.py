"""Mobil (Android/Appium) testlari uchun markaziy sozlamalar.

Faqat KONSTANTALAR. Maxfiy qiymatlar (login/parol) env orqali beriladi —
koda yozilmaydi (web flow_authorization bilan bir xil falsafada).
"""
import os

# --- Appium server ---
APPIUM_SERVER = os.getenv("APPIUM_SERVER", "http://127.0.0.1:4723")

# --- Sinaladigan ilova ---
APP_PACKAGE = "uz.greenwhite.smartup24"
APP_ACTIVITY = "uz.greenwhite.smartup24.MainActivity"

# --- Qurilma ---
# Bitta telefon ulangan bo'lsa UDID shart emas (None). Bir nechta bo'lsa
# `adb devices` dagi seriyani ANDROID_UDID env orqali ber.
DEVICE_UDID = os.getenv("ANDROID_UDID") or None

# --- Test login ma'lumotlari (mobil ilova; web admin'dan FARQLI bo'lishi mumkin) ---
# DIQQAT: koda yozilmaydi — env orqali beriladi:
#   $env:MOBILE_LOGIN="...";  $env:MOBILE_PASSWORD="..."
MOBILE_LOGIN = os.getenv("MOBILE_LOGIN", "")
MOBILE_PASSWORD = os.getenv("MOBILE_PASSWORD", "")
