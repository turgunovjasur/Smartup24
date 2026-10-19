# Smartup24 — S-05 Склады (Supplier) avtotestlari: bajarilgan ish (2026-10-14 … 10-18)

> Bu fayl boshqa chat/hamkasbga kontekst berish uchun. Test-case'ning to'liq matni alohida faylda:
> `docs/qa/test-cases/sbr/supplier/warehouse.md` (27 keys + avtotest holati jadvali) — ikkalasini birga yuboring.

## Kontekst
- Loyiha: Smartup24 (x24 ERP) UI avtotestlari. Stack: Python + Playwright + pytest + allure; mobil — Appium (Flutter ilova, Android Studio emulyatori).
- Muhit: faqat DEV (`app2.greenwhite.uz/x24`, kompaniya `sm24`).
- Manba: Team Lead test-case hujjati `sbr/supplier/warehouse.md` (27 keys).
- Qoidalar: test-case'da YO'Q tekshiruv qo'shilmaydi; test o'z ma'lumotini o'zi yaratadi (Alfa/Beta/Gamma/Epsilon — shartli nomlar), mavjud ma'lumotga tegilmaydi; ilova bag'i yashirilmaydi — test-case «Hozir» qatoridagi bag DEV'da tasdiqlansa `known_bug("SMAR24-…")` (warehouse_helpers.py, strict xfail; marker emas).

## Fayllar (repoda)
| Fayl | Nima |
|---|---|
| `tests/sbr/supplier/warehouse/warehouse_helpers.py` | barcha ombor web yordamchilari (yaratish, biriktirish/olib tashlash, «В наличие», regionlar) |
| `tests/sbr/supplier/warehouse/conftest.py` | web keyslar uchun umumiy seed (`alfa_seed`, bir martalik; `beta_seed` — Beta supplier + user + tovar + API orqali «Beta ombori») |
| `tests/sbr/supplier/warehouse/warehouse_api.py` | ombor endpointlari uchun kichik `requests` klienti (`WarehouseApi`, bitta user sessiyasi; har so'rov/javob Allure'ga) |
| `tests/sbr/supplier/warehouse/test_warehouse_api.py` | API keyslar: 1.5 (6 qism), 1.3 (2 qism), 2.1(f), 2.3, 3.2 |
| `tests/sbr/supplier/warehouse/test_warehouse_list.py` | §1 ro'yxat: 1.1, 1.4, 1.6 |
| `tests/sbr/supplier/warehouse/test_warehouse_form.py` | §2 forma: 2.1 a–e, 2.2 (web) |
| `tests/sbr/supplier/warehouse/test_warehouse_products.py` | §3 tovarlar: 3.1 (web) |
| `tests_mobile/tests/warehouse/test_warehouse_delete_e2e.py` | S-05.1.2 web+mobil E2E, 4 bosqich: web seed → mobil (oldin) → web o'chirish → mobil (keyin) |
| `tests_mobile/tests/warehouse/test_warehouse_catalog.py` | mobil katalog: 4.1, 2.2 (mobil), 4.2, 3.1 (mobil), 3.3, 4.3 |
| `tests_mobile/tests/warehouse/catalog_helpers.py`, `tests_mobile/tests/warehouse/conftest.py` | mobil katalog yordamchilari va seed (`S05_MOBILE_SEED`) |
| `docs/qa/test-cases/sbr/supplier/warehouse.md` | test-case nusxasi + avtotest holati jadvali |

