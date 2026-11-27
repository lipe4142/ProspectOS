"""Site Studio: modelo de conteúdo validado e exportação estática, sem executar código da IA."""
import base64
import html
import json
import re
from io import BytesIO
from zipfile import ZipFile, ZIP_DEFLATED

FONTS = ["Arial", "Georgia", "Verdana", "Tahoma", "Trebuchet MS", "system-ui"]
TEMPLATES = {
    "solar": ("Energia solar", "#f9b233", "#142b25", "#ffffff", "split"),
    "imoveis": ("Imobiliário", "#b89562", "#172523", "#ffffff", "editorial"),
    "advocacia": ("Advocacia", "#d4b179", "#182538", "#ffffff", "editorial"),
    "engenharia": ("Engenharia", "#ff6a00", "#141820", "#ffffff", "split"),
    "saude": ("Saúde e odontologia", "#047d79", "#f4fafa", "#173b3b", "split"),
    "educacao": ("Educação", "#7144c7", "#f7f4ff", "#241c39", "center"),
    "beleza": ("Beleza e estética", "#af627c", "#fff4f5", "#39252d", "editorial"),
    "restaurante": ("Restaurante", "#d99b56", "#241810", "#fff5e8", "center"),
    "tecnologia": ("Tecnologia", "#ff6a00", "#090909", "#ffffff", "split"),
    "servicos": ("Serviços", "#145dbf", "#f4f7fb", "#16243b", "center"),
}
KINDS = ("hero", "about", "services", "gallery", "faq", "contact", "cta")


def txt(value, limit=4000):
    if not isinstance(value, str) or len(value) > limit:
        raise ValueError("Texto inválido ou acima do limite.")
    return value.strip()


def image(value):
    if not value:
        return ""
    if not isinstance(value, str) or len(value) > 1_400_000:
        raise ValueError("Imagem acima de 1 MB.")
    m = re.fullmatch(r"data:image/(png|jpeg|webp);base64,([A-Za-z0-9+/=]+)", value)
    if not m:
        raise ValueError("Use imagens PNG, JPEG ou WebP autorizadas.")
    raw = base64.b64decode(m[2], validate=True)
    from PIL import Image
    with Image.open(BytesIO(raw)) as img:
        if img.width * img.height > 16_000_000 or img.format.lower() != m[1]:
            raise ValueError("Formato ou dimensões de imagem inválidos.")
        img.verify()
    return value


def validate(model):
    if not isinstance(model, dict):
        raise ValueError("Projeto inválido.")
    theme = model.get("theme", {})
    if not isinstance(theme, dict):
        raise ValueError("Tema inválido.")
    result = {"title": txt(model.get("title", ""), 160), "description": txt(model.get("description", ""), 300),
              "phone": re.sub(r"\D", "", txt(model.get("phone", ""), 40)), "theme": {}, "sections": []}
    for k in ("primary", "background", "text"):
        v = theme.get(k)
        if not isinstance(v, str) or not re.fullmatch(r"#[0-9a-fA-F]{6}", v):
            raise ValueError("Cor inválida.")
        result["theme"][k] = v
    font = theme.get("font")
    if font not in FONTS:
        raise ValueError("Fonte não suportada.")
    result["theme"]["font"] = font
    layout = theme.get("layout", "split")
    if layout not in ("split", "editorial", "center"):
        raise ValueError("Layout inválido.")
    result["theme"]["layout"] = layout
    sections = model.get("sections")
    if not isinstance(sections, list) or not 1 <= len(sections) <= 20:
        raise ValueError("Inclua de 1 a 20 seções.")
    for item in sections:
        if not isinstance(item, dict) or item.get("kind") not in KINDS:
            raise ValueError("Componente inválido.")
        result["sections"].append({
            "kind": item["kind"], "title": txt(item.get("title", ""), 160),
            "body": txt(item.get("body", "")), "image": image(item.get("image", "")),
        })
    if len(json.dumps(result)) > 8_000_000:
        raise ValueError("Projeto excede 8 MB.")
    if not result["title"]:
        raise ValueError("Informe o título do site.")
    return result


def starter(name, phone="", template="servicos"):
    _, primary, background, text, layout = TEMPLATES[template]
    return validate({"title": name, "description": "", "phone": phone,
                     "theme": {"primary": primary, "background": background, "text": text, "font": "system-ui", "layout": layout},
                     "sections": [{"kind": "hero", "title": name, "body": "Conheça nossa empresa.", "image": ""},
                                  {"kind": "contact", "title": "Entre em contato", "body": "", "image": ""}]})


