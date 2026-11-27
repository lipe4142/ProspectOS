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
    assert "<script>" not in studio.render(model)
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
