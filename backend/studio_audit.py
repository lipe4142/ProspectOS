"""Auditoria real em Chromium, sem acesso à rede ou ao CRM."""
import base64
from contextlib import suppress

SIZES = (("Celular",390,844),("Tablet",768,1024),("Desktop",1440,900))


def audit(document):
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        raise ValueError("Playwright indisponível. Instale as dependências do backend.") from None
    results=[]
    with sync_playwright() as p:
        browser=None
        for channel in (None,"msedge","chrome"):
            try:
                kwargs={"headless":True,"timeout":5000}
                if channel:
                    kwargs["channel"]=channel
                browser=p.chromium.launch(**kwargs)
                break
            except Exception:
                continue
        if browser is None:
            raise ValueError("Instale Chromium com python -m playwright install chromium ou utilize Chrome/Edge instalado.")
        try:
            for label,width,height in SIZES:
                context=browser.new_context(viewport={"width":width,"height":height},reduced_motion="reduce",service_workers="block")
                try:
                    context.route("**/*",lambda route: route.abort())
                    page=context.new_page()
                    page.set_content(document,wait_until="load",timeout=10000)
                    data=page.evaluate("""() => {
                      const vw=document.documentElement.clientWidth;
                      const over=[...document.querySelectorAll('header, main, footer, h1, h2, .btn, .item, img')].filter(e=>{
                        const r=e.getBoundingClientRect();return r.width>0&&(r.left < -2 || r.right > vw+2)
                      }).slice(0,8).map(e=>e.tagName+' '+String(e.className||'').slice(0,70));
                      const images=[...document.images];
                      return {viewport:vw,documentWidth:document.documentElement.scrollWidth,
                        overflow:over,brokenImages:images.filter(i=>i.complete&&!i.naturalWidth).length,
                        headings:document.querySelectorAll('h1').length,
                        tinyButtons:[...document.querySelectorAll('.btn')].filter(e=>{const r=e.getBoundingClientRect();return r.width>0&&r.height<40}).length};
                    }""")
                    pic=page.screenshot(type="jpeg",quality=55,timeout=10000,animations="disabled")
                    results.append({"label":label,"width":width,"height":height,
                                    "passed":data["documentWidth"]<=width+2 and not data["overflow"] and not data["brokenImages"] and data["headings"]==1,
                                    **data,"screenshot":"data:image/jpeg;base64,"+base64.b64encode(pic).decode("ascii")})
                finally:
                    context.close()
        finally:
            with suppress(Exception):
                browser.close()
    return results
