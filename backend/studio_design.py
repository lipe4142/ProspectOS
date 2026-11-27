"""Catálogo e composição inicial de páginas do Site Studio."""

import re
import unicodedata
from typing import NamedTuple


class Template(NamedTuple):
    label: str
    primary: str
    background: str
    text: str
    layout: str
    goal: str
    keywords: str = ""


STYLES = {
    "split": "Contemporâneo",
    "editorial": "Editorial",
    "center": "Minimalista",
    "cinematic": "Cinematográfico",
    "industrial": "Industrial",
    "organic": "Orgânico",
    "bento": "Modular",
}
TEMPLATES = {
    "servicos": Template("Serviços", "#145dbf", "#f4f7fb", "#16243b", "split", "quote"),
    "solar": Template("Energia solar", "#f9b233", "#142b25", "#ffffff", "industrial", "quote", r"energia solar|fotovoltaic|paineis solares"),
    "imoveis": Template("Imobiliário", "#b89562", "#172523", "#ffffff", "editorial", "showcase", r"imobiliari|\bimove[il]s?\b|corretor de imoveis"),
    "advocacia": Template("Advocacia", "#af804b", "#f6f2eb", "#25231f", "editorial", "contact", r"advoca|\bjuridic"),
    "arquitetura": Template("Arquitetura e interiores", "#9f613f", "#f4eee5", "#2c2722", "editorial", "showcase", r"arquitet|design de interiores"),
    "engenharia": Template("Engenharia", "#ff8638", "#141820", "#f2f3f8", "industrial", "quote", r"engenhari|construtora|construcao civil"),
    "saude": Template("Saúde e odontologia", "#047d79", "#f4fafa", "#173b3b", "organic", "booking", r"odontolog|dentista|saude|clinica|fisioterap|psicolog"),
    "educacao": Template("Educação", "#7144c7", "#f7f4ff", "#241c39", "center", "contact", r"\bescola|faculdade|educa|ensino|universidade"),
    "beleza": Template("Beleza e estética", "#a44969", "#fff4f5", "#39252d", "organic", "booking", r"estetica|beleza|salao|barbearia"),
    "restaurante": Template("Restaurante", "#e7aa66", "#241810", "#fff5e8", "cinematic", "contact", r"restauran|hamburguer|pizzari|lanchonete|confeitaria|cardapio"),
    "tecnologia": Template("Tecnologia", "#9e9bff", "#19172a", "#f6f5ff", "bento", "quote", r"tecnolog|software|informatica|\bsaas\b"),
    "loja": Template("Varejo e produtos", "#d35121", "#fbf3ec", "#321f19", "bento", "contact", r"\bloja\b|varejo|boutique"),
    "oficina": Template("Oficina automotiva", "#ffd150", "#262321", "#f8f2ea", "industrial", "quote", r"\boficina\b|mecanica automotiva"),
}
GOALS = {
    "contact": ("Receber contatos", "Fale com a equipe"),
    "quote": ("Solicitar orçamentos", "Solicitar orçamento"),
    "booking": ("Receber agendamentos", "Solicitar agendamento"),
    "showcase": ("Apresentar portfólio", "Falar sobre um projeto"),
}
DEPTHS = {"compact": "Essencial", "full": "Completa"}
APPEARANCES = {"template": "Do modelo", "light": "Claro", "dark": "Escuro"}
PALETTES = {
    "light": {"background": "#f8f7f4", "text": "#222127"},
    "dark": {"background": "#17181d", "text": "#f5f3ef"},
}
KIND_LABELS = {
    "hero": "Abertura", "about": "Sobre", "services": "Serviços", "gallery": "Galeria",
    "faq": "Perguntas frequentes", "contact": "Contato", "cta": "Chamada para ação",
    "benefits": "Diferenciais", "process": "Como funciona", "products": "Produtos",
    "location": "Localização",
}
VARIANTS = {
    "auto": "Automática", "split": "Texto e imagem", "center": "Centralizada",
    "cover": "Imagem de capa", "grid": "Grade", "list": "Lista", "bento": "Grade assimétrica",
}
ITEM_KINDS = ("services", "benefits", "process", "products", "faq")
KIND_VARIANTS = {
    "hero": ("auto", "split", "center", "cover"),
    "about": ("auto", "split", "center"),
    "gallery": ("auto", "cover", "split"),
    "faq": ("auto", "center"),
    "contact": ("auto", "split", "center"),
    "cta": ("auto", "split", "center"),
    "location": ("auto", "split", "center"),
    **{kind: ("auto", "grid", "list", "bento") for kind in ITEM_KINDS if kind != "faq"},
}

