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


@pytest.fixture
def studio_client(tmp_path, monkeypatch):
    from contextlib import closing
    from flask import Flask

    database = tmp_path / "studio.db"

    def connect():
        conn = sqlite3.connect(database)
        conn.row_factory = sqlite3.Row
        return conn

    monkeypatch.setattr(routes.db, "conectar", connect)
    with closing(connect()) as conn:
        routes.prepare(conn)
        conn.executescript("""
          CREATE TABLE leads (place_id TEXT PRIMARY KEY, nome TEXT, categoria TEXT,
                              nicho TEXT, telefone TEXT, endereco TEXT);
          INSERT INTO leads VALUES ('lead-1', 'Clínica Horizonte', 'Dentista', 'Odontologia',
                                     '98912345678', 'Rua A, 15');
        """)

    app = Flask(__name__)
    app.config["TESTING"] = True
    app.register_blueprint(routes.bp)
    return app.test_client(), connect


def test_plan_and_creation_share_template_goal_and_palette(studio_client):
    client, _ = studio_client
    config = {"lead_id": "lead-1", "template": "auto", "appearance": "dark", "depth": "full",
              "briefing": "Sobre: Atendimento odontológico.\nEspecialidades: Ortodontia; Avaliação odontológica"}
    response = client.post("/api/studio/plan", json=config)
    assert response.status_code == 200
    plan = response.get_json()
    assert plan["template"] == "saude"
    assert plan["goal"] == "booking"
    assert "wa.me" not in plan["html"]
    assert client.get("/api/studio/projects").get_json()["projects"] == []

    created = client.post("/api/studio/projects", json=config).get_json()
    model = created["model"]
    assert model["title"] == "Clínica Horizonte"
    assert model["theme"] == plan["theme"]
    assert model["description"] == "Atendimento odontológico."
    assert [section["kind"] for section in model["sections"]] == [section["kind"] for section in plan["sections"]]
    assert next(s for s in model["sections"] if s["kind"] == "location")["body"] == "Rua A, 15"
    assert next(s for s in model["sections"] if s["kind"] == "services")["items"][0]["title"] == "Ortodontia"

    compact = client.post("/api/studio/plan", json={**config, "depth": "compact", "goal": "showcase", "appearance": "light"}).get_json()
    assert [s["kind"] for s in compact["sections"]] == ["hero", "gallery", "services", "contact"]
    assert compact["theme"]["background"] != plan["theme"]["background"]


def test_preview_checklist_and_export_source(studio_client):
    client, _ = studio_client
    model = studio.starter("Studio & Praia", "98912345678", "loja", briefing="Produtos: Camiseta; Caneca")
    model["theme"]["text"] = model["theme"]["background"]
    model["sections"][1]["kind"] = "hero"
    preview = client.post("/api/studio/preview", json={"model": model}).get_json()
    assert preview["html"].count("<h1>") == 1
    assert "<details><summary>" in preview["html"]
    assert "wa.me" not in preview["html"]
    assert not next(check for check in preview["checks"] if check["id"] == "contrast")["passed"]
    source = client.post("/api/studio/preview", json={"model": model, "source": True}).get_json()
    assert "https://wa.me/5598912345678" in source["html"]
    assert "Studio &amp; Praia" in source["html"]


