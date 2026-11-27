"""Direção de arte e componentes originais para o FLP Site Studio.
Nenhum código, marca ou imagem de terceiros é incorporado.
"""
import html
import base64
import hashlib
import re

STYLES = {
    "split": ("Contemporâneo", "split"),
    "editorial": ("Editorial sofisticado", "editorial"),
    "center": ("Minimalista central", "center"),
    "cinematic": ("Cinematográfico", "cinematic"),
    "industrial": ("Industrial / tecnológico", "industrial"),
    "organic": ("Orgânico / acolhedor", "organic"),
    "brutalist": ("Tipografia expressiva", "brutalist"),
    "luxury": ("Luxo discreto", "luxury"),
    "bento": ("Bento contemporâneo", "bento"),
}
VARIANTS = {
    "auto": "Automático",
    "split": "Texto e imagem",
    "cover": "Imagem de impacto",
    "center": "Centralizado",
    "grid": "Cards em grade",
    "list": "Lista editorial",
    "bento": "Bento",
}
LABELS = {"hero":"Início", "about":"Sobre", "services":"Serviços", "gallery":"Galeria",
          "faq":"Dúvidas", "contact":"Contato", "cta":"Contato", "benefits":"Diferenciais",
          "process":"Como funciona", "products":"Produtos", "location":"Localização"}


def esc(v):
    return html.escape(v, quote=True)


def luminance(color):
    rgb = [int(color[i:i+2],16)/255 for i in (1,3,5)]
    return sum(w*(c/12.92 if c<=.04045 else ((c+.055)/1.055)**2.4) for c,w in zip(rgb,(.2126,.7152,.0722)))


def contrast(a,b):
    x,y=sorted((luminance(a),luminance(b)))
    return (y+.05)/(x+.05)


def ink(color):
    return "#000000" if luminance(color) > .179 else "#ffffff"


def art(style):
    # Original abstract compositions; no claim to be a business photograph.
    if style in ("industrial","bento","split"):
        shape='<g transform="translate(410 290) rotate(-24)"><rect x="-235" y="-145" width="470" height="290" rx="35" fill="none" stroke="currentColor" stroke-width="2"/><path d="M-235 -50H235 M-235 50H235 M-120 -145V145 M0 -145V145 M120 -145V145" stroke="currentColor" opacity=".5"/><circle r="88" fill="var(--primary)" opacity=".75"/></g>'
    elif style in ("editorial","luxury","organic"):
        shape='<g transform="translate(430 300)"><ellipse rx="208" ry="255" fill="var(--primary)" opacity=".32" transform="rotate(35)"/><ellipse rx="147" ry="235" fill="none" stroke="currentColor" stroke-width="2" transform="rotate(-35)"/><path d="M-190 180 Q100 -300 200 140" fill="none" stroke="currentColor" stroke-width="2"/></g>'
    else:
        shape='<g transform="translate(420 300)"><circle r="220" fill="var(--primary)" opacity=".23"/><circle r="170" fill="none" stroke="currentColor"/><circle r="110" fill="none" stroke="currentColor"/><path d="M-250 0H250 M0 -250V250" stroke="currentColor" opacity=".55"/></g>'
    return '<div class="art" aria-hidden="true"><svg viewBox="0 0 840 600" preserveAspectRatio="xMidYMid slice" xmlns="http://www.w3.org/2000/svg">'+shape+'</svg><span>FLP / DIREÇÃO VISUAL</span></div>'


def photo(s, style, hero=False, fallback=False):
    if s["image"]:
        provider = "Pixabay" if "pixabay.com/" in s.get("image_source","") else "Pexels"
        credit = '<figcaption>Imagem ilustrativa · <a href="'+esc(s["image_source"])+'" rel="noopener noreferrer">Foto: '+esc(s.get("image_credit") or provider)+' / '+provider+'</a></figcaption>' if s.get("image_source") else ""
        return '<figure class="media"><img src="'+esc(s["image"])+'" alt="'+esc(s.get("image_alt",""))+'" loading="'+("eager" if hero else "lazy")+'" decoding="async">'+credit+'</figure>'
    return art(style) if fallback else ""


