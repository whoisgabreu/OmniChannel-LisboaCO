import requests as req
import json

# url = "http://omni.v4lisboatech.com.br/vendas/recorrente/squad?squad_id=carcará"
url = "http://omni.v4lisboatech.com.br/projetos/fases?fase=ongoing"

header = {
    "Content-Type": "application/json",
    "X-API-KEY": "ccf9d74a30dc58035c50d1d0cb19dd20"
}


response = req.get(url = url, headers = header)

print(json.dumps(response.json(), indent = 2, ensure_ascii = False))