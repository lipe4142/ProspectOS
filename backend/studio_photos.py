"""Pesquisa opcional de imagens ilustrativas. Chave apenas no backend."""
import base64
import os
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
    return {"id":p["id"],"photographer":str(p.get("photographer",""))[:100],"alt":str(p.get("alt",""))[:200],
            "url":"https://www.pexels.com/photo/"+str(p["id"])+"/",
            "thumbnail":src.get("medium","")}


def search(query):
    if not isinstance(query,str) or not 2<=len(query.strip())<=100:
        raise ValueError("Informe de 2 a 100 caracteres para pesquisar imagens.")
    data = _api("/search",{"query":query.strip(),"per_page":8,"orientation":"landscape","locale":"pt-BR"})
    return [_photo(p) for p in data.get("photos",[]) if type(p.get("id")) is int
            and urlsplit((p.get("src") or {}).get("medium","")).hostname=="images.pexels.com"]


def import_photo(pid):
    if type(pid) is not int or not 0<pid<10**12:
        raise ValueError("Imagem inválida.")
    data = _api("/photos/"+str(pid))
    photo = _photo(data)
    url = data.get("src",{}).get("large","")
    parsed=urlsplit(url)
    if parsed.scheme!="https" or parsed.netloc!="images.pexels.com":
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
