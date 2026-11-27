"""Cloudflare Pages Direct Upload, apenas arquivos estáticos gerados pelo Studio."""
import base64
import json
import mimetypes
import os
import re
import time
import unicodedata
import requests

BASE = "https://api.cloudflare.com/client/v4"


class CloudflareError(Exception):
    pass


def credentials():
    account = os.environ.get("CLOUDFLARE_ACCOUNT_ID","").strip()
    token = os.environ.get("CLOUDFLARE_API_TOKEN","").strip()
    if not re.fullmatch(r"[a-fA-F0-9]{32}",account) or not token:
        raise CloudflareError("Configure CLOUDFLARE_ACCOUNT_ID e CLOUDFLARE_API_TOKEN no backend/.env.")
    return account, token


def call(method, path, token, **kwargs):
    try:
        r = requests.request(method, BASE+path, headers={"Authorization":"Bearer "+token},
                             timeout=(10,45), allow_redirects=False, **kwargs)
        result = r.json()
    except (requests.RequestException, ValueError):
        raise CloudflareError("Não foi possível comunicar com a Cloudflare.") from None
    if not r.ok or result.get("success") is not True:
        raise CloudflareError("Cloudflare recusou a operação (HTTP %s)." % r.status_code)
    return result.get("result")


def test_connection():
    account,token = credentials()
    call("GET",f"/accounts/{account}/pages/projects",token,params={"per_page":1})


def project_name(name,pid):
    stem = unicodedata.normalize("NFKD",name).encode("ascii","ignore").decode().lower()
    stem = re.sub("[^a-z0-9]+","-",stem).strip("-")[:35].strip("-") or "site"
    return "flp-"+stem+"-"+pid[:10]


def ensure_project(name,existing=False):
    account,token = credentials()
    path = f"/accounts/{account}/pages/projects"
    if existing:
        return call("GET",path+"/"+name,token)
    return call("POST",path,token,json={"name":name,"production_branch":"main"})


def deploy(name, assets):
    from blake3 import blake3
    account,token = credentials()
    path = f"/accounts/{account}/pages/projects/{name}"
    project = call("GET",path,token)
    jwt = call("GET",path+"/upload-token",token)["jwt"]
    manifest, items = {}, []
    for filename,body in assets.items():
        if filename == "_headers":
            continue
        encoded = base64.b64encode(body).decode("ascii")
        extension = filename.rsplit(".",1)[-1] if "." in filename else ""
        digest = blake3((encoded+extension).encode()).hexdigest()[:32]
        manifest["/"+filename] = digest
        items.append({"key":digest,"value":encoded,"base64":True,
                      "metadata":{"contentType":mimetypes.guess_type(filename)[0] or "application/octet-stream"}})
    missing = call("POST","/pages/assets/check-missing",jwt,json={"hashes":list(manifest.values())})
    for item in items:
        if item["key"] in missing:
            call("POST","/pages/assets/upload",jwt,json=[item])
    call("POST","/pages/assets/upsert-hashes",jwt,json={"hashes":list(manifest.values())})
    deployment = call("POST",path+"/deployments",token,
                      files={"manifest":(None,json.dumps(manifest)),"branch":(None,project["production_branch"]),
                             "_headers":("_headers",assets["_headers"],"text/plain")})
    deploy_id = deployment["id"]
    for _ in range(12):
        d = call("GET",path+"/deployments/"+deploy_id,token)
        stage = d.get("latest_stage") or {}
        if stage.get("status")=="failure":
            raise CloudflareError("Deploy recusado pela Cloudflare.")
        if stage.get("name")=="deploy" and stage.get("status")=="success":
            domain = project.get("subdomain","")
            if not re.fullmatch(r"[a-z0-9-]+\.pages\.dev",domain):
                raise CloudflareError("A API não retornou um subdomínio Pages válido.")
            url = "https://"+domain
            try:
                response = requests.get(url, timeout=(5,10),allow_redirects=False)
                if response.status_code == 200:
                    return url,deploy_id
            except requests.RequestException:
                pass
        time.sleep(3)
    raise CloudflareError("Deploy ainda não confirmado. Consulte o painel Cloudflare antes de tentar novamente.")
