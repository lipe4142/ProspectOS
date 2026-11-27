import pytest
from zipfile import ZipFile
import sqlite3
import site_studio as studio
import rotas_studio as routes
import studio_cloudflare as cf


def test_template_and_export():
    model=studio.starter("Empresa & Filhos","98912345678","solar")
    rendered=studio.render(model)
    assert "Empresa &amp; Filhos" in rendered
    assert "noindex,nofollow" in rendered
    assert "https://wa.me/5598912345678" in rendered
    assert "wa.me" not in studio.render(model,preview=True)
    with ZipFile(studio.export_zip(model)) as z:
        assert {"index.html","robots.txt","_headers","README.txt"} == set(z.namelist())


def test_escape_untrusted_content():
    model=studio.starter("<script>alert(1)</script>")
    assert "<script>" not in studio.render(model,preview=True)
    assert "<script>alert(1)</script>" not in studio.render(model)
    model["theme"]["primary"]="red;position:fixed"
    with pytest.raises(ValueError):
        studio.validate(model)


def test_reject_external_image():
    model=studio.starter("Empresa")
    model["sections"][0]["image"]="https://example.com/image.png"
    with pytest.raises(ValueError):
        studio.validate(model)


def test_migration_idempotent_and_preserves_leads():
    conn=sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE leads (place_id TEXT PRIMARY KEY)")
    conn.execute("INSERT INTO leads VALUES ('abc')")
    routes.prepare(conn)
    routes.prepare(conn)
    assert conn.execute("SELECT place_id FROM leads").fetchone()[0]=="abc"
    assert conn.execute("SELECT COUNT(*) FROM studio_projects").fetchone()[0]==0


def test_cloudflare_name():
    assert cf.project_name("Energia São Luís!", "abcdef0123456789")=="flp-energia-sao-luis-abcdef0123"


def test_cloudflare_missing_credentials(monkeypatch):
    monkeypatch.delenv("CLOUDFLARE_ACCOUNT_ID",raising=False)
    monkeypatch.delenv("CLOUDFLARE_API_TOKEN",raising=False)
    with pytest.raises(cf.CloudflareError):
        cf.credentials()


@pytest.mark.parametrize("layout",["split","editorial","center","cinematic","industrial","organic","brutalist","luxury","bento"])
def test_premium_styles(layout):
    model=studio.starter("Empresa de teste")
    model["theme"]["layout"]=layout
    doc=studio.render(model,preview=True)
    assert 'class="style-'+layout+' ' in doc
    assert "FLP / DIREÇÃO VISUAL" not in doc
    assert "prefers-reduced-motion" in doc
    assert "Content-Security-Policy" in doc
    assert "<script" not in doc


def test_premium_components_and_quality():
    model=studio.starter("Empresa")
    model["sections"].insert(1,{"kind":"services","title":"Serviços","body":"", "variant":"bento",
        "items":[{"title":"<img src=x>","body":"Descrição"}]})
    model["sections"].insert(2,{"kind":"faq","title":"Perguntas","body":"",
        "items":[{"title":"Como entrar em contato?","body":"Pelos canais disponíveis."}]})
    doc=studio.render(model)
    assert 'variant-bento' in doc and '<details>' in doc
    assert '&lt;img src=x&gt;' in doc
    assert any(x["label"]=="Imagem principal autorizada" and not x["passed"] for x in studio.quality(model))


def test_invalid_variant_and_credit_url():
    model=studio.starter("Empresa")
    model["sections"][0]["variant"]="bad"
    with pytest.raises(ValueError):
        studio.validate(model)
    model["sections"][0]["variant"]="auto"
    model["sections"][0]["image_source"]="javascript:alert(1)"
    with pytest.raises(ValueError):
        studio.validate(model)


def test_legacy_model_defaults():
    model=studio.starter("Empresa")
    for s in model["sections"]:
        for key in ("variant","eyebrow","cta","items","image_alt","image_source","image_credit"):
            s.pop(key)
    assert studio.validate(model)["sections"][0]["variant"]=="auto"


def test_photo_integration_requires_key(monkeypatch):
    import studio_photos
    monkeypatch.delenv("PEXELS_API_KEY",raising=False)
    with pytest.raises(ValueError,match="PEXELS_API_KEY"):
        studio_photos.search("arquitetura",provider="pexels")


def test_auto_direction_advocacy():
    import studio_direction
    info=studio_direction.analyze("Daniel Maia Advocacia", "Advogado trabalhista")
    assert info["template"]=="advocacia"
    assert info["style"]=="luxury"
    assert info["photo_query"]=="law books legal office"
    assert studio_direction.analyze("Empresa",preferred="solar")["template"]=="solar"


def test_pixabay_search_and_import(monkeypatch):
    import studio_photos as photos
    record={"id":42,"type":"photo","user":"Autor","tags":"law, books",
            "pageURL":"https://pixabay.com/photos/law-books-42/",
            "previewURL":"https://cdn.pixabay.com/photo/example.jpg",
            "largeImageURL":"https://pixabay.com/get/example.jpg"}
    monkeypatch.setenv("PIXABAY_API_KEY","fake")
    monkeypatch.setattr(photos,"pixabay_api",lambda params:{"hits":[record]})
    assert photos.search("law books")[0]["provider"]=="pixabay"
    monkeypatch.setattr(photos,"download",lambda photo,url,hosts:photo)
    assert photos.import_photo(42,"pixabay")["url"]==record["pageURL"]
    model=studio.starter("Escritório")
    model["sections"][0]["image_source"]=record["pageURL"]
    assert studio.validate(model)["sections"][0]["image_source"]==record["pageURL"]


def test_fixed_js_and_csp():
    import studio_premium as premium
    model=studio.starter("Empresa")
    doc=studio.render(model)
    assert "sha256-"+premium.SCRIPT_HASH in doc
    assert "<script>"+premium.SCRIPT+"</script>" in doc
    assert "<script>" not in studio.render(model,preview=True)
    assert premium.contrast("#ffffff","#000000")==21


def test_new_design_controls():
    model=studio.starter("Escritório")
    model["theme"].update(heading_font="Georgia",spacing="airy",corners="square")
    model["sections"][1]["surface"]="contrast"
    doc=studio.render(model,preview=True)
    assert "spacing-airy corners-square" in doc
    assert "surface-contrast" in doc
    assert "body[class]{--heading:Georgia}" in doc