def cards(s, kind):
    items = s.get("items") or []
    if not items:
        lines = [x.strip(" -•\t") for x in s["body"].splitlines() if x.strip()]
        if len(lines)>1:
            items = [{"title":x.split(" — ",1)[0],"body":x.split(" — ",1)[1] if " — " in x else ""} for x in lines[:12]]
    if not items:
        return ""
    if kind=="faq":
        return '<div class="faq-list">'+''.join('<details><summary>'+esc(x["title"])+'<span aria-hidden="true">+</span></summary><p>'+esc(x["body"])+'</p></details>' for x in items)+'</div>'
    return '<div class="cards">'+''.join('<article class="item"><span class="number">%02d /</span><h3>%s</h3>%s</article>'%(i+1,esc(x["title"]),'<p>'+esc(x["body"])+'</p>' if x["body"] else "") for i,x in enumerate(items))+'</div>'


CSS = """
*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;color:var(--text);background:var(--bg);font-family:var(--font),sans-serif;line-height:1.5}a{color:inherit;text-decoration:none}button,a,summary{-webkit-tap-highlight-color:transparent}a:focus-visible,summary:focus-visible{outline:3px solid var(--primary);outline-offset:4px}
.shell{width:min(100% - 2*clamp(20px,5vw,80px),1360px);margin-inline:auto}.top{position:sticky;top:0;z-index:5;background:var(--bg);border-bottom:1px solid var(--line)}.nav{min-height:76px;display:flex;justify-content:space-between;align-items:center;gap:22px}.brand{font-size:clamp(16px,1.5vw,22px);font-weight:850;letter-spacing:-.04em;max-width:40%;overflow-wrap:anywhere}.brand small{display:block;color:var(--muted);font-size:10px;letter-spacing:.14em;text-transform:uppercase;font-weight:600}.navlinks{display:flex;align-items:center;gap:clamp(12px,2vw,30px);font-size:13px;font-weight:600}.btn{display:inline-flex;align-items:center;justify-content:center;gap:12px;background:var(--primary);color:var(--on-primary);padding:15px 24px;font-weight:750;border:1px solid var(--primary);border-radius:var(--radius);font-size:14px;transition:transform .2s,opacity .2s;max-width:100%}.btn:hover{transform:translateY(-3px);opacity:.9}.btn.secondary{background:transparent;color:var(--text);border-color:var(--line)}.nav .btn{padding:10px 16px;font-size:12px}.actions{display:flex;gap:10px;flex-wrap:wrap;margin-top:30px}.kicker{display:flex;align-items:center;gap:10px;font-size:11px;font-weight:750;letter-spacing:.18em;text-transform:uppercase;margin:0 0 20px;color:var(--muted)}.kicker:before{content:"";height:2px;width:28px;background:var(--primary)}h1,h2,h3,p{overflow-wrap:anywhere}h1,h2{font-family:var(--heading),serif;font-weight:var(--heading-weight);line-height:.99;letter-spacing:var(--tracking);margin:0}h1{font-size:clamp(40px,6.8vw,106px);max-width:13ch}h2{font-size:clamp(32px,4.3vw,66px);max-width:18ch}h3{font-size:clamp(18px,2vw,26px);line-height:1.2;margin:0 0 12px;letter-spacing:-.035em}p{white-space:pre-line;font-size:clamp(15px,1.3vw,19px);line-height:1.72;max-width:64ch;margin:18px 0;color:var(--muted)}.hero{position:relative;padding-block:clamp(36px,7vw,100px);min-height:min(770px,85vh);display:grid;align-items:center;isolation:isolate;overflow:hidden}.hero .shell{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,.95fr);gap:clamp(28px,5vw,80px);align-items:center}.hero .copy{z-index:1;min-width:0}.media,.art{margin:0;overflow:hidden;border-radius:var(--media-radius);min-width:0;position:relative;aspect-ratio:4/4.3;background:var(--surface);color:var(--text)}.media figcaption{position:absolute;bottom:0;right:0;max-width:100%;font-size:10px;padding:6px 10px;background:#111d;color:#fff}.media img{display:block;width:100%;height:100%;object-fit:cover}.art{display:grid;place-items:center;background:radial-gradient(ellipse at 65% 35%,var(--tint),transparent 65%),var(--surface);border:1px solid var(--line)}.art svg{width:100%;height:100%;position:absolute;inset:0}.art span{position:absolute;left:20px;bottom:20px;font-size:10px;letter-spacing:.16em;font-weight:700}.hero-note{border-top:1px solid var(--line);margin-top:32px;padding-top:15px;color:var(--muted);font-size:11px;display:flex;justify-content:space-between;gap:10px}.section{padding-block:clamp(56px,8vw,120px);border-top:1px solid var(--line)}.section .intro{display:grid;grid-template-columns:1fr .8fr;gap:24px;align-items:end;margin-bottom:36px}.section .intro p{margin:0}.section .split{display:grid;grid-template-columns:1fr 1fr;gap:clamp(24px,5vw,80px);align-items:center}.section .split .media,.section .split .art{aspect-ratio:5/4}.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,220px),1fr));gap:14px}.item{padding:clamp(22px,3vw,40px);border:1px solid var(--line);background:var(--surface);border-radius:var(--media-radius);min-height:175px;transition:transform .2s}.item:hover{transform:translateY(-4px)}.number{display:block;color:var(--muted);font-size:11px;letter-spacing:.15em;margin-bottom:30px}.item p{font-size:15px;margin:0}.faq-list{max-width:900px;margin-inline:auto}.faq-list details{border-bottom:1px solid var(--line);padding:22px 0}.faq-list summary{cursor:pointer;display:flex;justify-content:space-between;gap:20px;font-size:clamp(16px,2vw,23px);font-weight:700;list-style:none}.faq-list summary::-webkit-details-marker{display:none}.faq-list details[open] summary span{transform:rotate(45deg)}.contact-box{background:var(--surface);border:1px solid var(--line);padding:clamp(25px,7vw,90px);border-radius:var(--media-radius)}.contact-box h2{max-width:20ch}.foot{border-top:1px solid var(--line);padding:28px 0}.foot .shell{display:flex;justify-content:space-between;gap:20px;flex-wrap:wrap;font-size:12px;color:var(--muted)}.floating{position:fixed;bottom:20px;right:20px;z-index:6;border-radius:99px;box-shadow:0 8px 30px #0003}.mobile-nav{display:none}.variant-list .cards{grid-template-columns:1fr}.variant-list .item{min-height:0;display:grid;grid-template-columns:70px 1fr 1.1fr;align-items:baseline;gap:15px}.variant-list .item h3,.variant-list .item .number{margin:0}.variant-bento .item:first-child{grid-column:span 2}.variant-center .intro{text-align:center;display:block}.variant-center .intro h2,.variant-center .intro p{margin-inline:auto}.variant-center .intro p{margin-top:18px}.variant-cover .media{aspect-ratio:16/7}.variant-cover .split{grid-template-columns:1fr}.variant-cover .split .media{aspect-ratio:16/7}
.style-editorial,.style-luxury{--heading:Georgia,'Times New Roman';--heading-weight:400;--tracking:-.065em;--radius:2px;--media-radius:2px}.style-editorial .hero .shell{grid-template-columns:1.1fr .9fr}.style-editorial .hero .media{aspect-ratio:4/5}.style-editorial .section:nth-child(even) .split>figure{order:-1}.style-luxury .hero .shell{grid-template-columns:.9fr 1.1fr}.style-luxury h1{font-style:italic}.style-luxury .kicker{letter-spacing:.24em}.style-luxury .cards{gap:0}.style-luxury .item{border-left:0}.style-organic{--heading:Georgia,'Times New Roman';--heading-weight:400;--tracking:-.045em;--radius:99px;--media-radius:32px}.style-organic .hero .media,.style-organic .hero .art{border-radius:50% 50% 18px 18px}.style-industrial{--heading:var(--font);--heading-weight:900;--tracking:-.055em;--radius:3px;--media-radius:4px}.style-industrial .hero .media,.style-industrial .hero .art{aspect-ratio:5/4;border:1px solid var(--line)}.style-industrial .item{border-top:3px solid var(--primary)}.style-brutalist{--heading:Arial,sans-serif;--heading-weight:950;--tracking:-.075em;--radius:0;--media-radius:0}.style-brutalist h1{text-transform:uppercase}.style-brutalist .item{border:2px solid var(--text)}.style-brutalist .hero .art{transform:rotate(-2deg)}.style-bento .hero .art,.style-bento .hero .media{border-radius:34px}.style-bento .cards .item:first-child{background:var(--tint)}.style-center .hero .shell,.hero.variant-center .shell{grid-template-columns:1fr;text-align:center;justify-items:center}.style-center .hero h1,.hero.variant-center h1{max-width:17ch;margin:auto}.style-center .hero p,.hero.variant-center p{margin-inline:auto}.style-center .hero .actions,.hero.variant-center .actions{justify-content:center}.style-center .hero .media,.hero.variant-center .media,.style-center .hero .art,.hero.variant-center .art{width:min(100%,850px);aspect-ratio:16/7}.style-cinematic .hero,.hero.variant-cover{min-height:min(840px,88vh)}.style-cinematic .hero .shell,.hero.variant-cover .shell{grid-template-columns:1fr;align-self:end}.style-cinematic .hero .media,.style-cinematic .hero .art,.hero.variant-cover .media,.hero.variant-cover .art{position:absolute;inset:0;aspect-ratio:auto;z-index:-2;border-radius:0}.style-cinematic .hero.has-photo,.hero.variant-cover.has-photo{color:#fff}.style-cinematic .hero.has-photo p,.style-cinematic .hero.has-photo .kicker,.style-cinematic .hero.has-photo .hero-note,.hero.variant-cover.has-photo p,.hero.variant-cover.has-photo .kicker,.hero.variant-cover.has-photo .hero-note{color:#eee}.style-cinematic .hero.has-photo:after,.hero.variant-cover.has-photo:after{content:"";position:absolute;inset:0;background:linear-gradient(90deg,#000c,#0002),linear-gradient(0deg,#0009,transparent);z-index:-1}.style-cinematic .hero.has-photo .btn.secondary,.hero.variant-cover.has-photo .btn.secondary{color:#fff;border-color:#ffffff70}.hero.variant-split:not(.variant-cover) .shell{grid-template-columns:minmax(0,1fr) minmax(0,1fr);text-align:left;justify-items:stretch}.hero.variant-split:not(.variant-cover) .media,.hero.variant-split:not(.variant-cover) .art{position:relative;inset:auto;z-index:auto;aspect-ratio:4/4.3}.hero.variant-split:not(.variant-cover) h1{margin:0}.hero.variant-split:not(.variant-cover) .actions{justify-content:flex-start}
@media(max-width:850px){.navlinks{display:none}.mobile-nav{display:block;position:relative}.mobile-nav summary{list-style:none;cursor:pointer;padding:10px;border:1px solid var(--line);border-radius:6px}.mobile-nav div{position:absolute;right:0;top:44px;background:var(--bg);border:1px solid var(--line);padding:16px;display:grid;gap:15px;min-width:170px}.brand{max-width:65%}.hero .shell,.style-editorial .hero .shell,.style-luxury .hero .shell,.hero.variant-split:not(.variant-cover) .shell,.section .intro,.section .split{grid-template-columns:1fr}.hero{min-height:0}.style-cinematic .hero,.hero.variant-cover{min-height:620px}.hero .media,.hero .art{aspect-ratio:5/4}.hero-note{margin-top:24px}.section .intro p{margin-top:0}.variant-list .item{grid-template-columns:1fr;gap:8px}.variant-bento .item:first-child{grid-column:auto}.nav .btn{display:none}.floating{bottom:12px;right:12px;padding:12px 18px}.foot{padding-bottom:80px}.style-editorial .section:nth-child(even) .split>figure{order:0}}
@media(prefers-reduced-motion:reduce){*{scroll-behavior:auto!important;transition:none!important;animation:none!important}}
@media(prefers-reduced-motion:no-preference){.hero .copy{animation:enter .65s cubic-bezier(.16,1,.3,1) both}.hero .media,.hero .art{animation:enter .85s cubic-bezier(.16,1,.3,1) both}@keyframes enter{from{opacity:0;transform:translateY(14px)}to{opacity:1;transform:translateY(0)}}}
"""


