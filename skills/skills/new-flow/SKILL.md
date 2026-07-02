---
name: new-flow
description: Yangi flow funksiya yaratish (flows/ papkasida). Bir nechta testda qayta ishlatiladigan UI harakatlar ketma-ketligini flow sifatida ajratish kerak bo'lganda ishlatiladi.
allowed-tools: Read, Glob, Grep, Edit, Write
---

# Yangi Flow Funksiya Yaratish (Smartup24)

Argument: `$ARGUMENTS` (flow nomi va qisqacha tavsif)

## Flow nima?

Flow — bir nechta testlarda qayta ishlatiladigan UI harakatlar ketma-ketligi.
Masalan: `authorization`, `logout`, `flow_navigate`.

## Joylashuv

`flows/flow_<nomi>.py`

Mavjud flowlar:
- `flows/flow_authorization.py` — `authorization(page, email, password)`, `logout(page)`
- `flows/flow_navbar.py` — `flow_navigate(page, tab, name)`, `flow_search(page, name)`, `flow_menu(page)`

## Shablon

```python
from playwright.sync_api import Page, expect


def <nomi>(page: Page, ...) -> None:
    """<Qisqacha tavsif>."""
    page.get_by_role("button", name="...").click()
    expect(page.locator("...")).to_be_visible()
```

## Qoidalar

- Funksiya `Page` ni birinchi argument sifatida qabul qilsin.
- Holatni `expect()` bilan tekshir, Python `assert` emas.
- **Forma maydonlari bilan ishlashni flow ichiga yozma** — u `BasePage` (utils/base_page.py) ishi. Flow faqat navigatsiya/ketma-ketlik (tab bosish, menyu, login) uchun.
- Faqat **bir nechta testda takrorlanadigan** harakatni flowga ajrat; bitta testga xos harakat test ichida qolsin. 1 qatorlik wrapper flow yozma.
- Barqaror locator ishlat: `get_by_role("button"/"link"/"menuitem", name=...)` yoki `smtid`. Dinamik `ng.formN.*` / `#cdk-drop-list-N` ISHLATMA.
- Teardownda ishlaydigan flow (masalan `logout`) `try/except` bilan himoyalansin — sahifa yopilgan/xato holatda bo'lsa ham testni buzmasin.

## Loyiha xususiyatlari

- **Navigatsiya**: `flow_navigate(page, tab, name)` navbar tab tugmasini (`Модератор`/`Поставщик`/`Клиент`) bosib, ochilgan menyudan `menuitem` ni tanlaydi. Товары/справочnik ro'yxatlariga shu orqali o't.
- **Sub-nav (list ichidagi bo'limlar)**: `Производители`, `Характеристика товаров` kabi bo'limlar `app-form-stack-widget` ichida `link` sifatida — `page.get_by_role("link", name=...)` bilan bosiladi (odatda test ichida, alohida flow shart emas).
- **Login**: `authorization(page)` login qilib navbar "Модератор" ko'ringunicha kutadi; `run_` funksiyalari login qilinganini kutadi, o'zi auth qilmaydi.

## Ish tartibi

1. `$ARGUMENTS` ni o'qi — qanday flow kerak, u bir nechta testda ishlatiladimi?
2. O'xshash mavjud flowni ko'r (`flows/`)
3. Yangi `flow_<nomi>.py` yarat yoki mavjud faylga qo'sh
4. Flow funksiyasini yoz
5. Qaysi testlarda ishlatilishini ko'rsat
