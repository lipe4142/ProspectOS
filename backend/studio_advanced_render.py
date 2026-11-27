"""Compilador de experiência estática; módulos originais e JS fixo."""
import base64
import html
import io
import json
import zipfile
from pathlib import Path
from studio_advanced import MEDIA

def e(x): return html.escape(str(x),quote=True)

def compile_site(plan,assets,preview=False):
    root=Path(__file__).parent
    css=(root/"studio_runtime.css").read_text(encoding="utf-8")
    js=(root/"studio_runtime.js").read_text(encoding="utf-8")
    def url(name):
        if name not in assets: return ""
        if preview:
            return "data:"+MEDIA[Path(name).suffix.lower()]+";base64,"+base64.b64encode(assets[name]).decode("ascii")
        return "media/"+name
    def image(name,alt,extra=""):
        src=url(name)
        return '<img loading="lazy" src="'+e(src)+'" alt="'+e(alt)+'" '+extra+'>' if src else '<div class="missing">Mídia pendente: '+e(name)+'</div>'
    def section(id,title,body,kicker=""):
        return '<section id="'+id+'" class="block"><div class="wrap"><p class="eyebrow">'+e(kicker or plan["title"])+'</p><h2>'+e(title)+'</h2>'+body+'</div></section>'
    def grid(items):
        return '<div class="grid">'+''.join('<article class="card reveal"><span class="index">'+str(i+1).zfill(2)+'</span><h3>'+e(t)+'</h3><p>'+e(d)+'</p></article>' for i,(t,d) in enumerate(items))+'</div>'
    def photos(items):
        return '<div class="photo-grid">'+''.join('<figure class="reveal">'+image(n,t)+'<figcaption>'+e(t)+' · Referência ilustrativa</figcaption></figure>' for n,t in items)+'</div>'
    features=set(plan["features"])
    solar=plan["solar"]
    blocks=[]
    name=e(plan["title"])
    nav=[("solutions","Soluções"),("technology","Tecnologia"),("gallery","Galeria"),("calculator","Simulador"),("contact","Contato")]
    nav=[(k,t) for k,t in nav if {"solutions":"cards","technology":"engineering","gallery":"gallery","calculator":"calculator","contact":"form"}[k] in features]
    links="".join('<a href="#'+k+'">'+t+'</a>' for k,t in nav)
    logo=next((n for n in assets if "logo" in n.lower() and MEDIA[Path(n).suffix.lower()].startswith("image/")),None)
    brand='<img class="logo" src="'+e(url(logo))+'" alt="'+name+'">' if logo else name
    header='<header class="header"><a class="brand" href="#home">'+brand+'</a><nav>'+links+'</nav><details class="mobile"><summary aria-label="Menu">☰</summary><nav>'+links+'</nav></details></header>'
    poster=url("hero-poster.jpg")
    video=url("solar.mp4")
    media=((image("hero-poster.jpg","Imagem de abertura") if poster else "")+'<video id="hero-video" muted playsinline preload="metadata" poster="'+e(poster)+'" src="'+e(video)+'"></video>') if video and "video" in features else (image("hero-poster.jpg","Imagem de abertura") if poster else "")
    hero='<div id="home" class="hero-track'+(" scrub" if video and "video" in features else "")+'"><div class="hero">'+media+'<div class="shade"></div><div class="hero-content"><p class="eyebrow">'+("O FUTURO NASCE DO SOL" if solar else name)+'</p><h1>'+e(plan["headline"])+'</h1><p>'+e(plan["description"])+'</p><div class="buttons">'+(' <a class="button" href="#'+nav[0][0]+'">Explore as soluções ↗</a>' if nav else "")+'</div><small class="scroll-hint">Role para descobrir ↓</small></div></div></div>'
    if "scenes" in features:
        titles=["Sua casa, sua energia","O potencial de cada telhado","Energia integrada à arquitetura","O primeiro raio de sol","Captação em grande escala","Conforto depois do anoitecer","Inversores inteligentes","Monitoramento em suas mãos"] if solar else ["Cena "+str(i+1) for i in range(8)]
        scenes=[]
        for i,t in enumerate(titles):
            scenes.append('<article class="scene scene-'+str(i)+'" aria-hidden="'+("false" if i==0 else "true")+'">'+image("hero-main"+str(i)+".jpeg",t)+'<div class="shade"></div><div class="scene-copy"><p class="eyebrow">'+str(i+1).zfill(2)+' / 08</p><h2>'+e(t)+'</h2></div></article>')
        blocks.append('<section class="scene-track"><div class="scene-stage">'+''.join(scenes)+'<div class="progress" aria-hidden="true"><span></span></div></div></section>')
    steps=[("Captar","Transformação da luz solar em eletricidade."),("Armazenar","Armazenamento opcional em baterias compatíveis."),("Monitorar","Acompanhamento da geração e do consumo."),("Distribuir","Conversão e distribuição da energia."),("Manter","Inspeção e manutenção preventiva."),("Expandir","Dimensionamento para diferentes imóveis.")]
    if "opposed" in features:
        cols=[[],[]]
        for i,(t,d) in enumerate(steps if solar else [("Etapa "+str(i+1),"") for i in range(6)]):
            cols[i%2].append('<article class="split-card">'+image("split-"+str(i+1)+".jpeg",t)+'<span class="index">'+str(i+1).zfill(2)+'</span><h3>'+e(t)+'</h3><p>'+e(d)+'</p></article>')
        blocks.append(section("process","Energia em movimento" if solar else "Nosso processo",'<div class="opposed"><div>'+''.join(cols[0])+'</div><div>'+''.join(cols[1])+'</div></div>'))
    if "cards" in features:
        blocks.append(section("solutions","Quatro movimentos de um único sistema." if solar else "Nossas soluções",grid([steps[i] for i in (0,1,2,4)] if solar else [("Solução","Informações a confirmar.")]),"SOLUÇÕES INTEGRADAS"))
    if "engineering" in features:
        blocks.append(section("technology","A luz chega. A energia flui." if solar else "Tecnologia e inovação",'<div class="engineering"><div class="sticky"><h3>Precisão e tecnologia</h3><p>Conheça os componentes e as possibilidades.</p></div>'+photos([("engineer.jpg","Engenharia"),("floating-solar.jpg","Energia solar flutuante"),("storage.jpg","Armazenamento"),("solar-macro.jpg","Tecnologia fotovoltaica")])+'</div>'))
    if "gallery" in features:
        names=[n for n in assets if n.startswith("hero-main") or n.startswith("gallery") or n in ("floating-solar.jpg","solar-macro.jpg")]
        if not names: names=["hero-main"+str(i)+".jpeg" for i in range(6)]
        gallery=''.join('<button class="gallery-item reveal" type="button" '+('data-gallery="true"' if n in assets else 'disabled')+'>'+image(n,"Referência visual "+str(i+1))+'<span>Referência '+str(i+1).zfill(2)+'</span></button>' for i,n in enumerate(names[:24]))
        blocks.append(section("gallery","Energia em imagens." if solar else "Galeria de inspiração",'<div class="bento">'+gallery+'</div><dialog id="lightbox"><button type="button" data-close aria-label="Fechar">✕</button><button type="button" data-prev aria-label="Anterior">←</button><img alt="Referência ilustrativa"><button type="button" data-next aria-label="Próxima">→</button></dialog>'))
    if "stats" in features:
        stats=[(3,"Áreas de atuação"),(4,"Etapas de planejamento"),(6,"Referências visuais"),(2,"Cenários dia e noite")] if solar else []
        blocks.append(section("impact","Indicadores da demonstração",'<div class="grid">'+''.join('<article class="card"><strong class="counter" data-count="'+str(n)+'">'+str(n).zfill(2)+'</strong><p>'+e(t)+'</p></article>' for n,t in stats)+'</div>'))
    if "calculator" in features:
        blocks.append(section("calculator","Quanto você pode economizar?",'''<form id="solar-calc" class="calculator"><div class="fields"><label>Conta mensal (R$)<input name="bill" type="number" min="0" step=".01" required placeholder="0,00"></label><label>Consumo mensal (kWh)<input name="kwh" type="number" min="1" step="1" required></label><label>Ligação<select name="connection"><option value="30">Monofásica (30 kWh)</option><option value="50">Bifásica (50 kWh)</option><option value="100">Trifásica (100 kWh)</option></select></label><label>Cobertura solar (%) <output data-range="coverage">80</output><input name="coverage" type="range" min="0" max="100" value="80"></label><label>Autoconsumo (%) <output data-range="self">40</output><input name="self" type="range" min="0" max="100" value="40"></label><label>Tarifa efetiva (R$/kWh)<input name="rate" type="number" min=".01" step=".0001" required placeholder="Consulte tarifa oficial"></label><label>Parcela não compensável (R$/kWh)<input name="noncomp" type="number" min="0" step=".0001" required placeholder="Conforme enquadramento"></label><label>Cobranças adicionais (R$)<input name="fixed" type="number" min="0" step=".01" value="0"></label></div><div class="result" aria-live="polite"><strong data-saving>Informe os dados</strong><dl data-results></dl><div class="bar"><span></span></div></div></form><p class="disclaimer">Estimativa simplificada, sem garantia. Informe os valores vigentes consultados na ANEEL/Equatorial Maranhão e as regras aplicáveis ao seu enquadramento de geração distribuída. Tributos, bandeiras e demais cobranças podem alterar o resultado. Não substitui cálculo técnico.</p>'''))
    if "applications" in features:
        blocks.append(section("applications","Soluções para cada realidade",photos([("floating-solar.jpg","Usinas solares"),("hero-main3.jpeg","Energia urbana"),("hero-main4.jpeg","Rede energética")]) if solar else grid([("Aplicações","Dados a confirmar.")])) )
    if "technical" in features:
        blocks.append(section("technical","Informações técnicas",grid([("Captação fotovoltaica","Módulos convertem luz em eletricidade."),("Armazenamento","Baterias compatíveis podem armazenar energia."),("Economia","Depende do consumo, tarifas e dimensionamento.")]) if solar else ""))
    if "cta" in features:
        blocks.append(section("conversion","Vamos transformar a luz em energia." if solar else "Vamos conversar?",'<a class="button" href="#contact">Solicitar avaliação ↗</a>' if "form" in features else ""))
    if "form" in features:
        blocks.append(section("contact","Planeje sua energia." if solar else "Solicite orçamento",'''<form id="quote" class="fields quote"><label>Nome<input name="name" required maxlength="100"></label><label>Cidade<input name="city" required maxlength="100"></label><label>Conta média mensal (R$)<input name="bill" type="number" min="0" required></label><label>Tipo de projeto<select name="type"><option>Residencial</option><option>Empresarial</option><option>Rural</option></select></label><button class="button" type="submit">Gerar solicitação</button><p role="status" id="quote-status">Formulário demonstrativo. Nenhum dado será transmitido ou armazenado.</p></form>'''))
    if "daynight" in features:
        blocks.append('<section id="daynight" class="daynight"><div class="day">'+image("day-site.png","Cenário diurno")+'</div><div class="night">'+image("night-site.png","Cenário noturno")+'</div><div class="shade"></div><div class="day-copy"><h2>O sol se põe.<br>A energia continua.</h2><div class="buttons"><button class="button" data-mode="day" aria-pressed="true">Dia ☀</button><button class="button" data-mode="night" aria-pressed="false">Noite ☾</button></div><p data-daytext>Geração durante o dia; uso da rede ou baterias compatíveis à noite.</p></div></section>')
    font=next((n for n in assets if "montserrat" in n.lower() and n.lower().endswith(".woff2")),None)
    if font: css="@font-face{font-family:Montserrat;src:url('"+url(font)+"') format('woff2');font-display:swap;font-weight:100 900}"+css
    css=":root{--accent:"+plan["primary"]+";--bg:"+plan["background"]+";--ink:"+plan["text"]+";--font:"+plan["font"]+",Arial,sans-serif}"+css
    body=header+hero+"<main>"+''.join(blocks)+"</main>"+'<footer>'+name+' · Demonstração desenvolvida por FLP Systems</footer>'+('<div id="cursor" aria-hidden="true"></div>' if "cursor" in features else "")
    policy="default-src 'none'; img-src data:; media-src data:; font-src data:; style-src 'unsafe-inline'; script-src 'unsafe-inline'; connect-src 'none'; form-action 'none'; base-uri 'none'; object-src 'none'"
    head='<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex,nofollow"><title>'+name+'</title><meta name="description" content="'+e(plan["description"])+'">'
    if preview:
        return head+'<meta http-equiv="Content-Security-Policy" content="'+e(policy)+'"><style>'+css+'</style></head><body>'+body+'<script>'+js+'</script></body></html>'
    policy=policy.replace("data:","'self'").replace("script-src 'unsafe-inline'","script-src 'self'").replace("style-src 'unsafe-inline'","style-src 'self' 'unsafe-inline'")
    doc=head+'<meta http-equiv="Content-Security-Policy" content="'+e(policy)+'"><link rel="stylesheet" href="style.css"></head><body>'+body+'<script src="app.js" defer></script></body></html>'
    files={"index.html":doc.encode(),"style.css":css.encode(),"app.js":js.encode(),"_headers":b"/*\n  X-Robots-Tag: noindex, nofollow\n  X-Content-Type-Options: nosniff\n","robots.txt":b"User-agent: *\nDisallow: /\n"}
    files.update({"media/"+n:b for n,b in assets.items()})
    return files

def export(files,report):
    buffer=io.BytesIO()
    with zipfile.ZipFile(buffer,"w",zipfile.ZIP_DEFLATED) as z:
        for n,data in files.items(): z.writestr(n,data)
        z.writestr("requirements-report.json",json.dumps(report,ensure_ascii=False,indent=2))
        z.writestr("README.txt","Site estático: abra index.html ou publique os arquivos em Cloudflare Pages/Vercel. Revise as referências, dados comerciais, licenças e cálculo antes de publicar. Formulário demonstrativo. Nenhuma dependência npm.")
    buffer.seek(0)
    return buffer