def render(model, preview=False):
    m = validate(model)
    e = html.escape
    t = m["theme"]
    phone = m["phone"]
    if len(phone) in (10, 11):
        phone = "55" + phone
    cta = ('<a class="cta" href="https://wa.me/' + phone + '">Fale pelo WhatsApp</a>') if not preview and 12 <= len(phone) <= 15 else ""
    nav = "".join('<a href="#s%d">%s</a>' % (i, e(s["title"])) for i, s in enumerate(m["sections"]) if s["title"])
    parts = []
    for i, s in enumerate(m["sections"]):
        heading = "h1" if i == 0 else "h2"
        pic = '<img alt="" loading="lazy" src="' + e(s["image"], quote=True) + '">' if s["image"] else ""
        parts.append(f'<section id="s{i}" class="{s["kind"]}"><div><{heading}>{e(s["title"])}</{heading}><p>{e(s["body"])}</p>{cta if s["kind"] in ("hero","contact","cta") else ""}</div>{pic}</section>')
    css = f":root{{--primary:{t['primary']};--bg:{t['background']};--text:{t['text']};font-family:{t['font']},sans-serif}}"
    css += """
*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;background:var(--bg);color:var(--text)}
header,main,footer{max-width:1320px;margin:auto;padding:24px clamp(20px,6vw,96px)}header{display:flex;align-items:center;gap:24px;justify-content:space-between;flex-wrap:wrap;border-bottom:1px solid color-mix(in srgb,var(--text) 15%,transparent)}
nav{display:flex;gap:16px;flex-wrap:wrap}a{color:inherit;text-decoration:none}a:focus-visible{outline:3px solid var(--primary);outline-offset:5px}
section{padding:clamp(40px,8vw,110px) 0;border-bottom:1px solid color-mix(in srgb,var(--text) 15%,transparent);display:grid;gap:32px;align-items:center}
section:has(img){grid-template-columns:1fr 1fr}h1,h2{margin:0 0 20px;line-height:1.05;letter-spacing:-.04em}h1{font-size:clamp(42px,7vw,100px)}h2{font-size:clamp(28px,4vw,58px)}
p{white-space:pre-line;line-height:1.75;max-width:64ch;font-size:clamp(16px,1.4vw,21px)}img{width:100%;max-height:560px;object-fit:cover;border-radius:20px}
.hero{min-height:58vh;border-top:4px solid var(--primary)}.cta{display:inline-block;padding:15px 24px;border:2px solid var(--primary);border-radius:999px;font-weight:700;transition:transform .2s}
.cta:hover{transform:translateY(-3px)}.center section{text-align:center;grid-template-columns:1fr}.center p{margin-inline:auto}.editorial section:nth-child(even):has(img)>img{order:-1}
footer{font-size:13px;opacity:.8}@media(max-width:720px){section:has(img){grid-template-columns:1fr}.editorial section:nth-child(even):has(img)>img{order:0}}
@media(prefers-reduced-motion:reduce){*{scroll-behavior:auto!important;transition:none!important}}
"""
    return ('<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            '<meta name="robots" content="noindex,nofollow"><meta http-equiv="Content-Security-Policy" content="default-src \\'none\\'; style-src \\'unsafe-inline\\'; img-src data:; base-uri \\'none\\'; form-action \\'none\\'">'
            '<title>' + e(m["title"]) + '</title><meta name="description" content="' + e(m["description"], quote=True) + '"><style>' + css +
            '</style></head><body class="' + t["layout"] + '"><header><strong>' + e(m["title"]) + '</strong><nav>' + nav +
            '</nav></header><main>' + "".join(parts) + '</main><footer>Projeto demonstrativo desenvolvido pela FLP Systems.</footer></body></html>')


def files(model):
    return {"index.html": render(model).encode("utf-8"),
            "robots.txt": b"User-agent: *\nAllow: /\n",
            "_headers": b"/*\n  X-Robots-Tag: noindex, nofollow\n  X-Content-Type-Options: nosniff\n"}


def export_zip(model):
    stream = BytesIO()
    with ZipFile(stream, "w", ZIP_DEFLATED) as z:
        for name, body in files(model).items():
            z.writestr(name, body)
        z.writestr("README.txt", "Abra index.html ou publique os arquivos em hospedagem estática. Demonstração não oficial; revise os dados antes de divulgar.")
    stream.seek(0)
    return stream
