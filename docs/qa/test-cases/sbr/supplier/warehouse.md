# S-05 Склады (Supplier)

> Manba: Team Lead test-case hujjati (backend repo `smartup24`, `claude/qa-test-cases` tarmog'i,
> `docs/qa/test-cases/sbr/supplier/warehouse.md`). Bu nusxa avtotestlar uchun 2026-10-15 da user
> chatga tashlagan matndan saqlandi. Avtotest holati — oxirgi bo'limda.

Formalar: sbr/supplier/warehouse_list (Ui_Sb242), sbr/supplier/warehouse+add|+edit (Ui_Sb243 — regionlar shu formada multiselect), sbr/supplier/warehouse_product_bind_list (Ui_Sb244 — «Прикрепленные товары», tablar «Прикрепленные» / «Доступные»), warehouse_audit_details (Ui_Sb257). Alohida «sklad regionlari» formasi yo'q. Omborda status yo'q — faqat o'chirish. Tovar miqdori yetkazib beruvchi UI'sida ko'rsatilmaydi va tahrirlanmaydi: faqat product_listdagi «Изменить наличие» (Y → 1 000 000, N → 0), buyurtma bo'yicha yechish / qaytarish va integratsiyalar.

Manba paketlar: Sbr_Api.Supplier_Warehouse_Save / _Delete / _Add_Product / _Remove_Product / _Regions_Save / Warehouse_Product_Update / Warehouse_Balance_Update / Charge_Warehouse_Product_Balance / Return_Warehouse_Product_Balance / Gen_Dw_Sptp_*, Sbr_Watcher.On_Supplier_Add (standart ombor «Склад по умолчанию», pcode SB:1), Sbd_Api.Deal_Change_Status (yechish / qaytarish), Sbr_Pref.Is_Stock_Visible, Sbe_Product (region filtri), Ui_Sb14, Sbe_Dalion, Sbe_Regos_Supplier, Sbe_Smx, Sbe_Sd.

Holat: ok (tasdiqlangan 07.10.2026)

## Ta'sir xaritasi

