"""Site Studio: modelo de conteúdo validado e exportação estática, sem executar código da IA."""
import base64
import html
import json
import re
from io import BytesIO
from zipfile import ZipFile, ZIP_DEFLATED
import studio_premium as premium

FONTS = ["Arial", "Georgia", "Verdana", "Tahoma", "Trebuchet MS", "system-ui"]
TEMPLATES = {
    "solar": ("Energia solar", "#f5b728", "#10251f", "#f5f7eb", "industrial"),
    "imoveis": ("Imobiliário", "#ae8c61", "#f0ede6", "#272d26", "editorial"),
    "advocacia": ("Advocacia", "#d4b179", "#182538", "#ffffff", "luxury"),
    "engenharia": ("Engenharia", "#ff7936", "#141820", "#ffffff", "industrial"),
    "saude": ("Saúde e odontologia", "#047d79", "#f4fafa", "#173b3b", "bento"),
    "educacao": ("Educação", "#7144c7", "#f7f4ff", "#241c39", "bento"),
    "beleza": ("Beleza e estética", "#a44b68", "#fff4f5", "#39252d", "organic"),
    "restaurante": ("Restaurante", "#db3e29", "#fff0e8", "#261813", "brutalist"),
    "tecnologia": ("Tecnologia", "#ff6a00", "#090909", "#ffffff", "bento"),
    "servicos": ("Serviços", "#145dbf", "#f4f7fb", "#16243b", "split"),
    "barbearia": ("Barbearia", "#bf4035", "#161616", "#f5f1e8", "cinematic"),
    "arquitetura": ("Arquitetura", "#a38b71", "#efebe4", "#34332d", "editorial"),
    "produtora": ("Produtora audiovisual", "#c6ee45", "#111111", "#f8f8f8", "brutalist"),
    "tatuagem": ("Estúdio de tatuagem", "#e14c3d", "#f4efe5", "#141414", "brutalist"),
    "confeitaria": ("Confeitaria", "#ac765b", "#fff9f1", "#33231e", "luxury"),
    "academia": ("Academia", "#cdeb36", "#101214", "#ffffff", "industrial"),
    "oficina": ("Oficina mecânica", "#eb612b", "#161a1d", "#ffffff", "industrial"),
    "loja": ("Loja e catálogo", "#3b5eaa", "#f7f5ef", "#1c222b", "bento"),
    "escola": ("Escola", "#285fbc", "#fff9ed", "#233047", "organic"),
    "clinica": ("Clínica", "#267f71", "#f5faf7", "#17372f", "center"),
}
KINDS = tuple(premium.LABELS)
STYLES = premium.STYLES
VARIANTS = premium.VARIANTS



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
    if layout not in STYLES:
        raise ValueError("Layout inválido.")
    result["theme"]["layout"] = layout
    sections = model.get("sections")
    if not isinstance(sections, list) or not 1 <= len(sections) <= 20:
        raise ValueError("Inclua de 1 a 20 seções.")
    for item in sections:
        if not isinstance(item, dict) or item.get("kind") not in KINDS:
            raise ValueError("Componente inválido.")
        variant = item.get("variant", "auto")
        if variant not in VARIANTS:
            raise ValueError("Composição inválida.")
        items = item.get("items", [])
        if not isinstance(items, list) or len(items) > 12 or any(not isinstance(x,dict) for x in items):
            raise ValueError("Lista de componentes inválida.")
        source = txt(item.get("image_source", ""), 200)
        if source and not re.fullmatch(r"https://www\.pexels\.com/photo/[0-9]+/",source):
            raise ValueError("Fonte de imagem inválida.")
        result["sections"].append({
            "kind": item["kind"], "title": txt(item.get("title", ""), 160),
            "body": txt(item.get("body", "")), "image": image(item.get("image", "")),
            "eyebrow": txt(item.get("eyebrow", ""), 100), "cta": txt(item.get("cta", ""), 60),
            "image_alt": txt(item.get("image_alt", ""), 200), "variant": variant,
            "image_source": source, "image_credit": txt(item.get("image_credit", ""), 100),
            "items": [{"title": txt(x.get("title", ""), 160), "body": txt(x.get("body", ""), 500)} for x in items],
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
                     "sections": [{"kind": "hero", "title": name, "body": "Conheça nossa empresa.", "image": "", "eyebrow": TEMPLATES[template][0]},
                                  {"kind": "about", "title": "Conheça a empresa", "body": "Apresentação a ser personalizada com as informações confirmadas da empresa.", "image": ""},
                                  {"kind": "contact", "title": "Vamos conversar?", "body": "", "image": ""}]})


def render(model, preview=False):
    return premium.render(validate(model), preview=preview)


def quality(model):
    """Diagnóstico heurístico, não substitui teste visual nem aprovação humana."""
    m = validate(model)
    sections = m["sections"]
    checks = [
        ("Abertura clara", sum(s["kind"] == "hero" for s in sections)==1 and bool(sections[0]["title"]) and sections[0]["kind"]=="hero"),
        ("Estrutura completa", len(sections)>=5 and len({s["kind"] for s in sections})>=4),
        ("Imagem principal autorizada", bool(sections[0]["image"])),
        ("Descrição SEO", len(m["description"])>=40),
        ("Canal comercial informado", 10<=len(m["phone"])<=15),
        ("Textos preenchidos", all(s["title"] and (s["body"] or s["items"]) for s in sections)),
        ("Conteúdo sem instruções de edição", not any("a ser personalizada" in s["body"].lower() or "a confirmar" in s["body"].lower() for s in sections)),
        ("Texto alternativo das imagens", all(not s["image"] or s["image_alt"] for s in sections)),
    ]
    return [{"label": label, "passed": passed} for label, passed in checks]


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
