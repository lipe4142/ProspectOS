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


@pytest.mark.parametrize("used, expected", [(10, 200), (99, 200), (100, 400)])
def test_ai_daily_unlimited_monthly_limit(tmp_path, monkeypatch, used, expected):
    from flask import Flask
    from contextlib import closing

    db_path = tmp_path / "studio.db"

    def connect():
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        return conn

    monkeypatch.setattr(routes.db, "conectar", connect)
    with closing(connect()) as conn:
        routes.prepare(conn)
        conn.executemany(
            "INSERT INTO studio_ai_usage(project_id) VALUES (?)",
            [("previous",)] * used,
        )
        conn.commit()

    calls = []
    def fake_ai(*args, **kwargs):
        calls.append(True)
        return studio.starter("Empresa"), "test", None

    monkeypatch.setattr(routes.ia, "executar_com_fallback", fake_ai)
    app = Flask(__name__)
    app.register_blueprint(routes.bp)
    app.config["TESTING"] = True
    with app.test_client() as client:
        created = client.post("/api/studio/projects", json={"name": "Empresa"})
        assert created.status_code == 201
        pid = created.get_json()["id"]
        result = client.post(
            f"/api/studio/projects/{pid}/ai",
            json={"instruction": "Atualize o site", "confirm_cost": True},
        )
        assert result.status_code == expected
        assert len(calls) == (1 if expected == 200 else 0)
        summary = client.get("/api/studio/projects").get_json()
        assert summary["requests_today"] == used + (1 if expected == 200 else 0)
        if expected == 400:
            assert "mensal" in result.get_json()["erro"]
