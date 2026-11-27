"""Renderização estática e revisão do modelo validado do Site Studio."""

from html import escape

from studio_design import GOALS, KIND_LABELS

CSS = """
* { box-sizing: border-box; }
html { scroll-behavior: smooth; color-scheme: var(--scheme); }
body {
  margin: 0; background: var(--bg); color: var(--ink);
  font: 1rem/1.65 var(--font), system-ui, sans-serif; overflow-wrap: anywhere;
  --heading: var(--font), system-ui, sans-serif;
  --track: -.055em; --weight: 740; --radius: 18px;
  --line: color-mix(in srgb, var(--ink) 17%, var(--bg));
  --surface: color-mix(in srgb, var(--ink) 5%, var(--bg));
  --wash: color-mix(in srgb, var(--accent) 15%, var(--bg));
}
h1, h2, h3, p, figure { margin: 0; }
h1, h2, h3 { font-family: var(--heading); font-weight: var(--weight); line-height: 1.04; letter-spacing: var(--track); }
h1 { font-size: clamp(2.7rem, 7.5vw, 7rem); max-width: 16ch; }
h2 { font-size: clamp(2rem, 4vw, 3.6rem); }
h3 { font-size: clamp(1.15rem, 2vw, 1.5rem); letter-spacing: -.025em; }
p { white-space: pre-line; }
a { color: inherit; text-decoration: none; }
:focus-visible { outline: 2px solid currentColor; outline-offset: 5px; }
.wrap { width: min(calc(100% - clamp(32px, 11vw, 144px)), 1160px); margin-inline: auto; }
.skip { position: fixed; top: 12px; left: 12px; z-index: 4; transform: translateY(-150%); }
.skip:focus { transform: none; }
.top {
  position: sticky; top: 0; z-index: 3; border-bottom: 1px solid var(--line); background: var(--bg);
}
.top-inner { display: flex; justify-content: space-between; align-items: center; gap: 22px; min-height: 70px; padding-block: 12px; }
.brand { font-size: 1.03rem; font-weight: 740; letter-spacing: -.028em; max-width: 42%; line-height: 1.2; }
.top-links { display: flex; flex-wrap: wrap; justify-content: center; gap: 5px 22px; font-size: .88rem; }
.top-links a:hover, .menu nav a:hover { text-decoration: underline; text-underline-offset: .27em; }
.menu { display: none; position: relative; flex: none; }
.menu summary { cursor: pointer; padding: 8px 13px; font-weight: 650; border: 1px solid var(--line); border-radius: 8px; }
.menu nav {
  position: absolute; inset: calc(100% + 9px) 0 auto auto; width: min(220px, calc(100vw - 32px)); padding: 12px;
  display: grid; gap: 3px; background: var(--bg); border: 1px solid var(--line); border-radius: 12px;
}
.menu nav a { padding: 9px; }
section, main { scroll-margin-top: 85px; }
.hero { position: relative; isolation: isolate; border-bottom: 1px solid var(--line); }
.hero > .wrap { display: grid; align-items: center; gap: clamp(24px, 5vw, 66px); min-height: clamp(400px, 65vh, 710px); padding-block: clamp(65px, 10vw, 155px); }
.hero:not(.has-image) { background: radial-gradient(ellipse at 88% 8%, var(--wash), transparent 70%), var(--bg); }
.hero.has-image .wrap { grid-template-columns: minmax(0, 1.06fr) minmax(0, .94fr); }
.hero p { font-size: clamp(1.04rem, 2vw, 1.24rem); max-width: 52ch; margin-top: 23px; }
.eyebrow { display: flex; align-items: center; gap: .65em; font-size: .78rem; font-weight: 720; text-transform: uppercase; letter-spacing: .14em; margin-bottom: 16px; }
.eyebrow::before { content: ""; width: 1.6em; height: 2px; flex: none; background: var(--accent); }
.actions { display: flex; align-items: center; flex-wrap: wrap; gap: 10px; margin-top: 27px; }
.actions:empty { display: none; }
.button {
  display: inline-flex; align-items: center; justify-content: center; gap: .6em; min-height: 44px;
  padding: 11px 19px; border: 1px solid var(--accent); border-radius: min(var(--radius), 28px);
  background: var(--accent); color: var(--on-accent); font-size: .9rem; font-weight: 750; line-height: 1.3;
  transition: transform .18s ease;
}
.button:hover { transform: translateY(-2px); }
.button:focus-visible { outline-color: var(--ink); }
.button.ghost { color: inherit; border-color: currentColor; background: transparent; }
.top .button { flex: none; }
.media { max-width: 100%; border-radius: var(--radius); overflow: hidden; background: var(--surface); }
.media img { display: block; width: 100%; aspect-ratio: 4 / 3; object-fit: cover; }
.hero .media img { aspect-ratio: 4 / 4.3; }
.hero.variant-center > .wrap { grid-template-columns: 1fr; justify-items: center; text-align: center; }
.hero.variant-center :is(h1, p) { margin-inline: auto; }
.hero.variant-center :is(.eyebrow, .actions) { justify-content: center; }
.hero.variant-center .media { width: min(100%, 840px); }
.hero.variant-center .media img { aspect-ratio: 16 / 8; }
.hero.variant-cover.has-image { color: #fff; --ink: #fff; }
.hero.variant-cover.has-image > .wrap { grid-template-columns: 1fr; align-items: end; min-height: 76vh; }
.hero.variant-cover.has-image .media { position: absolute; inset: 0; z-index: -2; border-radius: 0; }
.hero.variant-cover.has-image .media img { width: 100%; height: 100%; }
.hero.variant-cover.has-image::after { content: ""; position: absolute; z-index: -1; inset: 0; background: linear-gradient(74deg, #000e, #0007); }
.block { padding-block: clamp(52px, 8vw, 110px); border-bottom: 1px solid var(--line); }
.block:nth-of-type(even) { background: var(--surface); }
.block .body { max-width: 64ch; margin-top: 17px; }
.block > .wrap > h1 { font-size: clamp(2.5rem, 6vw, 5.5rem); }
.block .media { margin-top: 24px; }
.block.variant-cover .media img { aspect-ratio: 16 / 7; }
.block.variant-split.has-image > .wrap { display: grid; gap: clamp(24px, 6vw, 80px); grid-template-columns: repeat(2, minmax(0, 1fr)); align-items: center; }
.block.variant-split.has-image .media { margin: 0; }
.block.variant-center > .wrap { text-align: center; }
.block.variant-center :is(.eyebrow, .actions) { justify-content: center; }
.block.variant-center .body { margin-inline: auto; }
.cards {
  display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 14px;
  padding: 0; margin: 30px 0 0; list-style: none;
}
.card {
  padding: clamp(19px, 4vw, 34px); border-radius: var(--radius);
  border: 1px solid var(--line); background: var(--bg);
}
.card p { margin-top: 12px; font-size: .95rem; }
.variant-list .cards { grid-template-columns: 1fr; gap: 0; border-top: 1px solid var(--line); }
.variant-list .card { border: 0; border-bottom: 1px solid var(--line); border-radius: 0; background: transparent; padding-inline: 4px; }
.variant-list .card:has(p) { display: grid; grid-template-columns: .8fr 1.2fr; align-items: baseline; gap: 16px; }
.variant-list .card p { margin: 0; }
.variant-bento .card:first-child { grid-column: span 2; background: var(--wash); }
.faq-list { width: min(100%, 860px); margin: 26px auto 0; text-align: left; }
.faq-list details { border-bottom: 1px solid var(--line); }
.faq-list summary { cursor: pointer; padding: 17px 0; font-weight: 680; }
.faq-list details p { padding-bottom: 19px; }
.block.cta { background: var(--wash); }
.foot { padding-block: 24px; font-size: .82rem; }
.foot .wrap { display: flex; flex-wrap: wrap; justify-content: space-between; gap: 8px 16px; }
.foot a:hover { text-decoration: underline; }
.style-editorial {
  --heading: Georgia, serif; --weight: 400; --track: -.055em; --radius: 3px;
}
.style-editorial .hero:not(.has-image) > .wrap { align-items: end; }
.style-editorial .eyebrow::before { width: 2.4em; }
.style-editorial .hero .media img { aspect-ratio: 4 / 5; }
.style-organic { --heading: Georgia, serif; --weight: 500; --radius: 30px; }
.style-organic .hero .media { border-radius: 48% 48% var(--radius) var(--radius); }
.style-industrial { --radius: 3px; --weight: 850; }
.style-industrial .hero { border-top: 4px solid var(--accent); }
.style-industrial .card { border-top: 3px solid var(--accent); }
.style-minimal .hero:not(.has-image) { background: var(--bg); }
.style-cinematic .hero:not(.has-image) { background: linear-gradient(155deg, var(--bg) 28%, var(--wash)); }
.style-cinematic .hero:not(.has-image) > .wrap { align-items: end; }
.style-bento .hero:not(.has-image) > .wrap { min-height: 0; }
@media (max-width: 890px) {
  .top-links, .top .top-action { display: none; }
  .menu { display: block; }
  .brand { max-width: 72%; }
}
@media (max-width: 680px) {
  .hero > .wrap { min-height: 0; }
  .hero.has-image > .wrap, .block.variant-split.has-image > .wrap { grid-template-columns: 1fr; }
  .hero.variant-cover.has-image > .wrap { min-height: min(620px, 81vh); }
  .hero .media img, .block.variant-cover .media img { aspect-ratio: 4 / 3; }
  .cards, .variant-list .card:has(p) { grid-template-columns: 1fr; }
  .variant-bento .card:first-child { grid-column: auto; }
}
@media (prefers-reduced-motion: reduce) {
  html { scroll-behavior: auto; }
  *, *::before, *::after { transition: none !important; }
}
"""


