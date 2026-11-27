"""Auditoria real em Chromium, sem acesso à rede ou ao CRM."""
import base64
from contextlib import suppress

SIZES = (("Celular",390,844),("Tablet",768,1024),("Desktop",1440,900))


def audit(document,interactive=False):
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
                context=browser.new_context(viewport={"width":width,"height":height},reduced_motion="no-preference" if interactive else "reduce",service_workers="block")
                try:
                    context.route("**/*",lambda route: route.abort())
                    page=context.new_page()
                    errors=[]
                    page.on("pageerror",lambda err: errors.append(str(err)[:200]))
                    page.set_content(document,wait_until="load",timeout=15000)
                    if interactive: page.wait_for_timeout(250)
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
                    checks=[]
                    if interactive:
                        # Testes reais de eventos no runtime fixo, não no código livre não confiável.
                        tests=[
                            ("Dia/noite","#daynight","""() => {document.querySelector('[data-mode=night]').click();const ok=document.querySelector('#daynight').classList.contains('is-night');document.querySelector('[data-mode=day]').click();return ok}"""),
                            ("Simulador","#solar-calc","""() => {const f=document.querySelector('#solar-calc');for(const [k,v] of Object.entries({bill:500,kwh:400,rate:1,noncomp:0.2,fixed:20}))f.elements[k].value=v;f.dispatchEvent(new Event('input',{bubbles:true}));return f.querySelector('[data-results]').children.length===6}"""),
                            ("Formulário demonstrativo","#quote","""() => {const f=document.querySelector('#quote');f.elements.name.value='Teste';f.elements.city.value='Teste';f.elements.bill.value='200';f.requestSubmit();return document.querySelector('#quote-status').textContent.includes('Nenhum dado foi enviado')}"""),
                            ("Galeria","[data-gallery]","""() => {document.querySelector('[data-gallery]').click();const d=document.querySelector('#lightbox'),ok=d.open&&!!d.querySelector('img').src;d.close();return ok}""")
                        ]
                        for label_test,selector,script in tests:
                            if page.locator(selector).count():
                                try: passed=bool(page.evaluate(script))
                                except Exception: passed=False
                                checks.append({"label":label_test,"passed":passed})
                    results.append({"label":label,"width":width,"height":height,
                                    "passed":data["documentWidth"]<=width+2 and not data["overflow"] and not data["brokenImages"] and data["headings"]==1 and not errors and all(c["passed"] for c in checks),
                                    "interaction_checks":checks,"page_errors":errors,
                                    **data,"screenshot":"data:image/jpeg;base64,"+base64.b64encode(pic).decode("ascii")})
                finally:
                    context.close()
        finally:
            with suppress(Exception):
                browser.close()
    return results
