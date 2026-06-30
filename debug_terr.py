import random
from playwright.sync_api import sync_playwright
from flow_authorization import authorization

TERRITORY_URL = "https://app3.greenwhite.uz/x24/a2/sb/sbr/moderator/territory_list"


def log(msg):
    print(f"[DEBUG] {msg}", flush=True)


def main():
    a = random.randint(1000, 9999)
    name = f"kavardan{a}"
    log(f"name = {name}")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, args=["--start-maximized"])
        context = browser.new_context(no_viewport=True)
        context.set_default_timeout(15000)
        context.set_default_navigation_timeout(60000)
        page = context.new_page()
        try:
            authorization(page)
            page.goto(TERRITORY_URL)
            page.wait_for_load_state("networkidle")
            page.get_by_role("button", name="Создать", exact=True).click()
            page.wait_for_timeout(1000)

            tb = page.get_by_role("textbox")
            log(f"textbox count = {tb.count()}")
            tb.first.click()
            tb.first.fill(name)
            log(f"filled. textbox value = '{tb.first.input_value()}'")

            # ─── XARITA chizish asboblarini o'rganamiz ───────────────────
            # Leaflet.draw toolbar linklari (poligon/to'rtburchak/aylana va h.k.)
            draw_selectors = [
                "a.leaflet-draw-draw-polygon",
                "a.leaflet-draw-draw-rectangle",
                "a.leaflet-draw-draw-polyline",
                "a.leaflet-draw-draw-circle",
                "a.leaflet-draw-draw-marker",
            ]
            for sel in draw_selectors:
                log(f"{sel} count = {page.locator(sel).count()}")
            log(f"all leaflet-draw links = {page.locator('a[class*=leaflet-draw]').count()}")
            log(f"leaflet-bar links = {page.locator('.leaflet-bar a').count()}")

            # map konteyner o'lchami
            mapc = page.locator(".leaflet-container, #map, .map").first
            log(f"map container count = {page.locator('.leaflet-container').count()}")
            box = mapc.bounding_box()
            log(f"map box = {box}")

            # Poligon chizishni sinaymiz (leaflet.draw)
            poly = page.locator("a.leaflet-draw-draw-polygon").first
            if poly.count() and box:
                poly.click()
                page.wait_for_timeout(500)
                cx, cy = box["x"] + box["width"] / 2, box["y"] + box["height"] / 2
                pts = [(cx - 80, cy - 80), (cx + 80, cy - 80),
                       (cx + 80, cy + 80), (cx - 80, cy + 80)]
                for (px, py) in pts:
                    page.mouse.click(px, py)
                    page.wait_for_timeout(200)
                # poligonni yopish — birinchi nuqtaga qayta bosamiz
                page.mouse.click(pts[0][0], pts[0][1])
                page.wait_for_timeout(500)
                # "Finish/Завершить" tugmasi bo'lsa bosamiz
                for label in ["Finish", "Завершить", "Готово"]:
                    b = page.get_by_text(label, exact=True)
                    if b.count():
                        b.first.click()
                        break
                log("poligon chizildi")
                page.screenshot(path="dbg_terr_drawn.png", full_page=True)

            # MUHIM: add-forma sahifasida "Создать" tugmasi bormi?
            sozdat_on_form = page.get_by_role("button", name="Создать", exact=True)
            log(f"[add-form] Создать button count = {sozdat_on_form.count()}, "
                f"visible = {sozdat_on_form.first.is_visible() if sozdat_on_form.count() else False}")
            log(f"[add-form] url before save = {page.url}")

            save = page.get_by_role("button", name="Сохранить")
            log(f"Сохранить count = {save.count()}, enabled = {save.first.is_enabled()}, disabled_attr = {save.first.get_attribute('disabled')}")

            import time
            t0 = time.time()
            save.first.click()
            # URL territory_list ga o'tishini 20s gacha kuzatamiz
            navigated = False
            for _ in range(40):
                if "territory_list" in page.url:
                    navigated = True
                    break
                page.wait_for_timeout(500)
            log(f"navigated = {navigated} in {time.time()-t0:.1f}s, url = {page.url}")

            # validatsiya / xato matnlari bormi
            for w in ["обязательн", "Заполните", "ошибк", "Выберите", "Регион", "Тип", "границ", "област", "карт"]:
                c = page.get_by_text(w).count()
                if c:
                    log(f"  text '{w}' count = {c}")
            # toast / dialog
            log(f"cdk-overlay buttons = {page.locator('.cdk-overlay-container button').count()}")
            page.screenshot(path="dbg_terr_form.png", full_page=True)

            # forma ichidagi barcha label/input larni ko'ramiz
            inputs = page.locator("form input, smt-input input, smt-select, smt-tree-select").all()
            log(f"form control count = {len(inputs)}")
        except Exception as e:
            log(f"EXCEPTION: {type(e).__name__}: {e}")
            page.screenshot(path="dbg_terr_err.png", full_page=True)
        finally:
            page.wait_for_timeout(1500)
            context.close()
            browser.close()


if __name__ == "__main__":
    main()