def luminance(color):
    rgb = [int(color[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    return sum(w * (v / 12.92 if v <= .04045 else ((v + .055) / 1.055) ** 2.4)
               for v, w in zip(rgb, (.2126, .7152, .0722)))


def contrast(first, second):
    low, high = sorted((luminance(first), luminance(second)))
    return (high + .05) / (low + .05)


def whatsapp(phone):
    if len(phone) in (10, 11):
        phone = "55" + phone
    return "https://wa.me/" + phone if 12 <= len(phone) <= 15 else ""


def review(model):
    sections, theme = model["sections"], model["theme"]
    ratio = contrast(theme["background"], theme["text"])
    has_whatsapp = bool(whatsapp(model["phone"]))
    checks = (
        ("structure", "Abertura e contato", sections[0]["kind"] == "hero" and any(s["kind"] == "contact" for s in sections),
         "Comece com uma abertura e inclua uma seção de contato."),
        ("description", "Descrição SEO", bool(model["description"]), "Preencha a descrição em Ajustes do site."),
        ("contrast", "Contraste entre fundo e texto", ratio >= 4.5,
         f"O contraste é de {ratio:.1f}:1. Use uma combinação de pelo menos 4,5:1."),
        ("images", "Texto alternativo das imagens", all(not s["image"] or s["image_alt"] for s in sections),
         "Descreva as imagens informativas no campo Texto alternativo."),
        ("contact", "WhatsApp comercial", has_whatsapp, "Adicione um número com DDD para ativar os botões de WhatsApp."),
    )
    return [{"id": key, "label": label, "passed": passed, "hint": "" if passed else hint}
            for key, label, passed, hint in checks]


def _button(label, target, variant=""):
    if not target:
        return ""
    return f'<a class="button {variant}" href="{escape(target)}">{escape(label)}</a>'


def _variant(section, layout):
    if section["variant"] != "auto":
        return section["variant"]
    kind = section["kind"]
    if kind == "hero":
        return {"center": "center", "cinematic": "cover"}.get(layout, "split")
    if kind in ("about", "location", "contact"):
        return "split"
    if kind in ("gallery", "cta", "faq"):
        return "cover" if kind == "gallery" else "center"
    if kind == "process" or layout == "editorial":
        return "list"
    return "bento" if layout == "bento" else "grid"


def _items(section):
    items = [item for item in section["items"] if item["title"] or item["body"]]
    if not items:
        return ""
    if section["kind"] == "faq":
        entries = "".join(f'<details><summary>{escape(item["title"] or "Pergunta")}</summary><p>{escape(item["body"])}</p></details>'
                          for item in items)
        return f'<div class="faq-list">{entries}</div>'
    entries = []
    for item in items:
        title = f'<h3>{escape(item["title"])}</h3>' if item["title"] else ""
        body = f'<p>{escape(item["body"])}</p>' if item["body"] else ""
        entries.append(f'<li class="card">{title}{body}</li>')
    return f'<ul class="cards" role="list">{"".join(entries)}</ul>'


def _section(section, index, layout, action_target, action_label, next_section):
    kind = section["kind"]
    key = section["id"]
    heading = "h1" if index == 0 else "h2"
    name = escape(section["title"] or KIND_LABELS[kind])
    body = f'<p class="body">{escape(section["body"])}</p>' if section["body"] else ""
    eyebrow = f'<p class="eyebrow">{escape(section["eyebrow"])}</p>' if section["eyebrow"] else ""
    photo = ""
    if section["image"]:
        eager = 'loading="eager" fetchpriority="high"' if index == 0 else 'loading="lazy"'
        photo = f'<figure class="media"><img src="{escape(section["image"])}" alt="{escape(section["image_alt"])}" {eager} decoding="async"></figure>'
    actions = ""
    if kind in ("hero", "cta", "contact"):
        actions = _button(section["cta"] or action_label, action_target if action_target != "#" + key else "")
        if kind == "hero" and next_section and "#" + next_section != action_target:
            actions += _button("Conhecer mais", "#" + next_section, "ghost")
        actions = f'<div class="actions">{actions}</div>' if actions else ""

    mode = "hero" if kind == "hero" else f"block {kind}"
    variant = _variant(section, layout)
    extra = " has-image" if photo else ""
    intro = f'<div>{eyebrow}<{heading}>{name}</{heading}>{body}{actions}</div>'
    return f'<section id="{key}" class="{mode} variant-{variant}{extra}"><div class="wrap">{intro}{_items(section)}{photo}</div></section>'


def render_page(model, preview=False):
    theme, sections = model["theme"], model["sections"]
    title, description = escape(model["title"]), escape(model["description"])
    accent_ink = "#000000" if luminance(theme["primary"]) > .179 else "#ffffff"
    scheme = "dark" if luminance(theme["background"]) < .179 else "light"
    style = (':root{--accent:' + theme["primary"] + ';--bg:' + theme["background"] + ';--ink:' + theme["text"]
             + ';--on-accent:' + accent_ink + ';--font:"' + theme["font"] + '";--scheme:' + scheme + '}')
    if theme["font"] == "system-ui":
        style = style.replace('"system-ui"', 'system-ui')

    contact = next((section["id"] for section in sections if section["kind"] == "contact"), "")
    phone_link = whatsapp(model["phone"])
    target = (phone_link if not preview else "") or ("#" + contact if contact else "")
    label = GOALS[model["strategy"]["goal"]][1]
    start = "#" + sections[0]["id"]
    nav_links = {}
    for section in sections:
        kind = section["kind"]
        if kind not in ("hero", "cta"):
            nav_links.setdefault(kind, f'<a href="#{section["id"]}">{KIND_LABELS[kind]}</a>')
    main_links = [link for kind, link in nav_links.items() if kind != "contact"][:4]
    if contact:
        main_links.append(nav_links["contact"])
    nav = "".join(main_links)
    menus = (
        f'<nav class="top-links" aria-label="Navegação principal">{nav}</nav>'
        f'<details class="menu"><summary>Menu</summary><nav aria-label="Navegação principal">{nav}</nav></details>'
    ) if nav else ""
    parts = "".join(_section(section, i, theme["layout"], target, label,
                             sections[i + 1]["id"] if i + 1 < len(sections) else "")
                    for i, section in enumerate(sections))
    css_style = "minimal" if theme["layout"] == "center" else theme["layout"]
    return (
        '<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        '<meta name="robots" content="noindex,nofollow">'
        '<meta http-equiv="Content-Security-Policy" content="default-src \'none\'; style-src \'unsafe-inline\'; img-src data:; base-uri \'none\'; form-action \'none\'">'
        f'<title>{title}</title><meta name="description" content="{description}">'
        f'<meta property="og:type" content="website"><meta property="og:title" content="{title}">'
        f'<meta property="og:description" content="{description}"><style>{style}{CSS}</style></head>'
        f'<body class="style-{css_style}"><a class="skip button" href="#conteudo">Ir para o conteúdo</a>'
        f'<header class="top"><div class="wrap top-inner"><a class="brand" href="{start}">{title}</a>'
        f'{menus}{_button(label, target, "top-action")}</div></header>'
        f'<main id="conteudo">{parts}</main><footer class="foot"><div class="wrap"><a href="{start}">{title}</a>'
        '<span>Demonstração desenvolvida pela FLP Systems.</span></div></footer></body></html>'
    )
