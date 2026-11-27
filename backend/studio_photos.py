"""Pesquisa opcional de imagens ilustrativas. Chave apenas no backend."""
import base64
import os
import json
import time
from contextlib import closing
import db
from io import BytesIO
from urllib.parse import urlsplit

import requests
from PIL import Image, ImageOps

API = "https://api.pexels.com/v1"


def _api(path, params=None):
    key = os.environ.get("PEXELS_API_KEY", "").strip()
    if not key:
        raise ValueError("Configure PEXELS_API_KEY no backend/.env para pesquisar fotos.")
    try:
        r = requests.get(API+path, params=params, headers={"Authorization":key}, timeout=(5,15), allow_redirects=False)
        if r.status_code != 200:
            raise ValueError("Pexels indisponível ou cota atingida.")
        return r.json()
    except (requests.RequestException, TypeError):
        raise ValueError("Falha ao acessar o Pexels.") from None


def _photo(p):
    src = p.get("src") or {}
    return {"provider":"pexels","id":p["id"],"photographer":str(p.get("photographer",""))[:100],"alt":str(p.get("alt",""))[:200],
            "url":"https://www.pexels.com/photo/"+str(p["id"])+"/",
            "thumbnail":src.get("medium","")}


def pexels_search(query):
    if not isinstance(query,str) or not 2<=len(query.strip())<=100:
        raise ValueError("Informe de 2 a 100 caracteres para pesquisar imagens.")
    data = _api("/search",{"query":query.strip(),"per_page":8,"orientation":"landscape","locale":"pt-BR"})
    return [_photo(p) for p in data.get("photos",[]) if type(p.get("id")) is int
            and urlsplit((p.get("src") or {}).get("medium","")).hostname=="images.pexels.com"]


def pexels_import(pid):
    if type(pid) is not int or not 0<pid<10**12:
        raise ValueError("Imagem inválida.")
    data = _api("/photos/"+str(pid))
    photo = _photo(data)
    url = data.get("src",{}).get("large","")
    return download(photo,url,{"images.pexels.com"})


def download(photo,url,hosts):
    parsed=urlsplit(url)
    if parsed.scheme!="https" or parsed.netloc not in hosts:
        raise ValueError("Origem da imagem não autorizada.")
    try:
        with requests.get(url,stream=True,timeout=(5,20),allow_redirects=False) as r:
            if r.status_code!=200:
                raise ValueError("Imagem indisponível.")
            raw=bytearray()
            for chunk in r.iter_content(65536):
                raw.extend(chunk)
                if len(raw)>8_000_000:
                    raise ValueError("Imagem acima do limite.")
        with Image.open(BytesIO(raw)) as source:
            if source.width*source.height>25_000_000:
                raise ValueError("Imagem acima do limite de pixels.")
            img=ImageOps.exif_transpose(source).convert("RGB")
            img.thumbnail((1600,1200))
            out=BytesIO()
            img.save(out,"WEBP",quality=78)
            if out.tell()>1_000_000:
                raise ValueError("Imagem otimizada acima do limite.")
        return {**photo,"image":"data:image/webp;base64,"+base64.b64encode(out.getvalue()).decode("ascii")}
    except (requests.RequestException,OSError):
        raise ValueError("Não foi possível importar esta imagem.") from None


def pixabay_api(params):
    key=os.environ.get("PIXABAY_API_KEY","").strip()
    if not key:
        raise ValueError("Configure PIXABAY_API_KEY no backend/.env.")
    cache_key=json.dumps(params,sort_keys=True,ensure_ascii=False)
    now=int(time.time())
    with closing(db.conectar()) as conn:
        conn.execute("CREATE TABLE IF NOT EXISTS studio_photo_cache (key TEXT PRIMARY KEY, data TEXT NOT NULL, expires INTEGER NOT NULL)")
        row=conn.execute("SELECT data FROM studio_photo_cache WHERE key=? AND expires>?",(cache_key,now)).fetchone()
        if row:
            return json.loads(row[0])
        conn.commit()
    try:
        response=requests.get("https://pixabay.com/api/",params={**params,"key":key},timeout=(5,15),allow_redirects=False)
        if response.status_code!=200:
            raise ValueError("Pixabay indisponível (HTTP %s). Confira a chave ou cota."%response.status_code)
        data=response.json()
        if not isinstance(data,dict) or not isinstance(data.get("hits"),list):
            raise ValueError("Resposta inválida do Pixabay.")
    except (requests.RequestException,TypeError):
        raise ValueError("Falha ao consultar Pixabay.") from None
    with closing(db.conectar()) as conn:
        conn.execute("DELETE FROM studio_photo_cache WHERE expires<=?",(now,))
        conn.execute("INSERT OR REPLACE INTO studio_photo_cache(key,data,expires) VALUES(?,?,?)",(cache_key,json.dumps(data),now+86400))
        conn.commit()
    return data


def pixabay_photo(p):
    return {"provider":"pixabay","id":p["id"],"photographer":str(p.get("user",""))[:100],
            "alt":str(p.get("tags",""))[:200],"url":p.get("pageURL",""),"thumbnail":p.get("previewURL","")}


def pixabay_search(query):
    data=pixabay_api({"q":query,"image_type":"photo","orientation":"horizontal","safesearch":"true","min_width":1000,"per_page":8,"lang":"en"})
    return [pixabay_photo(p) for p in data["hits"] if type(p.get("id")) is int
            and urlsplit(p.get("previewURL","")).netloc=="cdn.pixabay.com"
            and urlsplit(p.get("previewURL","")).scheme=="https"
            and urlsplit(p.get("pageURL","")).netloc in ("pixabay.com","www.pixabay.com")]


def search(query,provider="auto"):
    if not isinstance(query,str) or not 2<=len(query.strip())<=100:
        raise ValueError("Informe de 2 a 100 caracteres para pesquisar imagens.")
    if provider not in ("auto","pixabay","pexels"):
        raise ValueError("Banco de imagens inválido.")
    if provider=="auto":
        if os.environ.get("PIXABAY_API_KEY","").strip():
            try:
                result=pixabay_search(query.strip())
                if result or not os.environ.get("PEXELS_API_KEY","").strip():
                    return result
            except ValueError:
                if not os.environ.get("PEXELS_API_KEY","").strip():
                    raise
        return pexels_search(query.strip())
    return pixabay_search(query.strip()) if provider=="pixabay" else pexels_search(query.strip())


def import_photo(pid,provider="pexels"):
    if type(pid) is not int or not 0<pid<10**12:
        raise ValueError("Imagem inválida.")
    if provider=="pexels":
        return pexels_import(pid)
    if provider!="pixabay":
        raise ValueError("Banco de imagens inválido.")
    hits=pixabay_api({"id":str(pid)})["hits"]
    photo=next((p for p in hits if p.get("id")==pid and p.get("type")=="photo"),None)
    if not photo:
        raise ValueError("Fotografia não localizada.")
    return download(pixabay_photo(photo),photo.get("largeImageURL","") or photo.get("webformatURL",""),{"pixabay.com","cdn.pixabay.com"})