# JavaScript original e fixo: a IA não pode fornecer ou executar scripts arbitrários.
SCRIPT = """(()=>{const media=matchMedia('(prefers-reduced-motion: reduce)');if(!media.matches&&'IntersectionObserver' in window){const observer=new IntersectionObserver(entries=>{for(const entry of entries){if(entry.isIntersecting){entry.target.classList.add('visible');observer.unobserve(entry.target)}}},{threshold:.08});document.querySelectorAll('.section').forEach(el=>{el.classList.add('reveal');observer.observe(el)})}document.querySelectorAll('.mobile-nav a').forEach(a=>a.addEventListener('click',()=>a.closest('details').removeAttribute('open')));})();"""
SCRIPT_HASH=base64.b64encode(hashlib.sha256(SCRIPT.encode("utf-8")).digest()).decode("ascii")
EXTRA_CSS = """
section{scroll-margin-top:85px}.hero .copy{position:relative}.hero:not(.has-photo) .art{display:none}.hero:not(.has-photo) .shell{grid-template-columns:1fr}.hero:not(.has-photo) h1{max-width:17ch}.hero:not(.has-photo){background:radial-gradient(ellipse at 90% 10%,var(--tint),transparent 70%),var(--bg);min-height:clamp(420px,66vh,720px)}.style-luxury .hero:not(.has-photo),.style-editorial .hero:not(.has-photo){background:linear-gradient(115deg,var(--bg) 65%,var(--surface))}.style-luxury .hero .copy{border-left:2px solid var(--primary);padding-left:clamp(18px,4vw,54px)}.style-luxury h1{font-style:normal}.style-luxury .item{border-left:1px solid var(--line)}.style-luxury .item .number{color:var(--primary)}.style-luxury .btn{letter-spacing:.025em}.style-editorial .hero .copy{padding-bottom:25px}.style-industrial .hero .kicker{letter-spacing:.22em}.style-brutalist .hero h1{font-size:clamp(44px,8vw,118px)}.style-bento .cards{grid-template-columns:repeat(3,minmax(0,1fr))}.style-bento .cards .item:first-child{grid-column:span 2}.surface-accent{--text:var(--on-primary);--muted:var(--on-primary);--surface:color-mix(in srgb,var(--on-primary) 9%,var(--primary));--line:color-mix(in srgb,var(--on-primary) 28%,transparent);background:var(--primary);color:var(--text)}.surface-accent .btn{background:var(--on-primary);color:var(--primary)}.surface-accent .kicker:before{background:var(--on-primary)}.surface-soft{background:var(--surface)}.surface-contrast{--text:var(--inverse-text);--muted:var(--inverse-text);--surface:color-mix(in srgb,var(--inverse-text) 8%,var(--inverse-bg));--line:color-mix(in srgb,var(--inverse-text) 25%,transparent);background:var(--inverse-bg);color:var(--text)}.section.variant-bento .cards{grid-template-columns:repeat(3,minmax(0,1fr))}.section.variant-bento .item:first-child{grid-column:span 2}.section .cards+.media{margin-top:24px;aspect-ratio:16/7}.spacing-compact .section{padding-block:clamp(38px,5vw,72px)}.spacing-airy .section{padding-block:clamp(70px,10vw,150px)}.corners-square{--radius:0px;--media-radius:0px}.corners-soft{--radius:10px;--media-radius:16px}.corners-round{--radius:99px;--media-radius:28px}.section.reveal{opacity:0;transform:translateY(18px);transition:opacity .55s ease,transform .55s ease}.section.reveal.visible{opacity:1;transform:none}
@media(max-width:850px){.style-bento .cards,.section.variant-bento .cards{grid-template-columns:1fr}.style-bento .cards .item:first-child,.section.variant-bento .item:first-child{grid-column:auto}.hero:not(.has-photo) .shell{grid-template-columns:1fr}.hero:not(.has-photo) h1{max-width:100%}.hero .copy{min-width:0}.nav{gap:10px}.hero h1{font-size:clamp(36px,10vw,64px)}}
@media(prefers-reduced-motion:reduce){.section.reveal{opacity:1;transform:none}}
"""


