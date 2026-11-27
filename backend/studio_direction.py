"""Análise local, sem inventar fatos nem consultar páginas externas."""
import re
import unicodedata

PROFILES = {
    "advocacia": (r"advocacia|advogad[oa]|juridic[oa]|escritorio de direito", "law books legal office", "Institucional, sóbrio e informativo; não prometa resultados.", "luxury", "split"),
    "solar": (r"energia solar|fotovoltaic|painel solar", "solar panels roof", "Tecnologia, energia e eficiência sem inventar percentuais.", "industrial", "cover"),
    "imoveis": (r"imobiliari|corretor de imoveis|imoveis", "modern house architecture", "Fotografia arquitetônica e informação verificável.", "editorial", "cover"),
    "arquitetura": (r"arquitet|interiores", "minimalist architecture interior", "Editorial, espaço negativo e fotografia.", "editorial", "split"),
    "engenharia": (r"engenhari|construtora|construcao civil", "modern construction engineering", "Precisão, portfólio autorizado e clareza.", "industrial", "split"),
    "saude": (r"odontolog|dentista", "dental clinic interior", "Acolhimento, clareza e sem promessas clínicas.", "organic", "split"),
    "clinica": (r"clinica|medic[oa]|fisioterap|psicolog", "medical clinic interior", "Acolhimento e linguagem informativa.", "organic", "split"),
    "barbearia": (r"barbearia|barbeiro", "barber shop interior", "Cinematográfico e textura.", "cinematic", "cover"),
    "beleza": (r"estetica|beleza|salao", "beauty salon interior", "Editorial delicado e acolhedor.", "organic", "split"),
    "confeitaria": (r"confeitar|doceria|bolos", "artisan cake pastry", "Fotografia de produto, paleta delicada.", "luxury", "split"),
    "restaurante": (r"restaurante|hamburguer|pizzari|lanchonete", "restaurant food burger", "Produto protagonista e hierarquia forte.", "brutalist", "cover"),
    "educacao": (r"faculdade|universit|curso|ensino|escola", "modern classroom books", "Clareza, confiança e navegação simples.", "bento", "split"),
    "tecnologia": (r"software|tecnologia|informatica|desenvolvimento de sistemas", "computer workspace technology", "Contemporâneo, modular e técnico.", "bento", "split"),
    "produtora": (r"produtora|audiovisual|filmagem", "film studio camera", "Expressivo e cinematográfico.", "brutalist", "cover"),
    "tatuagem": (r"tatuagem|tattoo", "tattoo studio interior", "Expressivo e editorial.", "brutalist", "split"),
    "academia": (r"academia|musculacao|fitness", "gym fitness equipment", "Contraste, energia e foco no serviço.", "industrial", "cover"),
    "oficina": (r"oficina|mecanica automotiva", "auto repair workshop", "Industrial e técnico.", "industrial", "split"),
    "loja": (r"\bloja\b|varejo|comercio", "retail store interior", "Produto protagonista e organização.", "bento", "split"),
}

def normalize(text):
    return unicodedata.normalize("NFKD",str(text or "")).encode("ascii","ignore").decode().lower()

def analyze(name, category="", niche="", briefing="", preferred="auto"):
    fields = [normalize(category),normalize(niche),normalize(name),normalize(briefing)]
    matches = [(k, sum(weight for value,weight in zip(fields,(5,4,4,1)) if re.search(v[0],value))) for k,v in PROFILES.items()]
    inferred,score = max(matches,key=lambda pair:pair[1])
    if not score:
        inferred = "servicos"
    chosen = inferred if preferred == "auto" else preferred
    profile = PROFILES.get(chosen, ("","professional office interior","Composição limpa, tipografia forte e foco no contato.","split","split"))
    return {"template":chosen,"inferred":inferred,"confidence":"indício forte" if score>=4 else "indício fraco" if score else "não identificado",
            "photo_query":profile[1],"direction":profile[2],"style":profile[3],"hero_variant":profile[4]}