COMPOSITIONS = {
    "contact": ("about", "offer", "faq", "location"),
    "quote": ("offer", "process", "benefits", "faq"),
    "booking": ("offer", "about", "process", "location"),
    "showcase": ("gallery", "offer", "about", "process"),
}


def normalized(text):
    return "".join(c for c in unicodedata.normalize("NFKD", text.lower()) if not unicodedata.combining(c))


def infer_template(name, briefing, lead=None):
    lead = lead or {}
    fields = (
        (normalized(str(lead.get("categoria") or "")), 6),
        (normalized(str(lead.get("nicho") or "")), 5),
        (normalized(name), 4),
        (normalized(briefing), 1),
    )

    def score(template):
        return sum(weight for text, weight in fields if re.search(template.keywords, text)) if template.keywords else 0

    return max(TEMPLATES, key=lambda key: score(TEMPLATES[key]))


def theme_for(template, appearance):
    profile = TEMPLATES[template]
    palette = PALETTES.get(appearance, {"background": profile.background, "text": profile.text})
    return {"primary": profile.primary, **palette, "font": "system-ui",
            "layout": profile.layout, "appearance": appearance}


def briefing_fields(briefing):
    fields = {}
    for line in briefing.splitlines():
        label, separator, value = line.strip(" -•\t").partition(":")
        if separator and value.strip():
            fields.setdefault(normalized(label), value.strip())
    return fields


def planned_sections(name, template, goal, depth, briefing, address):
    fields = briefing_fields(briefing)
    description = (fields.get("descricao") or fields.get("sobre") or "")[:300]
    address = (address or fields.get("endereco", ""))[:4000]
    offer = "products" if template in ("restaurante", "loja") else "services"
    offer_title = {
        "restaurante": "Cardápio", "advocacia": "Áreas de atuação", "saude": "Especialidades",
        "imoveis": "Imóveis e atendimento",
    }.get(template, KIND_LABELS[offer])
    cta = GOALS[goal][1]
    sections = {
        "hero": {"title": name, "body": description or "Conheça a empresa e encontre o próximo passo para o que você precisa.", "cta": cta},
        "about": {"title": "Sobre a empresa", "body": description or f"Conheça a proposta de {name} e tire suas dúvidas com a equipe."},
        offer: {"title": offer_title, "body": "Consulte a equipe para saber quais opções estão disponíveis."},
        "benefits": {"title": "O que avaliar antes de decidir", "body": "Converse com a equipe sobre as opções e o que faz sentido para sua necessidade."},
        "process": {"title": "Próximos passos", "items": [
            {"title": "Conte o que precisa", "body": "Compartilhe dúvidas, contexto e preferências no primeiro contato."},
            {"title": "Confirme os detalhes", "body": "Consulte disponibilidade e combine os próximos passos com a equipe."},
        ]},
        "gallery": {"title": "Portfólio", "body": "Peça à equipe exemplos relacionados ao seu projeto."},
        "faq": {"title": "Perguntas frequentes", "items": [
            {"title": "Como posso tirar dúvidas?", "body": "Consulte a seção de contato para falar com a equipe."},
            {"title": "Onde posso confirmar a disponibilidade?", "body": "Informe à equipe o que você procura para consultar as opções."},
        ]},
        "location": {"title": "Localização", "body": address or "Confirme o endereço e a disponibilidade antes de visitar."},
        "cta": {"title": "Vamos conversar?", "body": "Fale com a equipe para confirmar detalhes e combinar o próximo passo.", "cta": cta},
        "contact": {"title": "Entre em contato", "body": address or "Envie sua dúvida ou diga à equipe como ela pode ajudar.", "cta": cta},
    }
    for kind, labels in ((offer, ("cardapio", "produtos") if offer == "products" else ("servicos", "especialidades", "areas de atuacao")),
                         ("benefits", ("diferenciais",))):
        recorded = next((fields[label] for label in labels if label in fields), "")
        if recorded:
            values = re.split(r"\s*[;|]\s*|,\s+", recorded)
            sections[kind]["items"] = [{"title": value[:120], "body": ""} for value in values[:8] if value]
            sections[kind]["body"] = ""

    middle = COMPOSITIONS[goal][:2] if depth == "compact" else COMPOSITIONS[goal]
    outline = ["hero", *middle]
    if depth == "full":
        if address and "location" not in outline:
            outline.append("location")
        outline.append("cta")
    outline.append("contact")
    return description, [{"kind": kind if kind != "offer" else offer, **sections[kind if kind != "offer" else offer]}
                         for kind in outline]
