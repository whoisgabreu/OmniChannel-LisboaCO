import requests as req


url = "http://127.0.0.1:5005/vendas/recorrente/squad?squad_id=internacional"

header = {
    "Content-Type": "application/json",
    "X-API-KEY": "ccf9d74a30dc58035c50d1d0cb19dd20"
}


response = req.get(url = url, headers = header)

print(response.json())