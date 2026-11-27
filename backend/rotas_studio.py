"""API local do Site Studio, com versionamento e geração por IA."""
import json
import sqlite3
import uuid
from contextlib import closing
from flask import Blueprint, jsonify, request, send_file
import db
import ia
import site_studio as studio
import studio_ai
from rotas_comercial import _dados_empresa, _sugestoes_nicho
from studio_design import APPEARANCES, DEPTHS, GOALS, ITEM_KINDS, KIND_LABELS, KIND_VARIANTS, PALETTES, VARIANTS, infer_template, theme_for

bp = Blueprint("site_studio", __name__, url_prefix="/api/studio")


def prepare(conn):
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS studio_projects (
      id TEXT PRIMARY KEY, lead_id TEXT, name TEXT NOT NULL, template TEXT NOT NULL,
      briefing TEXT NOT NULL DEFAULT '', model TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'em_edicao',
      provider TEXT, url TEXT, cf_project TEXT, deploy_id TEXT, revision INTEGER NOT NULL DEFAULT 1,
      created_at TEXT DEFAULT CURRENT_TIMESTAMP, updated_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS studio_versions (
      id INTEGER PRIMARY KEY AUTOINCREMENT, project_id TEXT NOT NULL REFERENCES studio_projects(id),
      model TEXT NOT NULL, label TEXT NOT NULL, created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS studio_sent (
      project_id TEXT PRIMARY KEY REFERENCES studio_projects(id), sent_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS studio_ai_usage (
      id INTEGER PRIMARY KEY AUTOINCREMENT, project_id TEXT NOT NULL, provider TEXT,
      created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
    """)
    conn.commit()


def get_project(conn, pid):
    row = conn.execute("SELECT * FROM studio_projects WHERE id=?", (pid,)).fetchone()
    if row is None:
        raise LookupError("Projeto não encontrado.")
    data = dict(row)
    data["model"] = studio.validate(json.loads(data["model"]))
    sent = conn.execute("SELECT sent_at FROM studio_sent WHERE project_id=?", (pid,)).fetchone()
    data["sent_at"] = sent["sent_at"] if sent else None
    return data


def payload():
    if request.content_length and request.content_length > 9_000_000:
        raise ValueError("Requisição acima de 9 MB.")
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        raise ValueError("Dados inválidos.")
    return data


@bp.errorhandler(ValueError)
def bad(exc):
    return jsonify(erro=str(exc)), 400


@bp.errorhandler(LookupError)
def missing(exc):
    return jsonify(erro=str(exc)), 404


def save(conn, p, model, label, template=None, provider=None):
    model = studio.validate(model)
    cur = conn.execute("""UPDATE studio_projects SET model=?, revision=revision+1,
      template=COALESCE(?,template), provider=COALESCE(?,provider), status='em_edicao',
      updated_at=CURRENT_TIMESTAMP WHERE id=? AND revision=? AND status!='publicando'""",
      (json.dumps(model, ensure_ascii=False), template, provider, p["id"], p["revision"]))
    if cur.rowcount != 1:
        raise ValueError("Projeto alterado em outra operação. Recarregue a página.")
    conn.execute("INSERT INTO studio_versions(project_id,model,label) VALUES(?,?,?)",
                 (p["id"], json.dumps(p["model"], ensure_ascii=False), label))
    conn.commit()
    return get_project(conn, p["id"])


@bp.get("/projects")
def projects():
    with closing(db.conectar()) as conn:
        rows = conn.execute("""SELECT p.id,p.lead_id,p.name,p.template,p.status,p.url,p.updated_at,s.sent_at
          FROM studio_projects p LEFT JOIN studio_sent s ON s.project_id=p.id ORDER BY p.updated_at DESC""").fetchall()
        usage = conn.execute("SELECT COUNT(*) FROM studio_ai_usage WHERE date(created_at)=date('now')").fetchone()[0]
        return jsonify(
            projects=[dict(r) for r in rows], templates={k: v.label for k, v in studio.TEMPLATES.items()},
            template_palettes={k: theme_for(k, "template") for k in studio.TEMPLATES}, fonts=studio.FONTS,
            kinds=studio.KINDS, kind_labels=KIND_LABELS, item_kinds=ITEM_KINDS, kind_variants=KIND_VARIANTS,
            styles=studio.STYLES, variants=VARIANTS, goals={k: v[0] for k, v in GOALS.items()},
            depths=DEPTHS, appearances=APPEARANCES, palettes=PALETTES,
            requests_today=usage, requests_month=monthly_usage(conn),
        )


def monthly_usage(conn):
    return conn.execute(
        "SELECT COUNT(*) FROM studio_ai_usage WHERE strftime('%Y-%m',created_at)=strftime('%Y-%m','now')"
    ).fetchone()[0]


def planned_project(conn, data, sample=False):
    lead_id = studio.txt(data.get("lead_id", ""), 500)
    lead = None
    if lead_id:
        row = conn.execute("SELECT * FROM leads WHERE place_id=?", (lead_id,)).fetchone()
        if not row:
            raise LookupError("Lead não encontrado.")
        lead = dict(row)
    name = studio.txt(data.get("name") or (lead or {}).get("nome") or "", 160)
    if not name and not sample:
        raise ValueError("Informe a empresa.")
    phone = studio.txt(data.get("phone") or str((lead or {}).get("telefone") or ""), 40)
    briefing = studio.txt(data.get("briefing") or "", 20000)
    if not briefing and lead:
        briefing = (_dados_empresa(lead) + "\n" + _sugestoes_nicho(lead))[:20000]
    template = data.get("template", "servicos")
    if template == "auto":
        template = infer_template(name, briefing, lead)
    model = studio.starter(
        name or "Sua empresa", phone, template, goal=data.get("goal", "auto"), depth=data.get("depth", "full"),
        appearance=data.get("appearance", "template"), briefing=briefing, address=str((lead or {}).get("endereco") or ""),
    )
    return lead_id, briefing, template, model


@bp.post("/plan")
def plan():
    with closing(db.conectar()) as conn:
        _, _, template, model = planned_project(conn, payload(), sample=True)
    return jsonify(
        html=studio.render(model, preview=True), template=template, theme=model["theme"],
        goal=model["strategy"]["goal"], sections=[{"id": s["id"], "kind": s["kind"], "title": s["title"]}
                                                 for s in model["sections"]],
    )


@bp.post("/projects")
def create():
    d = payload()
    with closing(db.conectar()) as conn:
        lead_id, briefing, template, model = planned_project(conn, d)
        pid = uuid.uuid4().hex
        conn.execute("INSERT INTO studio_projects(id,lead_id,name,template,briefing,model) VALUES(?,?,?,?,?,?)",
                     (pid, lead_id or None, model["title"], template, briefing, json.dumps(model, ensure_ascii=False)))
        conn.commit()
        return jsonify(get_project(conn,pid)), 201


@bp.get("/projects/<pid>")
def detail(pid):
    with closing(db.conectar()) as conn:
        return jsonify(get_project(conn,pid))


@bp.put("/projects/<pid>")
def edit(pid):
    d = payload()
    with closing(db.conectar()) as conn:
        p = get_project(conn,pid)
        if d.get("revision") != p["revision"]:
            raise ValueError("Versão desatualizada. Recarregue a página.")
        return jsonify(save(conn,p,d.get("model"),"Antes da edição manual"))


@bp.post("/preview")
def preview():
    d = payload()
    return jsonify(studio.preview(d.get("model"), source=d.get("source") is True))


@bp.post("/projects/<pid>/template")
def change_template(pid):
    d = payload()
    template = studio.choice(d.get("template"), studio.TEMPLATES, "Modelo")
    with closing(db.conectar()) as conn:
        p = get_project(conn,pid)
        check_revision(d, p)
        model = p["model"].copy()
        model["theme"] = theme_for(template, "template")
        return jsonify(save(conn,p,model,"Antes da troca de template",template))


@bp.get("/projects/<pid>/versions")
def versions(pid):
    with closing(db.conectar()) as conn:
        get_project(conn,pid)
        rows = conn.execute("SELECT id,label,created_at FROM studio_versions WHERE project_id=? ORDER BY id DESC",(pid,)).fetchall()
        return jsonify([dict(r) for r in rows])


@bp.post("/projects/<pid>/restore/<int:vid>")
def restore(pid,vid):
    d = payload() if request.content_length else {}
    with closing(db.conectar()) as conn:
        p = get_project(conn,pid)
        check_revision(d, p)
        row = conn.execute("SELECT model FROM studio_versions WHERE id=? AND project_id=?",(vid,pid)).fetchone()
        if not row:
            raise LookupError("Versão não encontrada.")
        return jsonify(save(conn,p,json.loads(row["model"]),"Antes da restauração"))


@bp.get("/projects/<pid>/export")
def export(pid):
    with closing(db.conectar()) as conn:
        p = get_project(conn,pid)
        return send_file(studio.export_zip(p["model"]),mimetype="application/zip",
                         as_attachment=True,download_name="site-"+pid[:8]+".zip")


def check_revision(data, project):
    if ("revision" in data and data["revision"] != project["revision"]) or project["status"] == "publicando":
        raise ValueError("O projeto mudou ou está em publicação. Recarregue antes de continuar.")


@bp.post("/projects/<pid>/ai")
def generate(pid):
    d = payload()
    if d.get("confirm_cost") is not True:
        raise ValueError("Confirme o uso da IA e possíveis cobranças do provedor.")
    instruction = studio.txt(d.get("instruction",""),4000)
    if not instruction:
        raise ValueError("Informe a alteração desejada.")
    mode = studio.choice(d.get("mode", "edit"), ("edit", "generate", "section"), "Modo de geração")
    with closing(db.conectar()) as conn:
        conn.execute("BEGIN IMMEDIATE")
        p = get_project(conn, pid)
        check_revision(d, p)
        system, user, parser, max_tokens = studio_ai.request_for(p, mode, instruction, d.get("section_id"))
        if monthly_usage(conn) >= 100:
            raise ValueError("Limite mensal de operações de IA (100/mês) atingido.")
        cur = conn.execute("INSERT INTO studio_ai_usage(project_id) VALUES(?)",(pid,))
        usage_id = cur.lastrowid
        conn.commit()
        try:
            result, provider, _ = ia.executar_com_fallback(
                system, user, parser=parser, descricao_log="gerar site", temperatura=0.4,
                formato_json=True, max_tokens=max_tokens,
            )
        except ia.NenhumProvedorDisponivel:
            return jsonify(erro="IA indisponível ou resposta inválida. Confira chaves e cotas; o projeto foi preservado."), 503
        conn.execute("UPDATE studio_ai_usage SET provider=? WHERE id=?",(provider,usage_id))
        conn.commit()
        return jsonify(save(conn,p,result,"Antes da alteração por IA",provider=provider))


import studio_cloudflare as cf


@bp.get("/cloudflare")
def cloudflare():
    try:
        cf.test_connection()
        return jsonify(message="Conexão com Cloudflare Pages confirmada.")
    except cf.CloudflareError as exc:
        return jsonify(erro=str(exc)), 503


@bp.post("/projects/<pid>/publish")
def publish(pid):
    d = payload()
    if d.get("reviewed") is not True:
        raise ValueError("Revise e confirme a publicação.")
    with closing(db.conectar()) as conn:
        p = get_project(conn,pid)
        check_revision(d, p)
        assets = studio.files(p["model"])
        try:
            cf.credentials()
        except cf.CloudflareError as exc:
            return jsonify(erro=str(exc)), 503
        cur = conn.execute("UPDATE studio_projects SET status='publicando' WHERE id=? AND revision=? AND status!='publicando'",(pid,p["revision"]))
        if cur.rowcount != 1:
            raise ValueError("Uma operação está em andamento. Recarregue.")
        conn.execute("INSERT INTO studio_versions(project_id,model,label) VALUES(?,?,?)",
                     (pid,json.dumps(p["model"],ensure_ascii=False),"Antes da publicação"))
        conn.commit()
        try:
            name = p["cf_project"] or cf.project_name(p["name"],pid)
            if not p["cf_project"]:
                cf.ensure_project(name)
                conn.execute("UPDATE studio_projects SET cf_project=? WHERE id=?",(name,pid))
                conn.commit()
            url,deploy_id = cf.deploy(name,assets)
            conn.execute("UPDATE studio_projects SET status='publicado',url=?,deploy_id=?,updated_at=CURRENT_TIMESTAMP WHERE id=?",(url,deploy_id,pid))
            conn.commit()
            return jsonify(get_project(conn,pid))
        except Exception as exc:
            conn.execute("UPDATE studio_projects SET status='erro_publicacao' WHERE id=?",(pid,))
            conn.commit()
            return jsonify(erro=str(exc) if isinstance(exc,cf.CloudflareError) else "Falha na publicação. Confira dependências e painel Cloudflare."),502


@bp.post("/projects/<pid>/sent")
def confirm_sent(pid):
    from datetime import datetime
    d = payload()
    if d.get("confirmed") is not True:
        raise ValueError("Confirme apenas após enviar a demonstração.")
    with closing(db.conectar()) as conn:
        conn.execute("BEGIN IMMEDIATE")
        p = get_project(conn,pid)
        check_revision(d, p)
        if not p["url"] or p["status"] != "publicado" or not p["lead_id"]:
            raise ValueError("Publique o projeto vinculado a um lead antes de registrar o envio.")
        if p["sent_at"]:
            return jsonify(p)
        lead = conn.execute("SELECT status FROM leads WHERE place_id=?",(p["lead_id"],)).fetchone()
        if not lead:
            raise LookupError("Lead não encontrado.")
        now = datetime.now().isoformat(timespec="seconds")
        if lead["status"] == "novo":
            conn.execute("UPDATE leads SET status='contatado',atualizado_em=? WHERE place_id=?",(now,p["lead_id"]))
            conn.execute("INSERT INTO historico_status(place_id,status_anterior,status_novo,alterado_em) VALUES(?,?,?,?)",
                         (p["lead_id"],"novo","contatado",now))
        conn.execute("INSERT INTO studio_sent(project_id) VALUES(?)",(pid,))
        conn.commit()
        return jsonify(get_project(conn,pid))
