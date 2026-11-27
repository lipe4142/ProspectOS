import io
import zipfile
import pytest
import studio_advanced as a
import studio_advanced_render as render
import studio_code

PROMPT="""## 1. Objetivo
FLP Solar, energia solar. #090909 #FF6A00.
## 2. Hero
Vídeo controlado pelo scroll solar.mp4.
## 3. Cenas cinematográficas
hero-main0.jpeg
## 4. Colunas opostas
split-1.jpeg até split-6.jpeg.
## 5. Galeria interativa
Lightbox.
## 6. Simulador de economia
Consumo mensal em kWh.
## 7. Formulário de orçamento
Gerar solicitação.
## 8. Dia e noite
day-site.png night-site.png.
"""

def test_requirements_and_assets():
    analysis=a.analyze(PROMPT)
    assert len(analysis["sections"])==8
    assert {"video","scenes","opposed","gallery","calculator","form","daynight"}<=set(analysis["features"])
    assert "split-3.jpeg" in analysis["assets"]
    plan=a.initial_plan("FLP Solar",PROMPT)
    report=a.coverage(PROMPT,plan,{"solar.mp4":b"example"})
    assert "solar.mp4" not in report["missing_assets"]
    assert "day-site.png" in report["missing_assets"]

def test_compiles_separate_files_and_preview():
    plan=a.initial_plan("FLP Solar",PROMPT)
    assets={"solar.mp4":b"video","day-site.png":b"image"}
    files=render.compile_site(plan,assets)
    assert {"index.html","style.css","app.js","media/solar.mp4"}<=files.keys()
    assert b'id="solar-calc"' in files["index.html"]
    assert b'id="hero-video"' in files["index.html"]
    assert b"requestAnimationFrame" in files["app.js"]
    assert b"data-mode" in files["index.html"]
    preview=render.compile_site(plan,assets,preview=True)
    assert "data:video/mp4;base64," in preview
    assert "connect-src" in preview
    assert "requestAnimationFrame" in preview
    with zipfile.ZipFile(render.export(files,{})) as z:
        assert "requirements-report.json" in z.namelist()

def test_zip_never_extracts_code():
    b=io.BytesIO()
    with zipfile.ZipFile(b,"w") as z:
        z.writestr("source/public/images/day-site.png",b"media")
        z.writestr("source/src/App.tsx","export default function App(){}")
        z.writestr("source/.env","KEY=do-not-read")
        z.writestr("source/public/icon.svg","<svg/>")
    assert a.read_media_zip(b.getvalue())=={"day-site.png":b"media"}
    ref=a.inspect_reference_zip(b.getvalue())
    assert len(ref["excerpts"])==1
    assert "do-not-read" not in str(ref)

def test_code_validation_and_review_preview():
    c={"html":'<main><h1>Teste</h1><img src="media/day-site.png" alt="Dia"></main>',"css":"main{color:#fff}","js":"document.querySelector('h1').textContent='Teste';"}
    assert studio_code.validate(c)==c
    p=studio_code.files(c,{"day-site.png":b"image"},"Teste",preview=True)
    assert "sha256-" in p and "data:image/png;base64," in p
    for malicious in ['<script>alert(1)</script>','<img src="https://example.com/a.jpg">','<button onclick="alert(1)">X</button>','<iframe srcdoc="x"></iframe>']:
        with pytest.raises(ValueError):
            studio_code.validate({**c,"html":malicious})
    with pytest.raises(ValueError):
        studio_code.validate({**c,"css":"@import 'https://example.com/style.css';"})

def test_github_rejects_arbitrary_url():
    for url in ("http://127.0.0.1/", "https://github.com.evil.example/u/r", "https://github.com/u/r/../../x"):
        with pytest.raises(ValueError):
            a.public_github_zip(url)
