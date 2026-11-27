"""Modelo validado, planejamento e exportação estática do Site Studio."""

import base64
import binascii
import json
import re
from io import BytesIO
from zipfile import ZipFile, ZIP_DEFLATED

from studio_design import (
    APPEARANCES, DEPTHS, GOALS, ITEM_KINDS, KIND_LABELS, KIND_VARIANTS, STYLES, TEMPLATES,
    planned_sections, theme_for,
)
from studio_render import render_page, review

FONTS = ["Arial", "Georgia", "Verdana", "Tahoma", "Trebuchet MS", "system-ui"]
KINDS = tuple(KIND_LABELS)
SECTION_ID = re.compile(r"[a-z0-9][a-z0-9-]{0,47}")


def txt(value, limit=4000):
    if not isinstance(value, str) or len(value) > limit:
        raise ValueError("Texto inválido ou acima do limite.")
    return value.strip()


def choice(value, allowed, label):
    if not isinstance(value, str) or value not in allowed:
        raise ValueError(f"{label} inválido.")
    return value


def image(value):
    if not value:
        return ""
    if not isinstance(value, str) or len(value) > 1_400_000:
        raise ValueError("Imagem acima de 1 MB.")
    match = re.fullmatch(r"data:image/(png|jpeg|webp);base64,([A-Za-z0-9+/=]+)", value)
    if not match:
        raise ValueError("Use imagens PNG, JPEG ou WebP autorizadas.")
    from PIL import Image

    try:
        raw = base64.b64decode(match[2], validate=True)
        with Image.open(BytesIO(raw)) as img:
            if img.width * img.height > 16_000_000 or (img.format or "").lower() != match[1]:
                raise ValueError("Formato ou dimensões de imagem inválidos.")
            img.verify()
    except (binascii.Error, OSError, Image.DecompressionBombError, SyntaxError) as exc:
        raise ValueError("A imagem está corrompida ou tem dimensões inválidas.") from exc
    return value


def _theme(value):
    if not isinstance(value, dict):
        raise ValueError("Tema inválido.")
    colors = {key: value.get(key) for key in ("primary", "background", "text")}
    if any(not isinstance(color, str) or not re.fullmatch(r"#[0-9a-fA-F]{6}", color) for color in colors.values()):
        raise ValueError("Cor inválida.")
    return {
        **colors,
        "font": choice(value.get("font"), FONTS, "Fonte"),
        "layout": choice(value.get("layout", "split"), STYLES, "Layout"),
        "appearance": choice(value.get("appearance", "custom"), (*APPEARANCES, "custom"), "Tema"),
    }


def _section_items(value):
    if not isinstance(value, list) or len(value) > 8 or any(not isinstance(item, dict) for item in value):
        raise ValueError("Inclua até 8 itens por seção.")
    return [{"title": txt(item.get("title", ""), 120), "body": txt(item.get("body", ""), 500)} for item in value]


def _sections(values):
    if not isinstance(values, list) or not 1 <= len(values) <= 20:
        raise ValueError("Inclua de 1 a 20 seções.")
    explicit = set()
    for section in values:
        if not isinstance(section, dict):
            raise ValueError("Seção inválida.")
        if "id" in section:
            key = section["id"]
            if not isinstance(key, str) or not SECTION_ID.fullmatch(key) or key in explicit or key == "conteudo":
                raise ValueError("Identificador de seção inválido ou repetido.")
            explicit.add(key)

    result = []
    for index, section in enumerate(values):
        kind = choice(section.get("kind"), KINDS, "Componente")
        default_id = f"s{index}"
        suffix = 1
        while default_id in explicit:
            default_id = f"s{index}-{suffix}"
            suffix += 1
        result.append({
            "id": section.get("id", default_id), "kind": kind,
            "title": txt(section.get("title", ""), 160), "body": txt(section.get("body", "")),
            "eyebrow": txt(section.get("eyebrow", ""), 80), "cta": txt(section.get("cta", ""), 64),
            "image": image(section.get("image", "")), "image_alt": txt(section.get("image_alt", ""), 160),
            "variant": choice(section.get("variant", "auto"), KIND_VARIANTS[kind], "Composição"),
            "items": _section_items(section.get("items", [])) if kind in ITEM_KINDS else [],
        })
    return result


def validate(model):
    if not isinstance(model, dict):
        raise ValueError("Projeto inválido.")
    strategy = model.get("strategy", {})
    if not isinstance(strategy, dict):
        raise ValueError("Estratégia inválida.")
    result = {
        "title": txt(model.get("title", ""), 160), "description": txt(model.get("description", ""), 300),
        "phone": re.sub(r"[^0-9]", "", txt(model.get("phone", ""), 40)),
        "theme": _theme(model.get("theme")),
        "strategy": {
            "goal": choice(strategy.get("goal", "contact"), GOALS, "Objetivo"),
            "depth": choice(strategy.get("depth", "full"), DEPTHS, "Estrutura"),
        },
        "sections": _sections(model.get("sections")),
    }
    if not result["title"]:
        raise ValueError("Informe o título do site.")
    if len(json.dumps(result)) > 8_000_000:
        raise ValueError("Projeto excede 8 MB.")
    return result


def starter(name, phone="", template="servicos", *, goal="auto", depth="full",
            appearance="template", briefing="", address=""):
    template = choice(template, TEMPLATES, "Modelo")
    goal = TEMPLATES[template].goal if goal == "auto" else choice(goal, GOALS, "Objetivo")
    depth = choice(depth, DEPTHS, "Estrutura")
    appearance = choice(appearance, APPEARANCES, "Tema")
    description, sections = planned_sections(name, template, goal, depth, briefing, address)
    return validate({
        "title": name, "description": description, "phone": phone, "theme": theme_for(template, appearance),
        "strategy": {"goal": goal, "depth": depth}, "sections": sections,
    })


def preview(model, source=False):
    validated = validate(model)
    return {"html": render_page(validated, preview=not source), "checks": review(validated)}


def render(model, preview=False):
    return render_page(validate(model), preview=preview)


def files(model):
    return {
        "index.html": render(model).encode("utf-8"),
        "robots.txt": b"User-agent: *\nAllow: /\n",
        "_headers": b"/*\n  X-Robots-Tag: noindex, nofollow\n  X-Content-Type-Options: nosniff\n",
    }


def export_zip(model):
    stream = BytesIO()
    with ZipFile(stream, "w", ZIP_DEFLATED) as archive:
        for name, body in files(model).items():
            archive.writestr(name, body)
        archive.writestr("README.txt", "Abra index.html ou publique os arquivos em hospedagem estática. Demonstração não oficial. Revise os dados antes de divulgar.")
    stream.seek(0)
    return stream