## Keyslar holati (27 tadan; avtomatlashtiriladigan 23 tadan 15 tasi tayyor — 2026-10-18)
| Holat | Keyslar |
|---|---|
| ✅ To'liq tayyor (DEV) | 1.1; 1.2 (web+mobil E2E); 1.3 (API, xfail SMAR24-1059); 1.4; 1.5 (API, 6 qism: 5 xfail SMAR24-926/1061 + $detach yashil); 1.6; 2.1 (a/c/d ✅, b xfail SMAR24-1060, e xfail Team Lead savoli, f xfail SMAR24-1060); 2.2 (web+mobil); 2.3 (API, xfail SMAR24-1060); 3.1 (web+mobil); 3.2 (API, yashil); 3.3; 4.1; 4.2; 4.3 (xfail SMAR24-1063 — supplier ro'yxatda 2 marta) |
| ⛔ Team Lead qarori kerak | 3.4, 3.5, 3.6, 3.7, 3.8, 4.4, 4.5, E1 — aniq qoldiq qo'yish yo'li yo'q |
| ➖ Avtomatlashtirilmaydi | 5.1–5.3 (test-case: Avtotest = N), 3.9 (qaror: e'tibor berilmaydi) |

## Topilmalar (ilova xulqi, dalil bilan)
1. **S-05.1.2 / SMAR24-1059:** ombor o'chirilgach, faqat shu omborda bo'lgan tovar **web katalogda qoladi**, mobil katalogda yo'qoladi — test-case «Hozir: DW qayta qurilmaydi, boshqa o'quvchilar eskirgan qatorni ko'radi» ga mos.
2. **Web katalog ombor regionini filtrlamaydi**, mobil filtrlaydi — region filtri faqat mobil kanalda tekshiriladi.
3. **S-05.2.1(b) / SMAR24-1060:** takroriy kodda xom texnik xato (`Z:#z:sbr_supplier_warehouses dup_val_on_index code=tsh …`), «bunday kod bor» o'rniga → xfail.
4. **S-05.2.1(e):** ilova bir xil nomli 2-omborni **rad etadi** («Этот название уже используется»); test-case «ruxsat» kutadi va o'zi [taxmin] deb belgilagan → xfail, Team Lead qarori kutilmoqda.
5. **S-05.1.4:** test-case taxmin qilgan skalyar `warehouse_ids` xatosi **kuzatilmadi** — bitta ombor normal o'chadi.
6. **S-05.1.6:** moderator to'sig'i (SMAR24-1004) UI'da **ko'rinmadi** — «Склады», «Создать», «Изменить», «Товары» bor.
7. **S-05.3.1:** «Доступные» = **shu omborda bo'lmagan** tovarlar (taxmin tasdiqlandi); yangi biriktirilgan tovar «В наличие = Нет», miqdor ustuni yo'q.
8. Ombor «Регион» maydoni **multiselect** («2 выбрано»).
9. Avtomatlashtirilmagan: S-05.1.2 dagi «tovar so'rovi omborga ishora qilsa ORA-02292» — UI'da so'rov yaratish yo'li yo'q.
10. **API (2026-10-18, `requests`, faqat Content-Type + sessiya cookie):**
    - **S-05.1.5 / SMAR24-926/1061:** ombor egaligi tekshirilmaydi — Alfa sessiyasi «Beta ombori»ning edit:model'ini oladi, uni qayta nomlaydi, o'chiradi, unga o'z tovarini biriktiradi, o'z omborini `supplier_id` = Beta bilan Beta'ga o'tkazadi — hammasi HTTP 200 va effekt bor → 5 ta xfail.
    - **S-05.1.5 $detach va S-05.3.2:** server HTTP 200 (bo'sh body) qaytaradi, lekin begona tovarni **jim e'tiborsiz qoldiradi** (bog'lanish o'zgarmaydi) — xato xabari yo'q. User qarori: «rad» = holat o'zgarmagan → testlar yashil, status faqat Allure dalili. Team Lead'ga xabar berilsin.
    - **Bind ro'yxati (`warehouse_product_bind_list:table`) faqat CHAQIRUVCHI supplier tovarlarini ko'rsatadi:** Alfa «Beta ombori»ga biriktirgan Alfa tovarini Beta ko'rmaydi (Alfa ko'radi) — tekshiruvlar to'g'ri sessiya ko'rinishidan o'qiladi.
    - **S-05.1.3 / SMAR24-1059:** standart ombor (pcode SB:1) API orqali qayta nomlanadi va o'chiriladi (HTTP 200) → xfail.
    - **S-05.2.1(f) / SMAR24-1060:** mavjud bo'lmagan region_id → HTTP 500 xom «Z:#z:sbr_supplier_warehouse_regions parent key not found …» (test-case taxmini ORA-02291 emas, Z:#z:), ombor yaratilmaydi → xfail.
    - **S-05.2.3 / SMAR24-1060:** `edit$save` region_id kalitisiz → barcha regionlar o'chadi (edit:model region_id = []) → xfail.
    - Tekshirilmagan qismlar (DEV'da ma'lumot yo'q): 2.1(f) boshqa kompaniya regioni, 3.2 xizmat tovari.

## Yo'lda tuzatilgan umumiy muammolar (barcha bo'limlarga ta'sir)
- **Login:** DEV deploy'da parol maydoni «Введите пароль» → «Пароль»; `flows/flow_authorization.py` va `utils/base_api.py` ikkalasini qabul qiladi.
- **`utils/base_page.py`:** multi-select («Роли», «Торговые точки») server filtr javobini kutib tanlash; `save()` 2-klik loader ostida 60 s qotmaydi; tree-select paneli qayta ochish.
- **group_a (faqat ixtiyoriy parametrlar, eski xulq o'zgarmagan):** `run_supplier(extra_regions)`, `run_cooperation(supplier_name, client_name)` + «Запросы поставщиков» tab race himoyasi, `run_product(name)`, `run_product_linking` (aniq nom, bitta klik).
- **Mobil:** `screens/catalog_screen.py` (kategoriya bor/yo'q holatlari, soxta-PASS himoyasi, 60 s); `core/driver_factory.py` (`waitForIdleTimeout=0`, ilova tayyorligini 120 s kutish, `uiautomator2ServerLaunchTimeout` 90 s).
- **DEV sozlamasi:** admin «Клиенты» ro'yxatidagi qadalgan filtr shabloni (Ид клиента = 16791) olib tashlandi (user ruxsati bilan) — u barcha client testlarini yiqitardi.

## Muhit eslatmalari
- Emulyator: Android Studio `Medium_Phone_API_37.0` (`ANDROID_SDK_ROOT=%LOCALAPPDATA%\Android\Sdk` bilan yoqiladi); Appium alohida oynada.
- **Har mobil run'da `INSTALL_APP=0`** (`.env` da 1 — ilovani o'chirib Play'dan qayta o'rnatadi).
- Kompyuter xotirasi kam (1–3 GB bo'sh) → emulyator sekin; web qismi `HEADLESS=1` bilan.
- Qoldiqni ko'rish: Модератор → Поставщики → supplier → Просмотр → Настройки → Основное → «Кому показывать остатки» → mijoz → mobil katalogda «N шт». Zakazdan keyin: supplier → Товары → «Отправить обновление остатков в интеграцию», keyin qayta tekshirish.

## Team Lead'ga ochiq savollar
1. Qoldiq keyslarini (3.4, 3.5, 3.7, 3.8, 4.4) test-case raqamlari o'rniga **1 000 000** bilan tekshirsak bo'ladimi? (UI faqat 1 000 000 / 0 qo'yadi; masalan 3.4: qoldiq 1 000 000, buyurtma 1 000 001 → «Нет в наличии».)
2. 3.5 (korobka), 3.6 (manfiy), E1 (Dalion mock) uchun aniq qoldiq qanday qo'yiladi — test DB, integratsiya API yoki mock?
3. S-05.2.1(e): ombor nomi unikal bo'lishi kerakmi?

## Commit holati
Hech narsa commit qilinmagan (`main` da diskda). Commit'dan oldin: setup + group_a regressiya run'i (`base_page` o'zgargani uchun) va code review. Begona fayllar commit'ga kirmaydi: `.mcp.json`, `tests/test_document/test_all_document_runner.py` (unda `test_all_document_runner` har testni 2 marta yuguradi — alohida muammo).