def test_scoped_ai_preserves_other_sections_and_uploaded_image(studio_client, monkeypatch):
    import base64
    import json
    from io import BytesIO
    from PIL import Image

    client, _ = studio_client
    project = client.post("/api/studio/projects", json={"name": "Empresa", "phone": "98912345678"}).get_json()
    pid = project["id"]
    buffer = BytesIO()
    Image.new("RGB", (2, 2)).save(buffer, "PNG")
    photo = "data:image/png;base64," + base64.b64encode(buffer.getvalue()).decode()
    project["model"]["sections"][0].update(image=photo, image_alt="Foto autorizada")
    saved = client.put(f"/api/studio/projects/{pid}", json={"revision": 1, "model": project["model"]}).get_json()
    calls = []

    def fake_ai(system, user, *, parser, max_tokens, **kwargs):
        calls.append(True)
        assert max_tokens == 1500
        assert photo not in user
        assert json.loads(user)["secao"]["id"] == "s0"
        generated = {"title": "Nova abertura", "body": "Texto atualizado.", "image": "https://example.com/fake",
                     "id": "outro", "phone": "000", "kind": "gallery"}
        return parser(json.dumps(generated)), "test", []

    monkeypatch.setattr(routes.ia, "executar_com_fallback", fake_ai)
    action = {"mode": "section", "section_id": "s0", "instruction": "Encurte a abertura", "confirm_cost": True}
    assert client.post(f"/api/studio/projects/{pid}/ai", json={**action, "revision": 1}).status_code == 400
    assert calls == []
    result = client.post(f"/api/studio/projects/{pid}/ai", json={**action, "revision": 2})
    assert result.status_code == 200
    model = result.get_json()["model"]
    assert model["phone"] == "98912345678"
    assert model["sections"][1:] == saved["model"]["sections"][1:]
    assert model["sections"][0]["title"] == "Nova abertura"
    assert model["sections"][0]["image"] == photo
    assert model["sections"][0]["image_alt"] == "Foto autorizada"
    assert model["sections"][0]["kind"] == "hero"
    assert client.get("/api/studio/projects").get_json()["requests_month"] == 1

    version = client.get(f"/api/studio/projects/{pid}/versions").get_json()[0]
    restored = client.post(f"/api/studio/projects/{pid}/restore/{version['id']}")
    assert restored.status_code == 200
    assert restored.get_json()["model"] == saved["model"]


def test_full_ai_expands_legacy_outline_and_checks_ids(studio_client, monkeypatch):
    import json
    from contextlib import closing

    client, connect = studio_client
    created = client.post("/api/studio/projects", json={"name": "Projeto antigo", "phone": "98912345678"}).get_json()
    pid = created["id"]
    legacy = {
        "title": "Projeto antigo", "description": "", "phone": "98912345678",
        "theme": {"primary": "#223344", "background": "#fafafa", "text": "#1b1b1b", "font": "Georgia", "layout": "editorial"},
        "sections": [
            {"kind": "hero", "title": "Abertura", "body": "", "image": ""},
            {"kind": "contact", "title": "Contato", "body": "", "image": ""},
        ],
    }
    with closing(connect()) as conn:
        conn.execute("UPDATE studio_projects SET model=? WHERE id=?", (json.dumps(legacy), pid))
        conn.commit()
    old = client.get(f"/api/studio/projects/{pid}").get_json()["model"]
    assert [part["id"] for part in old["sections"]] == ["s0", "s1"]

    def fake_ai(system, user, *, parser, max_tokens, **kwargs):
        assert max_tokens > 700
        outline = json.loads(user)["roteiro"]
        assert len(outline) > 2
        valid = [{"id": s["id"], "title": "Novo " + s["title"], "body": "Texto do briefing"} for s in reversed(outline)]
        with pytest.raises(ValueError, match="identificadores"):
            parser(json.dumps({"sections": [*valid[:-1], valid[0]]}))
        return parser(json.dumps({"description": "Descrição revisada", "sections": valid})), "test", []

    monkeypatch.setattr(routes.ia, "executar_com_fallback", fake_ai)
    result = client.post(f"/api/studio/projects/{pid}/ai", json={
        "mode": "generate", "instruction": "Atualize a demonstração.", "confirm_cost": True,
    })
    assert result.status_code == 200
    model = result.get_json()["model"]
    assert model["theme"] == old["theme"]
    assert model["phone"] == old["phone"]
    assert model["description"] == "Descrição revisada"
    assert model["sections"][0]["id"] == "s0"
    assert model["sections"][-1]["id"] == "s1"


def test_corrupt_images_return_validation_error(studio_client):
    client, _ = studio_client
    model = studio.starter("Empresa")
    model["sections"][0]["image"] = "data:image/png;base64,AAAA"
    response = client.post("/api/studio/preview", json={"model": model})
    assert response.status_code == 400
    assert "corrompida" in response.get_json()["erro"]