def render(m, preview=False):
    t=m["theme"]
    style=t["layout"]
    on=ink(t["primary"])
    dark=ink(t["background"])=="#ffffff"
    muted = "#d0d0d0" if dark else "#535353"
    # Blend user-selected foreground with background for coherent surfaces.
    css = f":root{{--primary:{t['primary']};--bg:{t['background']};--text:{t['text']};--on-primary:{on};--font:{t['font']};--heading:var(--font);--heading-weight:850;--tracking:-.055em;--muted:{muted};--line:color-mix(in srgb,var(--text) 18%,transparent);--surface:color-mix(in srgb,var(--text) 5%,var(--bg));--tint:color-mix(in srgb,var(--primary) 20%,var(--bg));--radius:10px;--media-radius:18px}}"
    css += ":root{--inverse-bg:"+("#f6f4ef" if dark else "#142033")+";--inverse-text:"+("#17202b" if dark else "#ffffff")+"}"
    if t.get("heading_font","auto")!="auto":
        css += "body[class]{--heading:"+t["heading_font"]+"}"
    phone=m["phone"]
    if len(phone) in (10,11): phone="55"+phone
    has_phone=12<=len(phone)<=15
    contact_index=next((i for i,s in enumerate(m["sections"]) if s["kind"]=="contact"),0)
    link="https://wa.me/"+phone if has_phone and not preview else "#s"+str(contact_index)
    def button(label="", secondary=False):
        return '<a class="btn'+(' secondary' if secondary else '')+'" href="'+link+'">'+esc(label or ("Fale pelo WhatsApp" if has_phone else "Entre em contato"))+' <span aria-hidden="true">↗</span></a>'
    nav="".join('<a href="#s%d">%s</a>'%(i,esc(LABELS[s["kind"]])) for i,s in enumerate(m["sections"]) if s["kind"] not in ("hero","cta"))
    out=[]
    for i,s in enumerate(m["sections"]):
        kind=s["kind"]; variant=s.get("variant","auto"); title=esc(s["title"]); body=esc(s["body"]); surface=s.get("surface","normal")
        eyebrow=esc(s.get("eyebrow") or (m["title"] if kind=="hero" else LABELS[kind]))
        if variant=="auto" and kind!="hero":
            variant = {"services":"list" if style in ("luxury","editorial") else "bento" if style=="bento" else "grid",
                       "benefits":"grid","process":"list","faq":"center","gallery":"cover","products":"grid","about":"split"}.get(kind,"auto")
        label=s.get("cta","")
        p='<p>'+body+'</p>' if body else ""
        pic=photo(s,style,hero=kind=="hero")
        kick='<div class="kicker">'+eyebrow+'</div>'
        if kind=="hero":
            c=button(label) if has_phone or any(x["kind"]=="contact" for x in m["sections"]) else ""
            secondary='<a class="btn secondary" href="#s'+str(i+1)+'">Conhecer mais ↓</a>' if i+1<len(m["sections"]) else ""
            out.append(f'<section id="s{i}" class="hero variant-{variant} surface-{surface} {"has-photo" if pic else ""}"><div class="shell"><div class="copy">{kick}<h1>{title}</h1>{p}<div class="actions">{c}{secondary}</div></div>{pic}</div></section>')
        elif kind in ("contact","cta","location"):
            anchor='<span id="contato"></span>' if kind=="contact" else ""
            out.append(f'<section id="s{i}" class="section variant-{variant} surface-{surface}"><div class="shell">{anchor}<div class="contact-box">{kick}<h2>{title}</h2>{p}<div class="actions">{button(label) if has_phone else ""}</div>{pic}</div></div></section>')
        else:
            components=cards(s,kind)
            if components:
                inner=f'<div class="intro"><div>{kick}<h2>{title}</h2></div>{p if s.get("items") else ""}</div>{components}{pic}'
            elif pic:
                inner=f'<div class="split"><div>{kick}<h2>{title}</h2>{p}</div>{pic}</div>'
            else:
                inner=f'<div class="intro"><div>{kick}<h2>{title}</h2></div>{p}</div>'
            out.append(f'<section id="s{i}" class="section variant-{variant} kind-{kind} surface-{surface}"><div class="shell">{inner}</div></section>')
    # Preview does not contain an external WhatsApp URL.
    cta=button() if has_phone else ""
    floating='<a class="btn floating" href="'+link+'">WhatsApp ↗</a>' if has_phone and not preview else ""
    script_policy = "" if preview else "; script-src 'sha256-"+SCRIPT_HASH+"'"
    script_tag = "" if preview else "<script>"+SCRIPT+"</script>"
    return ('<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            '<meta name="robots" content="noindex,nofollow"><meta http-equiv="Content-Security-Policy" content="default-src \'none\'; style-src \'unsafe-inline\'; img-src data:; base-uri \'none\'; form-action \'none\''+script_policy+'">'
            '<title>'+esc(m["title"])+'</title><meta name="description" content="'+esc(m["description"])+'"><style>'+css+CSS+EXTRA_CSS+'</style></head>'
            '<body class="style-'+style+' spacing-'+t.get('spacing','balanced')+' corners-'+t.get('corners','auto')+'"><header class="top"><div class="shell nav"><a class="brand" href="#s0">'+esc(m["title"])+'</a><nav class="navlinks" aria-label="Navegação">'+nav+'</nav>'+cta+'<details class="mobile-nav"><summary>Menu ☰</summary><div>'+nav+'</div></details></div></header>'
            '<main>'+''.join(out)+'</main><footer class="foot"><div class="shell"><strong>'+esc(m["title"])+'</strong><span>Projeto demonstrativo desenvolvido pela FLP Systems.</span></div></footer>'+floating+script_tag+'</body></html>')
