import asyncio
import aiohttp
import json

url = "https://api.pipefy.com/graphql"
bearer = "Bearer eyJhbGciOiJIUzUxMiJ9.eyJpc3MiOiJQaXBlZnkiLCJpYXQiOjE3MzE5NDAxNTksImp0aSI6ImRlOWYzZTliLTRhNWItNGQ4NS1hYTIxLWI1MTI5ZTljOWRlOSIsInN1YiI6MzA0NjI1NjE4LCJ1c2VyIjp7ImlkIjozMDQ2MjU2MTgsImVtYWlsIjoidjRsaWRlcmFuY2EubGlzYm9hQGdtYWlsLmNvbSJ9fQ.1idDgKqRm_kjkckYenzI2PDukClXncgmYHJzr96NCoChL7ZJWKatJoj8x3FqnSvk3_D0XWVldQ2oFgEs1l_hWg"

HEADERS = {
    "Authorization": bearer,
    "Content-Type": "application/json"
}

async def extract_id(session, next_page_id=None):
    query = f"""
    {{
        allCards(pipeId: 305511213{f', after: "{next_page_id}"' if next_page_id else ''}) {{
            edges {{ node {{ id }} }}
            pageInfo {{ hasNextPage endCursor }}
        }}
    }}
    """
    payload = {"query": query}

    async with session.post(url, json=payload) as resp:
        resp.raise_for_status()
        data = await resp.json()
        cards = [edge["node"]["id"] for edge in data["data"]["allCards"]["edges"]]

        if data["data"]["allCards"]["pageInfo"]["hasNextPage"]:
            cards += await extract_id(session, data["data"]["allCards"]["pageInfo"]["endCursor"])

        return cards

async def extract_card_info(session, card_id):
    query = f"""
    {{
        card(id: {card_id}) {{
            id
            title
            created_at
            due_date
            late      # se o card está atrasado
            expired   # se o card passou da validade
            current_phase {{
                id
                name
                done     # se é uma fase final
                }}
            fields {{
                name
                value
                }}
        }}
    }}
    """
    payload = {"query": query}

    async with session.post(url, json=payload) as resp:
        resp.raise_for_status()
        return await resp.json()

# def format_pipefy_json(pipefy_data):
#     card = pipefy_data['data']['card']
#     formatted = {'id': card['id'], 'title': card['title']}
#     for field in card['fields']:
#         formatted[field['name']] = field['value']
#     return formatted

def format_pipefy_json(pipefy_data):
    if 'data' not in pipefy_data or 'card' not in pipefy_data['data']:
        print("Erro na resposta:", json.dumps(pipefy_data, indent=2, ensure_ascii=False))
        return None  # ou algum dicionário vazio se preferir

    card = pipefy_data['data']['card']
    formatted = {'id': card['id'], 'title': card['title'], 'fase': card['current_phase']['name']}
    for field in card.get('fields', []):
        formatted[field['name']] = field['value']
    return formatted



async def main():
    async with aiohttp.ClientSession(headers=HEADERS) as session:
        ids = await extract_id(session)
        print(f"Total de Cards: {len(ids)}")

        tasks = [
            extract_card_info(session, card_id)
            for card_id in ids
        ]
        raw_cards = await asyncio.gather(*tasks)

        formatted_cards = [format_pipefy_json(data) for data in raw_cards]

        result = {"data": formatted_cards}

        # with open("card.json", "w", encoding="utf-8-sig") as f:
        #     json.dump(result, f, indent=4, ensure_ascii=False)

        # print("Arquivo 'teste.json' salvo!")
        return result


asyncio.run(main())