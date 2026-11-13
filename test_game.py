from pathlib import Path
from playwright.sync_api import sync_playwright

html = (Path(__file__).resolve().parent / "index.html").read_text(encoding="utf-8")
for asset in [
    '<link rel="preconnect" href="https://fonts.googleapis.com">',
    '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>',
    '<link href="https://fonts.googleapis.com/css2?family=Outfit:wght@400;500;600;700;800&family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">',
    '<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.2/css/all.min.css">'
]:
    html = html.replace(asset, "")

errors = []
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
    page = browser.new_page(viewport={"width": 1365, "height": 900})
    page.goto("about:blank")
    page.evaluate("""(() => {
      const data = new Map();
      Object.defineProperty(window, "localStorage", { configurable: true, value: {
        getItem: k => data.has(k) ? data.get(k) : null,
        setItem: (k, v) => data.set(k, String(v)),
        removeItem: k => data.delete(k), clear: () => data.clear()
      }});
    })()""")
    page.on("pageerror", lambda e: errors.append("PAGE: " + str(e)))
    page.on("console", lambda m: errors.append("CONSOLE: " + m.text) if m.type == "error" else None)

    def load():
        page.set_content(html, wait_until="domcontentloaded")

    load()
    assert page.title() == "Tycoon Empire"
    assert page.locator("#cash").inner_text() != "—"
    for tab in ["business", "production", "market", "research", "finance", "overview"]:
        page.locator(f'#nav button[data-tab="{tab}"]').click()
        assert page.locator("#view").inner_text().strip()

    page.locator('#nav button[data-tab="market"]').click()
    page.locator("#price-Grain").fill("-999")
    page.locator("#price-Grain").dispatch_event("change")
    assert "Harga harus antara" in page.locator("#toastHost").inner_text()

    page.evaluate("localStorage.clear(); state = initialState(); render();")
    page.evaluate("tick()")
    assert page.locator("#day").inner_text() == "2"
    page.locator("#saveBtn").click()
    page.evaluate("state.day = 1; load(); render();")
    assert page.locator("#day").inner_text() == "2"

    payload = '<img src=x onerror=window.__xss=1>'
    page.evaluate("""payload => {
      localStorage.setItem("tycoonEmpireSave", JSON.stringify({
        version: 4, state: {cash: 8000, history:[{day:1,label:payload,amount:1}],
        event:{label:payload,description:payload,product:null,multiplier:1}}
      }));
    }""", payload)
    page.evaluate("load(); render();")
    page.locator('#nav button[data-tab="finance"]').click()
    assert page.evaluate("window.__xss || false") is False
    assert page.locator("#view img").count() == 0

    page.evaluate("""() => {
      localStorage.setItem("tycoonEmpireSave", JSON.stringify({
        version:4, state:{cash:310000,day:1,rep:50,buildings:{farm:1}}
      }));
    }""")
    page.evaluate("load(); render(); tick()")
    assert "Kekaisaran Bisnis Terbentuk" in page.locator("#view").inner_text()

    # Deterministic fresh-start victory using neutral market conditions.
    page.evaluate("state = initialState(); tab = 'overview'; render(); Math.random = () => 0.5;")
    result = page.evaluate("""() => {
      for (let day = 0; day < CFG.deadline && !state.gameOver; day++) {
        document.querySelector("#nextBtn").click();
        for (const product of products) {
          const quantity = state.stock[product] || 0;
          if (quantity > 0) {
            const input = document.querySelector("#qty-" + key(product));
            if (input) input.value = quantity;
            sell(product);
          }
        }
        const choices = Object.keys(defs).filter(k => k !== "lab" && state.cash >= bcost(k) + 500)
          .sort((a, b) => ((defs[b].output * defs[b].price - defs[b].upkeep) / defs[b].cost)
            - ((defs[a].output * defs[a].price - defs[a].upkeep) / defs[a].cost));
        if (choices.length && state.buildings[choices[0]] < 20) buy(choices[0]);
        if (state.cash > 20000 && state.debt > 0) payDebt();
      }
      return {won: state.won, day: state.day, worth: worth()};
    }""")
    assert result["won"] is True and result["day"] <= 151, result

    # Deadline loss from a fresh game with no actions.
    page.evaluate("state = initialState(); tab = 'overview'; render(); Math.random = () => 0.5;")
    page.evaluate("""() => {
      for (let day = 0; day <= CFG.deadline && !state.gameOver; day++)
        document.querySelector("#nextBtn").click();
    }""")
    assert page.evaluate("state.gameOver && !state.won && state.day === CFG.deadline + 1")

    # Bankruptcy after two consecutive negative-cash days.
    page.evaluate("""() => {
      localStorage.setItem("tycoonEmpireSave", JSON.stringify({
        version:4, state:{cash:-1000,day:4,rep:50,debt:0,negativeDays:1,buildings:{farm:0}}
      }));
    }""")
    page.evaluate("load(); render(); tick()")
    assert "Pailit" in page.locator("#view").inner_text()

    mobile = browser.new_page(viewport={"width":360,"height":800}, device_scale_factor=2, is_mobile=True, has_touch=True)
    mobile.goto("about:blank")
    mobile.evaluate("""Object.defineProperty(window, "localStorage", {
      configurable:true, value:{getItem:()=>null,setItem:()=>{},removeItem:()=>{},clear:()=>{}}
    })""")
    mobile.on("pageerror", lambda e: errors.append("MOBILE PAGE: " + str(e)))
    mobile.set_content(html, wait_until="domcontentloaded")
    dimensions = mobile.evaluate("({scroll:document.documentElement.scrollWidth,client:document.documentElement.clientWidth})")
    assert dimensions["scroll"] <= dimensions["client"] + 1, dimensions
    assert mobile.locator("#nav button").count() == 6
    assert mobile.locator('#nav button[data-tab="market"]').bounding_box()["height"] >= 44

    tiny = browser.new_page(viewport={"width":320,"height":700}, is_mobile=True, has_touch=True)
    tiny.goto("about:blank")
    tiny.evaluate("""Object.defineProperty(window, "localStorage", {
      configurable:true, value:{getItem:()=>null,setItem:()=>{},removeItem:()=>{},clear:()=>{}}
    })""")
    tiny.set_content(html, wait_until="domcontentloaded")
    tiny_dimensions = tiny.evaluate("({scroll:document.documentElement.scrollWidth,client:document.documentElement.clientWidth})")
    assert tiny_dimensions["scroll"] <= tiny_dimensions["client"] + 1, tiny_dimensions

    if errors:
        raise AssertionError("\\n".join(errors))
    print("PASS: startup, six tabs, price validation, tick, save/load, XSS, win, bankruptcy, deadline and mobile layout")
    print("MOBILE:", dimensions, tiny_dimensions)
    print("CONSOLE ERRORS: 0")
    browser.close()