| Sozlama / harakat | Kimga ta'sir | Qayerda ko'rinadi |
|---|---|---|
| Tovar omborga biriktirilgan va avail = Y (kamida bitta omborda) | Mijoz | katalog (DW) — avail = N yoki biriktirilmagan tovar katalogda yo'q |
| Ombor regionlari | Mijoz | katalog filtri: tovar faqat mijoz regionidagi (yoki regionsiz) omborda avail = Y bo'lsa ko'rinadi; buyurtma va tarifga ta'sir qilmaydi |
| Ombor qoldig'i (quantity, barcha omborlar yig'indisi) | Mijoz | buyurtma statusi New+ ga o'tganda yechiladi, yetmasa xato; stock_quantity faqat SB:stock_visible_personsdagi mijozga |
| «Изменить наличие» (product_list) | Mijoz | Y → barcha omborlarda 1 000 000, N → 0 — integratsiya ma'lumotini ustidan yozadi |
| Integratsiya (Dalion / Regos / SMX / SalesDoctor) | Mijoz | qoldiq qayta yoziladi (javobda yo'q tovar → N / 0), Regos — faqat kelgan qatorlar |
| Ombor o'chirildi | Mijoz | tovar-ombor va regionlar cascade o'chadi; DW qayta qurilmaydi |

## Umumiy test ma'lumotlari (README §4a bo'yicha)

- Yetkazib beruvchi «Alfa», boshqa yetkazib beruvchi «Beta»; mijoz «Gamma» (Alfa bilan kelishuvli, o'zi Yunusobod tumanida, nuqtalari «Gamma-1» Yunusobod, «Gamma-2» Chilonzor); mijoz «Epsilon» (Samarqand viloyati).
- Alfa omborlari: «Склад по умолчанию» (standart, SB:1, regionsiz), «Toshkent ombori» (kod TSH, region Toshkent shahri), «Samarqand ombori» (kod SAM, region Samarqand viloyati).
- Tovarlar: «Sut 1L» (10 000, dona), «Non» (2 000), «Suv 6×1.5» (korobka, box_quant 6); narxlari va portfoliosi bor.
- Qoldiqlar (boshlang'ich): «Sut 1L» — Toshkent 100 (Y), Samarqand 50 (Y); «Non» — faqat Toshkent 20 (Y); «Suv 6×1.5» — Toshkent 12 (Y).
- Foydalanuvchilar: Alfa-admin, Gamma-user-1, Epsilon-user-1, Moderator.

## Model (koddan)

- `sbr_supplier_warehouses`: Название (500, unikal emas), Код (50, yetkazib beruvchi ichida unikal, registr va chetki bo'shliqsiz — _u2; bo'sh bo'lishi mumkin), pcode SB:1 = standart. Status yo'q.
- `sbr_supplier_warehouse_products`: PK (supplier, warehouse, product); avail Y/N; quantity (number(20,6)); _c2: avail = Y bo'lsa quantity > 0 (avail = N da manfiy ham mumkin). Biriktirish — Insert_Try (avail = N, 0).
- `sbr_supplier_warehouse_regions`: PK (warehouse, region); ombor bilan cascade. Regions_Save: yuborilmaganlar o'chiriladi, region_id umuman kelmasa — hammasi.
- `sbr_supplier_product_requests.warehouse_id` → cascade'siz FK (o'chirish ORA-02292).
- Katalog (DW): tovar kamida bitta omborda avail = Y + narx + faol portfolio + faol tovar + faol xarakteristika / narx turi + promo emas + kategoriya + LOB. Qayta quriladi: Remove_Product, Warehouse_Product_Update, Warehouse_Balance_Updateda; ombor o'chirilganda emas.
- Region filtri (Sbe_Product.Build_Product_List, Ui_Sb14): tovar ko'rinadi, agar (a) mijoz regionlaridan biridagi omborda avail = Y, yoki (b) regionsiz omborda avail = Y va yetkazib beruvchida kamida bitta regionli ombor bor, yoki (c) yetkazib beruvchining hech bir omborida region yo'q — eski filtr (yetkazib beruvchi sbr_person_regions). Mijoz regionlari — mijoz va nuqtalari regionlari ajdodlari bilan (shahar darajasidagi ombor tumandagi mijozni qamraydi, teskarisi yo'q).
- Yechish (Deal_Change_Status, i_Skip_Charge = N): {Approval, Financing, Draft, Suspended} → {New, Executing, Waiting, Shipped, Delivered, Completed} o'tishida Charge_Deal_Quantity — har tovar: barcha omborlar quantity yig'indisi (avail'dan qat'i nazar, manfiylar ham) < sold_quant → «Нет в наличии, название товара = $1, кол-во заказа = $2, кол-во на складе = $3»; aks holda warehouse_id tartibida quantity > 0 omborlardan yechiladi; avail = Y qoldiq ≥ bo'sag'a (korobka bo'lsa box_quant, aks holda 1). Qaytarish: {New…Completed} → {Approval, Draft, Cancelled} — butun miqdor warehouse_id bo'yicha birinchi omborga. Checkout (Place_Deal) Skip_Charge = Y — yechish birinchi New+ o'tishda. Savat va checkout qoldiq / avail / regionni tekshirmaydi. Dalion va SMX buyurtmalari Skip_Charge = Y.
- stock_quantity = greatest(0, sum(quantity)) — faqat Sbr_Pref.Is_Stock_Visible = Y (S-18.1.5).

## 1. Ro'yxat (warehouse_list, Ui_Sb242)

```
S-05.1.1  Ro'yxat tarkibi                                                            [crud]
Kanal:      web
Tekshirish: Alfa-admin → Склады
Kutilgan:   3 qator: Название, Код, Регионы (listagg), Количество товаров; yashirin: ИД склада, Создал, …; standart omborda «Удалить» o'chiq; Beta omborlari yo'q.
            Status ustuni yo'q (omborda status yo'q)
Avtotest:   Y
Manba:      Ui_Sb242.Query (122-177)

S-05.1.2  O'chirish — tovarlar va regionlar cascade, DW qayta qurilmaydi              [crud][effect][bug-candidate]
Kanal:      web+mobile
Shart:      «Samarqand ombori»da «Sut 1L» 50 (Y), boshqa omborda yo'q tovar «Qatiq» 10 (Y); Epsilon (Samarqand) katalogda «Sut 1L» va «Qatiq»ni ko'radi;
            tovar so'rovi (sbr_supplier_product_requests) shu omborga ishora qiladi
Tekshirish: Alfa-admin → «Samarqand ombori» → Удалить → «Вы действительно хотите удалить Samarqand ombori?» → Да; Epsilon-user-1: c:exp_product_list;
            Gamma-user-1: c:exp_product_list
Kutilgan:   ombor, uning tovar-qatorlari va regionlari o'chadi; «Qatiq» katalogdan yo'qoladi (hech qayerda avail Y yo'q); Epsilon «Sut 1L»ni ko'rmaydi
            (regionida ombor yo'q); so'rov ishora qilsa — tushunarli xato
Hozir:      DW qayta qurilmaydi — «Qatiq»ning DW qatori qoladi (mobil ro'yxat region/avail filtri bilan yashiradi, lekin boshqa o'quvchilar eskirgan
            qatorni ko'rishi mumkin); so'rov ishorasi → xom ORA-02292; Dalion sbe_binds bog'lanishi yetim qoladi
Avtotest:   Y
Manba:      Sbr_Api.Supplier_Warehouse_Delete (848-857)

S-05.1.3  Standart ombor himoyasi faqat UI'da                                         [negative][bug-candidate]
Kanal:      web (API)
Tekshirish: $delete warehouse_ids = [«Склад по умолчанию»]; warehouse+edit$save name = «Boshqa» (UI'da pcode bor nom faqat o'qish)
Kutilgan:   rad (pcode)
Hozir:      o'chadi / qayta nomlanadi — API pcode'ni tekshirmaydi; standart ombor o'chsa yangi tovarlar hech qanday omborga biriktirilmaydi
Avtotest:   Y
Manba:      Sbr_Api.Supplier_Warehouse_Delete, Sbr_Watcher (595-613)

S-05.1.4  Bitta qatorni o'chirish — warehouse_ids skalyar                              [crud][bug-candidate][taxmin]
Kanal:      web
Tekshirish: qator menyusidan «Удалить» (bitta ombor)
Kutilgan:   o'chadi
Hozir:      [taxmin] Angular warehouse_ids'ni skalyar yuboradi (warehouse-list.ts:207), server r_Array_Number kutadi — stendda tekshirish (xato yoki
            Biruni skalyarni massivga o'giradimi)
Avtotest:   Y
Manba:      smartup24-angular warehouse-list.ts:207, Ui_Sb242.Del (186-200)

S-05.1.5  Egalik                                                                      [access][negative][bug-candidate]
Kanal:      web (API)
Shart:      Alfa-admin; «Beta ombori» id'si ma'lum
Tekshirish: $delete «Beta ombori»; warehouse+edit:model / $save «Beta ombori»; $save «Toshkent ombori» supplier_id = Beta; bind_list$attach /
            $detach «Beta ombori» bilan
Kutilgan:   hammasi rad
Hozir:      hammasi o'tadi — ombor yetkazib beruvchiga tegishliligi tekshirilmaydi; Edit supplier_id'ni so'rovdan oladi (omborni boshqa yetkazib
            beruvchiga o'tkazish); Add / Edit / Detach'da Check_Moderator_Access ham yo'q (Jira: SMAR24-926 doirasida)
Avtotest:   Y
Manba:      Ui_Sb243.Add / Edit (73-114), Ui_Sb242.Del, Ui_Sb244.Detach

S-05.1.6  Moderator kirishi                                                           [access][bug-candidate]
Kanal:      web
Tekshirish: Moderator → supplier_view(Alfa) → Склады
Kutilgan:   ro'yxat; «Создать», «Изменить», «Товары» (onboarding — SMAR24-1004 qoidasi)
Hozir:      SB:M:1 da warehouse_list'da faqat * va delete; supplier_view'dagi warehouse tab ('H') rolda ko'rsatilmagan — [taxmin] 'H' turi
            moderatorga avtomatik ochiladimi, stendda tekshirish. Qaror (07.10.2026): moderator ombor yaratishi / tahrirlashi kerak (Jira: SMAR24-1004, izoh 07.10.2026)
Avtotest:   Y
Manba:      setup/role_settings.sql (1358-1367, 1252-1254)
```

## 2. Forma (warehouse+add|+edit, Ui_Sb243)

```
S-05.2.1  Yaratish — maydonlar va tekshiruvlar                                        [crud][negative][bug-candidate]
Kanal:      web (UI + API)
Tekshirish: (a) Название bo'sh; (b) Код «tsh» (bor: TSH); (c) Код « TSH »; (d) Название 501 belgi; (e) ikki ombor bir xil nom bilan; (f) API: region_id =
            mavjud bo'lmagan / Beta kompaniyasi regioni
Kutilgan:   (a) UI maydon qizil (matn yo'q); (b) «bunday kod bor»; (c) bo'shliqlar kesiladi; (d) UI 500 — to'g'ri; (e) ruxsat (nom unikal emas — [taxmin]
            kutilganmi?); (f) tushunarli xato
Hozir:      (b) _u2 xom ORA-00001; (c) _u2 funksional indeks trim qiladi — saqlanadi, lekin kod bo'shliq bilan yoziladi [taxmin]; (f) xom ORA-02291.
            Supplier_Warehouse_Save biznes-tekshiruvsiz
Avtotest:   Y
Manba:      Sbr_Api.Supplier_Warehouse_Save (842-846), sbr_supplier_warehouses_u2

S-05.2.2  Regionlar — multiselect, daraxt                                             [crud][effect]
Kanal:      web+mobile
Shart:      «Toshkent ombori» regioni Toshkent shahri; Gamma Yunusobod tumanida (shahar ichida)
Tekshirish: Alfa-admin → Изменить → Регион daraxtida Toshkent shahri + Samarqand viloyati → Сохранить → qayta ochish; keyin hamma regionni olib tashlab Сохранить
Kutilgan:   ikkala region saqlanadi, ro'yxatda «Регионы» ustunida ikkalasi; Gamma (tuman) shahar darajasidagi ombor bilan qamraladi; regionlar olib
            tashlansa ombor «regionsiz» bo'ladi (S-05.4.2 b). Nofaol region daraxtda ko'rinmaydi — saqlangan nofaol region [taxmin] saqlashda yo'qolishi mumkin
Avtotest:   Y
Manba:      Sbr_Api.Supplier_Warehouse_Regions_Save (897-919), Ui_Sb243.Add_Model (faqat faol regionlar)

S-05.2.3  region_id kaliti umuman yuborilmasa — hamma region o'chadi                   [crud][negative][bug-candidate]
Kanal:      web (API)
Shart:      «Toshkent ombori» 2 region bilan
Tekshirish: warehouse+edit$save name = «Toshkent ombori 2», region_id kalitisiz
Kutilgan:   yuborilmagan kalit — regionlar o'zgarmaydi (S-12 / M-06 dagi «absent keeps» qoidasi)
Hozir:      Regions_Save(null) — barcha regionlar o'chiriladi; integratsiya yoki eski front nomni o'zgartirsa ombor regionsiz qoladi
Avtotest:   Y
Manba:      Sbr_Api.Supplier_Warehouse_Regions_Save
```

## 3. Tovarlarni biriktirish (warehouse_product_bind_list, Ui_Sb244) va qoldiq

```
S-05.3.1  «Прикрепленные» / «Доступные», biriktirish va ochirish                       [crud][effect]
Kanal:      web+mobile
Shart:      «Toshkent ombori»: Sut, Non, Suv; «Qatiq» hech qanday omborda emas (narxi, portfoliosi bor)
Tekshirish: Alfa-admin → «Toshkent ombori» → Товары → Доступные → «Qatiq» → Прикрепить → «Хотите прикрепить Qatiq?» → Да; Gamma-user-1: c:exp_product_list;
            keyin Прикрепленные → «Non» → Открепить → Да; Gamma: c:exp_product_list
Kutilgan:   «Qatiq» biriktiriladi avail = N, 0 bilan — katalogda hali ko'rinmaydi (nalichie qo'yilmaguncha, S-05.3.3); ustunlar Штрих-коды, Название,
            Статус, «В наличие» (Да/Нет), miqdor ustuni yo'q; «Non» ochirilgach katalogdan yo'qoladi (boshqa omborda yo'q), DW qayta quriladi.
            «Доступные» — faqat hech qanday omborda bo'lmagan tovarlar emas, shu omborda bo'lmaganlar [taxmin — Query mantig'ini stendda tekshirish];
            xizmat tovarlari ro'yxatda yo'q
Avtotest:   Y
Manba:      Sbr_Api.Supplier_Warehouse_Add_Product (859-874, Insert_Try N/0), Remove_Product (876-895)

S-05.3.2  Boshqa yetkazib beruvchi tovarini / xizmatni biriktirish                     [access][negative][bug-candidate]
Kanal:      web (API)
Tekshirish: $attach warehouse_id = «Toshkent ombori», product_id = Beta tovari; = «Yetkazib berish» (xizmat)
Kutilgan:   rad
Hozir:      biriktiriladi — tovar yetkazib beruvchiniki ekani tekshirilmaydi
Avtotest:   Y
Manba:      Sbr_Api.Supplier_Warehouse_Add_Product

S-05.3.3  «Изменить наличие» — fiktiv 1 000 000 va integratsiya ma'lumotini ustidan yozish  [effect]
Kanal:      web+mobile
Shart:      «Sut 1L» Toshkent 100, Samarqand 50 (Dalion'dan kelgan); «Qatiq» Toshkent N/0
Tekshirish: Alfa-admin → Товары (product_list) → «Qatiq» → Изменить наличие → Да; Gamma: c:exp_product_list; keyin «Sut 1L» → Изменить наличие → Нет; → Да
Kutilgan:   «Qatiq» katalogda paydo bo'ladi; «Sut 1L» Нет → katalogdan yo'qoladi, Да → qaytadi. Qaror (07.10.2026): fiktiv 1 000 000 va integratsiya qoldig'ini ustidan
            yozish shunday qoladi (keyingi sinxronizatsiya tiklaydi)
Hozir:      Да → barcha omborlarda quantity = 1 000 000, Нет → 0: Dalion'dan kelgan 100 / 50 yo'qoladi, keyingi sinxronizatsiyagacha (10 daqiqa)
            stock_quantity 2 000 000 ko'rinadi, yechish cheklanmaydi
Avtotest:   Y
Manba:      Ui_Sb65.Change_Avail (product_list.pkb:150-172), Sbr_Api.Warehouse_Product_Update (611-641)

S-05.3.4  Yechish — qoldiq yetmasa buyurtma statusi o'zgarmaydi                         [effect][boundary][state]
Kanal:      web+mobile
Shart:      «Non» Toshkent 20 (Y); Gamma buyurtmasi «Non» × 25 (checkout o'tdi — savat qoldiqni tekshirmaydi)
Tekshirish: Alfa-admin buyurtmani New qiladi (yoki Draft → New birinchi o'tish); keyin × 20 bilan
Kutilgan:   25: «Нет в наличии, название товара = Non, кол-во заказа = 25, кол-во на складе = 20», status o'zgarmaydi; 20: o'tadi, Toshkent 0, avail = N,
            «Non» katalogdan yo'qoladi
Avtotest:   Y
Manba:      Sbd_Api.Deal_Change_Status (4029-4055), Charge_Warehouse_Product_Balance (922-994)

S-05.3.5  Yechish bir nechta ombordan — warehouse_id tartibida; bo'sag'a korobka bo'yicha  [effect][boundary]
Kanal:      web
Shart:      «Sut 1L» Toshkent 100, Samarqand 50; «Suv 6×1.5» Toshkent 12 (box_quant 6)
Tekshirish: Gamma buyurtmasi «Sut 1L» × 120 → New; «Suv» × 8 (korobkalab sotiladi) → New
Kutilgan:   Sut: Toshkent 100 → 0 (avail = N), Samarqand 50 → 30 (Y) — mijoz regioni emas, warehouse_id tartibi; Suv: 12 → 4 < 6 (box_quant) → avail = N,
            katalogdan yo'qoladi, garchi 4 dona bor
Avtotest:   Y
Manba:      Charge_Warehouse_Product_Balance (bo'sag'a: box_quant yoki 1)

S-05.3.6  Yig'indi avail = N va manfiy qoldiqlarni ham sanaydi                           [effect][boundary]
Kanal:      web
Shart:      «Sut 1L» Toshkent 30 (N, Alfa «Изменить наличие» Нет qilgan... yoki Regos manfiy −20 yozgan), Samarqand 50 (Y)
Tekshirish: Gamma buyurtmasi «Sut 1L» × 70 → New; manfiy holatda × 40
Kutilgan:   Qaror (07.10.2026): avail = N ombor qoldiqlari faqat ma'lumot uchun saqlanadi va 10 daqiqa – 24 soat oralig'ida yangilanib turadi; hozirgi hisob
            (yig'indi avail'siz, manfiy bilan) kutilgan, aniq ombor hisobi hozircha kerak emas
Hozir:      30 + 50 = 80 ≥ 70 → o'tadi, Toshkent'dan yashirin 30 yechiladi; manfiy: −20 + 50 = 30 < 40 → rad (Regos manfiyi yig'indini kamaytiradi)
Avtotest:   Y
Manba:      Charge_Warehouse_Product_Balance (sum avail'siz)

S-05.3.7  Qaytarish — birinchi omborga                                                   [effect][state][bug-candidate]
Kanal:      web
Shart:      S-05.3.5 dan keyin (Toshkent 0, Samarqand 30)
Tekshirish: Alfa-admin buyurtmani Cancelled qiladi
Kutilgan:   Qaror (07.10.2026): Smartup24'da ombor hisobi yuritilmaydi — birinchi omborga qaytish kutilgan; omborsiz tovarda bekor qilish bloklanmasligi kerak
            (NO_DATA_FOUND qismi bug-candidate bo'lib qoladi)
Hozir:      butun 120 birinchi omborga (warehouse_id bo'yicha — Toshkent): Toshkent 120, Samarqand 30; tovar hech qanday omborga biriktirilmagan bo'lsa
            select into → NO_DATA_FOUND, bekor qilish bloklanadi
Avtotest:   Y
Manba:      Return_Warehouse_Product_Balance (996-1046)

S-05.3.8  Suspended orqali qayta yechish                                                  [effect][state][bug-candidate][taxmin]
Kanal:      web
Shart:      Gamma buyurtmasi «Non» × 10 New (yechilgan: 20 → 10)
Tekshirish: New → Suspended → Executing (agar o'tishlar ruxsat etilgan bo'lsa); Cancelled → New
Kutilgan:   Suspended qaytarmaydi, Executing qayta yechmaydi (jami bir marta); Cancelled → New qayta yechadi
Hozir:      [taxmin] kod bo'yicha: New → Suspended hech narsa qaytarmaydi, Suspended → Executing yana yechadi (10 → 0, ikki marta); Cancelled → New
            yechmaydi (Cancelled manba to'plamida yo'q). Qaysi o'tishlar UI'da ruxsat — stendda
Avtotest:   Y
Manba:      Sbd_Api.Deal_Change_Status (4031-4055 to'plamlari)

S-05.3.9  Parallel ikki buyurtma bitta qoldiqqa                                           [concurrency]
Shart:      «Non» 20; ikki buyurtma × 15 bir vaqtda New
Kutilgan:   bittasi rad
Hozir:      yig'indi qulfsiz o'qiladi, Update_One o'qilgan qiymatdan absolyut yozadi — ikkalasi o'tishi (oversell) yoki yangilanish yo'qolishi mumkin.
            Qaror (07.10.2026): S-07.6.1 kabi e'tibor berilmaydi
Avtotest:   QA hal qiladi
Manba:      Charge_Warehouse_Product_Balance
```

## 4. Ta'sir: mijoz katalogi, region, qoldiq ko'rinishi

```
S-05.4.1  Katalogda ko'rinish — avail Y kamida bitta omborda                             [effect]
Kanal:      mobile
Shart:      «Sut 1L» Toshkent Y / Samarqand Y; «Non» Toshkent Y; «Qatiq» Toshkent N
Tekshirish: Gamma-user-1 (Yunusobod): c:exp_product_list (Alfa)
Kutilgan:   Sut, Non — bor; Qatiq — yo'q
Avtotest:   Y
Manba:      Sbr_Api.Gen_Dw_Sptp_* (avail = 'Y')

S-05.4.2  Ombor regionlari — mijoz regioni bo'yicha filtr                                  [effect][boundary]
Kanal:      mobile
Shart:      «Toshkent ombori» (Toshkent shahri): Non Y; «Samarqand ombori» (Samarqand): Sut Y (Toshkentda Sut N); «Склад по умолчанию» (regionsiz): Qatiq Y
Tekshirish: Gamma (Yunusobod → Toshkent shahri ichida): c:exp_product_list; Epsilon (Samarqand): c:exp_product_list; keyin Alfa barcha omborlardan
            regionlarni olib tashlaydi → ikkalasi
Kutilgan:   Gamma: Non (a — shahar darajasidagi ombor tumanni qamraydi), Qatiq (b — regionsiz ombor, yetkazib beruvchida regionli ombor bor), Sut yo'q;
            Epsilon: Sut, Qatiq, Non yo'q; regionlar olib tashlangach (c): eski filtr — yetkazib beruvchi sbr_person_regions bo'yicha, hamma tovar.
            Region buyurtma, tarif va c:exp_product_supplier_list'ga ta'sir qilmaydi
Avtotest:   Y
Manba:      Sbe_Product.Build_Product_List (761-804), Sbr_Util.Get_Client_Regions (2245-2283)

S-05.4.3  c:exp_product_supplier_list — regionsiz va dublikat                               [effect][bug-candidate]
Kanal:      mobile
Shart:      «Sut 1L» Toshkent Y va Samarqand Y
Tekshirish: Gamma-user-1: c:exp_product_supplier_list («Sut 1L»)
Kutilgan:   Alfa bir marta; ombor regioni hisobga olinadi (katalog bilan bir xil)
Hozir:      Alfa ikki marta (ombor qatorlari bilan join, distinct yo'q); ombor regioni filtrlanmaydi — katalogda ko'rinmagan tovar yetkazib beruvchisi bu
            yerda bor
Avtotest:   Y
Manba:      Sbe_Cproduct.Exp_Product_Supplier_List (355-360)

S-05.4.4  stock_quantity — faqat ruxsat etilgan mijozga, barcha omborlar yig'indisi          [effect][access]
Kanal:      mobile
Shart:      «Sut 1L» Toshkent 100, Samarqand 50; Alfa SB:stock_visible_persons = [Gamma]
Tekshirish: Gamma-user-1 va Epsilon-user-1: c:exp_product_list, c:exp_product_info, c:exp_basket_headers_info
Kutilgan:   Gamma: stock_quantity = 150 (regiondan qat'i nazar, bazaviy birlikda); Epsilon: kalit yo'q (0 emas); ro'yxat bo'sh bo'lsa hech kimga
Bog'liq:    S-18.1.5
Avtotest:   Y
Manba:      Sbr_Pref.Is_Stock_Visible (359-398)

S-05.4.5  Savat va checkout qoldiqni tekshirmaydi                                            [effect][boundary]
Kanal:      mobile
Shart:      «Non» 20
Tekshirish: Gamma: c:imp_basket_add_product («Non» × 100) → checkout
Kutilgan:   savatga qo'shiladi, checkout o'tadi (Draft / Approval, Skip_Charge = Y); xato faqat New+ ga o'tishda (S-05.3.4). Mijoz stock_quantity'ni
            ko'rsa ilova o'zi cheklaydi (MOB-C) — hujjatlashtirilgan xulq. Qaror (07.10.2026): checkout'da tekshiruv kerak emas, shunday qoladi
Avtotest:   Y
Manba:      Sbd_Api.Place_Deal (3500-3520)
```

## 5. Integratsiya [ext]

```
S-05.5.1  Dalion — har 10 daqiqada qayta yozish                                              [ext]
Shart:      Alfa Dalion bilan; ombor kodi TSH 1C omboriga sbe_binds orqali bog'langan («Сверить коды»); Alfa qo'lda «Qatiq» Y qilgan (1 000 000), 1C javobida Qatiq yo'q
Kutilgan:   «Sut 1L» = Количество − Зарезервировано (manfiy → 0), avail bo'sag'a bo'yicha; javobda yo'q «Qatiq» → N / 0 (qo'lda qo'yilgan yo'qoladi);
            bo'sh javob — hech narsa o'zgarmaydi (ataylab); noaniq kod — o'tkazib yuboriladi
Avtotest:   N
Manba:      Sbe_Dalion.Send_Balance_Sync (1561-1724), Sbr_Api.Warehouse_Balance_Update (644-689)

S-05.5.2  Regos — kod aniq moslik, faqat kelgan qatorlar, manfiy qoldiq                       [ext][bug-candidate]
Shart:      Alfa Regos bilan; ombor kodi «TSH», Regos stock_id «tsh » (bo'shliq / registr)
Kutilgan:   kod _u2 kabi registr va bo'shliqsiz mos keladi; xato qatorlar jurnalda
Hozir:      aniq moslik — «tsh » topilmaydi, jim o'tkaziladi (when others then null); javobda yo'q tovarlar 0 qilinmaydi; manfiy qoldiq yoziladi (avail N) va
            yig'indini kamaytiradi (S-05.3.6)
Avtotest:   N
Manba:      Sbe_Regos_Supplier (439-560)

S-05.5.3  SMX / SalesDoctor — Warehouse_Balance_Update                                        [ext]
Kutilgan:   faqat mavjud biriktirishlar yangilanadi; javobda yo'q → N / 0; avail = Y va quantity ≤ 0 juftligi → xom ORA-02290 (_c2) [bug-candidate]
Avtotest:   N
Manba:      Sbe_Smx (290-401), Sbe_Sd (403)
```

## E2E stsenariylar

```
S-05.E1  Ombor → region → katalog → buyurtma → yechish → bekor                                [effect][state]
Kanal:      web+mobile
Oqim:       (1) Alfa-admin «Samarqand ombori» (kod SAM, region Samarqand) yaratadi, «Sut 1L»ni biriktiradi (N/0) → Epsilon katalogda ko'rmaydi;
            (2) Dalion sinxron: Sut 50 Y → Epsilon ko'radi, Gamma (Toshkent) uchun Sut Toshkent omborida Y bo'lgani uchun ko'radi;
            (3) Gamma buyurtma Sut × 120 → checkout o'tadi → Alfa-admin New → Toshkent 0 (N), Samarqand 30;
            (4) Alfa-admin Cancelled → 120 Toshkent'ga (S-05.3.7), Samarqand 30 qoladi;
            (5) Alfa-admin «Samarqand ombori»ni o'chiradi → Epsilon katalogda Sut ko'rmaydi; DW qayta qurilmagan (S-05.1.2)
Avtotest:   Y (Dalion mock)
```

## Qarorlar / ochiq savollar

| Keys | Savol | Qaror |
|---|---|---|
| A. S-05.3.6 | Yig'indiga avail = N va manfiy qoldiqlar kiradi | Shunday qoladi (07.10.2026) — avail = N qoldiqlar faqat ma'lumot uchun, 10 daqiqa – 24 soat oralig'ida yangilanadi |
| B. S-05.3.7 | Qaytarish birinchi omborga | Shunday qoladi (07.10.2026) — Smartup24'da ombor hisobi yuritilmaydi, aniq hisob kerak emas |
| C. S-05.3.3 | «Изменить наличие» fiktiv 1 000 000 | Shunday qoladi (07.10.2026) |
| D. S-05.3.9 | Parallel yechishda oversell | E'tibor berilmaydi (07.10.2026) |
| E. S-05.4.5 | Checkout'da qoldiq tekshiruvi | Shunday qoladi (07.10.2026) |
| F. S-05.1.6 | Moderator ombor yaratishi / tahrirlashi | Ha (07.10.2026) → SMAR24-1004 (izoh) |
| S-05.1.5 | Egalik | SMAR24-926 |

## Jira (07.10.2026)

| Keys | Jira |
|---|---|
| S-05.1.2, 1.3 — ombor o'chirish: pcode, ishoralar ORA-02292, DW, Dalion bind | SMAR24-1059 |
| S-05.2.1, 2.3, 1.4 — validatsiya yo'q; yo'q region_id regionlarni o'chiradi; skalyar warehouse_ids | SMAR24-1060 |
| S-05.3.2, 1.5 — ombor IDOR / egasini almashtirish; chet tovar / xizmat biriktirish | SMAR24-1061 |
| S-05.3.7, 3.8 — bekor qilishda NO_DATA_FOUND; Suspended orqali ikki marta yechish | SMAR24-1062 |
| S-05.4.3 — c:exp_product_supplier_list dubl va region | SMAR24-1063 |
| S-05.5.2, 5.3 — Regos kod mosligi; SMX / SD _c2 ORA-02290 | SMAR24-1064 |
| S-05.1.6 — moderator ombor yaratishi (qaror F) | SMAR24-1004 (izoh) |
| S-05.1.5 — egalik | SMAR24-926 |

## Avtotest holati (QA avtomatlashtirish, bizning repo)

| Keys | Fayl | Holat |
|---|---|---|
| S-05.1.1 | tests/sbr/supplier/warehouse/test_warehouse_list.py::test_warehouse_list_shows_columns | ✅ DEV yashil (2026-10-14) |
| S-05.1.2 | tests_mobile/tests/warehouse/test_warehouse_delete_e2e.py::test_delete_e2e_1…4 (web+mobil, 4 bosqich) | ✅ DEV rasmiy run 4 passed (2026-10-16, 15 daq): Epsilon katalogi «Ничего не найдено!» (Sut/Qatiq yo'q), Gamma'da Qatiq yo'q. Web katalogda Qatiq qoladi (DW, SMAR24-1059) — web tekshirilmaydi (test-case mobil). So'rov/ORA-02292 qismi — UI yo'li yo'q |
| S-05.1.3 (rename) | tests/sbr/supplier/warehouse/test_warehouse_api.py::test_api_default_warehouse_rename_rejected | ⚠️ xfail (strict) — SMAR24-1059: Beta o'z «Склад по умолчанию»ga `warehouse+edit$save` name=«Boshqa» → HTTP 200, nom «Boshqa» bo'ladi (pcode tekshirilmaydi; test oxirida tiklanadi) (2026-10-18) |
| S-05.1.3 (delete) | tests/sbr/supplier/warehouse/test_warehouse_api.py::test_api_default_warehouse_delete_rejected | ⚠️ xfail (strict) — SMAR24-1059: `warehouse_list$delete` standart ombor → HTTP 200, ombor o'chadi (2026-10-18) |
| S-05.1.4 | tests/sbr/supplier/warehouse/test_warehouse_list.py::test_warehouse_delete | ✅ DEV yashil (2026-10-15) — qator menyusidan o'chirish ishlaydi, skalyar warehouse_ids xatosi kuzatilmadi |
| S-05.1.5 (edit:model) | tests/sbr/supplier/warehouse/test_warehouse_api.py::test_api_foreign_warehouse_edit_model_rejected | ⚠️ xfail (strict) — SMAR24-926/1061: Alfa sessiyasi «Beta ombori» `warehouse+edit:model` → HTTP 200, Beta omborining to'liq ma'lumoti (2026-10-18) |
| S-05.1.5 (edit$save) | tests/sbr/supplier/warehouse/test_warehouse_api.py::test_api_foreign_warehouse_rename_rejected | ⚠️ xfail (strict) — SMAR24-926/1061: Alfa «Beta ombori»ni qayta nomlaydi → HTTP 200, Beta'da nom o'zgaradi (test tiklaydi) |
| S-05.1.5 ($attach) | tests/sbr/supplier/warehouse/test_warehouse_api.py::test_api_foreign_warehouse_attach_rejected | ⚠️ xfail (strict) — SMAR24-926/1061: Alfa o'z tovarini «Beta ombori»ga biriktiradi → HTTP 200, bog'lanish yaratiladi. DIQQAT: bind ro'yxati faqat CHAQIRUVCHI supplier tovarlarini ko'rsatadi — Beta ko'rinishida yo'q, Alfa ko'rinishida bor |
| S-05.1.5 ($detach) | tests/sbr/supplier/warehouse/test_warehouse_api.py::test_api_foreign_warehouse_detach_rejected | ✅ DEV yashil (2026-10-18) — «rad» = holat o'zgarmagan: Beta tovari «Beta ombori»da qoladi. Lekin server 200 (bo'sh body) qaytaradi, xato xabari yo'q — jim e'tiborsiz qoldiradi (Team Lead'ga xabar) |
| S-05.1.5 (supplier_id) | tests/sbr/supplier/warehouse/test_warehouse_api.py::test_api_warehouse_owner_change_rejected | ⚠️ xfail (strict) — SMAR24-926/1061: Alfa vaqtinchalik ombori `edit$save` supplier_id = Beta → HTTP 200, ombor Beta ro'yxatiga o'tadi |
| S-05.1.5 ($delete) | tests/sbr/supplier/warehouse/test_warehouse_api.py::test_api_foreign_warehouse_delete_rejected | ⚠️ xfail (strict) — SMAR24-926/1061: Alfa «Beta ombori»ni o'chiradi → HTTP 200, ombor o'chadi |
| S-05.1.6 | tests/sbr/supplier/warehouse/test_warehouse_list.py::test_warehouse_moderator_can_open | ✅ DEV yashil (2026-10-15) — moderator supplier_view'da «Склады»: «Создать», qator paneli «Изменить/Удалить/Товары» bor (faqat ko'rinish tekshirildi) |
| S-05.2.1 (a) | tests/sbr/supplier/warehouse/test_warehouse_form.py::test_warehouse_create_empty_name_blocked | ✅ DEV yashil — maydon `border-error-300` (qizil), matn yo'q, so'rov ketmaydi |
| S-05.2.1 (b) | tests/sbr/supplier/warehouse/test_warehouse_form.py::test_warehouse_create_duplicate_code_error | ⚠️ xfail (strict) — SMAR24-1060: dublikat kod xom texnik xato «Z:#z:sbr_supplier_warehouses dup_val_on_index code=tsh …», «bunday kod bor» kabi tushunarli xabar yo'q (assertion: xom belgilar dup_val_on_index / ORA- / Z:#z: yo'q) |
| S-05.2.1 (c) | tests/sbr/supplier/warehouse/test_warehouse_form.py::test_warehouse_create_code_trimmed | ✅ DEV yashil — «  Z…  » → ro'yxatda «Z…» (trim). Test-case (c) «« TSH »» noaniq: mavjud TSH bilan emas, yangi kod bilan tekshirildi |
| S-05.2.1 (d) | tests/sbr/supplier/warehouse/test_warehouse_form.py::test_warehouse_create_name_max_500 | ✅ DEV yashil — 501 belgidan 500 qoladi |
| S-05.2.1 (e) | tests/sbr/supplier/warehouse/test_warehouse_form.py::test_warehouse_create_duplicate_name_allowed | ⚠️ xfail (strict) — test-case [taxmin] «ruxsat», ilova nomni unikal qiladi: `warehouse+add$save` 500 «Этот название уже используется (название : …) Попробуйте другой.» — Team Lead qarori kutilmoqda |
| S-05.2.1 (f) | tests/sbr/supplier/warehouse/test_warehouse_api.py::test_api_create_unknown_region_error | ⚠️ xfail (strict) — SMAR24-1060: `warehouse+add$save` region_id=[999999999] → HTTP 500 xom «Z:#z:sbr_supplier_warehouse_regions parent key not found sbr_regions_pk …»; ombor yaratilmaydi (2026-10-18). «Beta kompaniyasi regioni» — DEV'da ikkinchi kompaniya yo'q, tekshirilmadi |
| S-05.2.3 | tests/sbr/supplier/warehouse/test_warehouse_api.py::test_api_edit_without_region_key_keeps_regions | ⚠️ xfail (strict) — SMAR24-1060: 2 regionli ombor (Ташкент + Бухара) `edit$save` region_id kalitisiz → HTTP 200, edit:model region_id = [] (hammasi o'chadi) (2026-10-18) |
| S-05.2.2 (web) | tests/sbr/supplier/warehouse/test_warehouse_form.py::test_warehouse_edit_regions | ✅ DEV yashil — multi (2 region, «2 выбрано»), ro'yxatda ikkalasi; hammasi olib tashlansa regionsiz. Mobil qismi — 2-guruh |
| S-05.3.1 (web) | tests/sbr/supplier/warehouse/test_warehouse_products.py::test_warehouse_product_attach_detach | ✅ DEV yashil — «Доступные» = shu omborda yo'qlar (boshqa ombordagi ham chiqadi); biriktirish avail = Нет; ustunlar 4 ta, miqdor yo'q; Открепить. Xizmat tovari DEV'da yo'q — tekshirilmadi. Katalog (mobil) — 2-guruh |
| S-05.3.2 | tests/sbr/supplier/warehouse/test_warehouse_api.py::test_api_attach_foreign_product_rejected | ✅ DEV yashil (2026-10-18) — «rad» = holat o'zgarmagan: Beta tovari Alfa omboriga tushmaydi (Alfa va Beta ko'rinishida ham yo'q). Lekin server 200 (bo'sh body) qaytaradi, xato xabari yo'q — jim e'tiborsiz qoldiradi (Team Lead'ga xabar). Xizmat tovari DEV'da yo'q — tekshirilmadi |
| S-05.4.1 | tests_mobile/tests/warehouse/test_warehouse_catalog.py::test_catalog_shows_only_available_products | ✅ DEV yashil (2026-10-16) — Gamma: Sut, Non bor; Qatiq (N) yo'q |
| S-05.2.2 (mobil) | tests_mobile/tests/warehouse/test_warehouse_catalog.py::test_catalog_city_warehouse_covers_district | ✅ DEV yashil — tumandagi Gamma shahar darajasidagi ombordagi Non'ni ko'radi (test o'zi Region-{c}city → Region-{c}tuman daraxtini yaratadi) |
| S-05.4.2 | tests_mobile/tests/warehouse/test_warehouse_catalog.py::test_catalog_filters_by_warehouse_region | ✅ DEV yashil — Gamma: Non+Qatiq, Sut yo'q; Epsilon: Sut+Qatiq, Non yo'q; regionlar olib tashlangach ikkalasi hamma tovar. Farq: «Toshkentda Sut N» = Sut Toshkent omboriga biriktirilmagan («Изменить наличие» tovarning barcha omborlarini birdan o'zgartiradi) |
| S-05.3.1 (mobil) | tests_mobile/tests/warehouse/test_warehouse_catalog.py::test_catalog_hides_new_and_detached_products | ✅ DEV yashil — biriktirilgan Qatiq (N) katalogda yo'q; ochirilgan Non yo'qoladi |
| S-05.3.3 | tests_mobile/tests/warehouse/test_warehouse_catalog.py::test_catalog_follows_change_avail | ✅ DEV yashil — Qatiq Да → paydo; Sut Нет → yo'qoladi; Да → qaytadi (mobil). Fiktiv 1 000 000 qiymati tekshirilmadi (UI'da miqdor yo'q) |
| S-05.4.3 | tests_mobile/tests/warehouse/test_warehouse_catalog.py::test_product_suppliers_listed_once | ⚠️ xfail (strict, raises=AssertionError) — SMAR24-1063: tovar sahifasi → «Другие поставщики» («Изменить поставщика») da Alfa 2 marta (Sut Toshkent Y + Samarqand Y). «Ombor regioni filtrlanmaydi» qismi UI'dan tekshirilmadi (katalogda ko'rinmagan tovar sahifasiga UI'da kirib bo'lmaydi) |
| S-05.4.5 | — | ⛔ yozilmadi — Shart «Non 20» UI'da qo'yib bo'lmaydi («Изменить наличие» faqat 1 000 000 / 0); qoldiqdan ko'p qo'shish uchun aniq qoldiq kerak — Team Lead savoli (qoldiq keyslari bilan bir xil) |
| boshqalar | — | yozilmagan |
