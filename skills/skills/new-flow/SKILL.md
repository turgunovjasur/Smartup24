---
name: new-flow
description: Yangi flow funksiya yaratish (tests/smoke/flows/ papkasida). UI harakatlar ketma-ketligini flow sifatida ajratish kerak bo'lganda ishlatiladi.
allowed-tools: Read, Glob, Grep, Edit, Write
---

# Yangi Flow Funksiya Yaratish

Argument: `$ARGUMENTS` (flow nomi va qisqacha tavsif)

## Flow nima?

Flow — bu bir nechta testlarda qayta ishlatiladigan UI harakatlar ketma-ketligi.
Masalan: `authorization`, `navigate_to_menu`, `open_modal` va hokazo.

## Joylashuv

`tests/smoke/flows/flow_<nomi>.py`

## Shablon

```python
import allure
from playwright.sync_api import Page, expect


def <nomi>(page: Page, **kwargs) -> None:
    """
    <Qisqacha tavsif>.

    Args:
        page: Playwright page instance
        **kwargs: Qo'shimcha parametrlar (code, data va h.k.)
    """
    with allure.step("1 - <Qadam>"):
        page.locator("<selector>").click()

    with allure.step("2 - <Qadam>"):
        expect(page.locator("<selector>")).to_be_visible()
```

## Qoidalar

- Funksiya `Page` ni birinchi argument sifatida qabul qilsin
- Har bir muhim qadam `allure.step` bilan o'ralsin
- `expect()` bilan holatni tekshir, `assert` emas
- Flow faqat UI harakatlarni bajarsin — ma'lumot saqlash/o'qish test ichida qolsin
- Funksiya nomi `flow_` prefiksi emas, tavsifli ism bo'lsin: `authorization`, `create_room`

## Loyiha Xususiyatlari

### Order flowlarni qayta ishlatish
- Order testlari ko'p yoziladi; orderga tegishli takrorlanadigan harakatlar `tests/smoke/flows/flow_order/` ichidagi alohida flow funksiyalarga ajratilsin va yangi order case'larda shu flowlardan foydalanilsin.
- Order case'lari contract shartlariga bog'liq bo'lishi mumkin; contract yaratish flowlari `Типы оплат` kabi shartlarni parametr sifatida qabul qiladigan qilib loyihalansin.
- Biruni error xabarlari hamma joyda bir xil pattern bilan keladi; error kutish, text tekshirish va modal yopish umumiy flow/helper sifatida ajratilsin.
- Listlarda kerakli ustun/search yoqilmagan bo'lsa, grid setting orqali ustun va searchni yoqadigan reusable flow yozish mumkin.

## Ish tartibi

1. `$ARGUMENTS` ni o'qi — qanday flow kerak?
2. O'xshash mavjud flow larni ko'r (`tests/smoke/flows/`)
3. Yangi `flow_<nomi>.py` fayl yarat
4. Flow funksiyasini yoz
5. Qaysi testlarda ishlatish kerakligini ko'rsat
