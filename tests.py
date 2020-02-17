from main import create_app


async def test_elasticsearch(aiohttp_client):
    client = await aiohttp_client(await create_app())
    resp = await client.get("/api/elasticsearch/info")
    assert resp.status == 200


async def test_validation(aiohttp_client):
    client = await aiohttp_client(await create_app())
    resp = await client.post("/api/recipes/suggest", json={
        "BAD_KEY": []
    })
    assert resp.status == 400

    resp = await client.post("/api/recipes/suggest", json={
        "items": [
            {
                "item": "мясо",
                "q": -1
            }
        ]
    })
    assert resp.status == 400

    resp = await client.post("/api/recipes/suggest", json={
        "items": [
            {
                "item": 1,
                "q": 10
            }
        ]
    })
    assert resp.status == 400

    resp = await client.post("/api/recipes/suggest", json={
        "items": [
            {
                "BAD_KEY": "test",
                "q": 10
            }
        ]
    })
    assert resp.status == 400

    resp = await client.post("/api/recipes/suggest", json={
        "items": [
            {
                "item": "test item",
                "q": 1
            }
        ]
    })
    assert resp.status == 200


async def test_suggested_recipes(aiohttp_client):
    client = await aiohttp_client(await create_app())
    resp = await client.post("/api/recipes/suggest", json={
        "items": [
            {
                "item": "мясо",
                "q": 400
            },
            {
                "item": "картофель",
                "q": 3
            }
        ]
    })
    assert resp.status == 200
    await resp.json() == []

    resp = await client.post("/api/recipes/suggest", json={
        "items": [
            {
                "item": "мясо",
                "q": 500
            },
            {
                "item": "картофель",
                "q": 3
            }
        ]
    })
    assert resp.status == 200
    await resp.json() == {
        'recipes': [
            {
                'recipe': {
                    'components': [
                        {'q': 500, 'item': 'мясо'},
                        {'q': 3, 'item': 'картофель'}
                    ],
                    'name': 'Салат «Ленинградский»'
                },
                'dishes_count': 1
            }
        ]
    }

    resp = await client.post("/api/recipes/suggest", json={
        "items": [
            {
                "item": "мясо",
                "q": 1100
            },
            {
                "item": "картофель",
                "q": 7
            }
        ]
    })
    assert resp.status == 200
    await resp.json() == {
        'recipes': [
            {
                'recipe': {
                    'components': [
                        {'q': 500, 'item': 'мясо'},
                        {'q': 3, 'item': 'картофель'}
                    ],
                    'name': 'Салат «Ленинградский»'
                },
                'dishes_count': 2
            }
        ]
    }

    resp = await client.post("/api/recipes/suggest", json={
        "items": [
            {
                "item": "мясо",
                "q": 1100
            },
            {
                "item": "картофель",
                "q": 7
            },
            {
                "item": "огурец",
                "q": 6
            },
        ]
    })
    assert resp.status == 200
    await resp.json() == {
        "recipes": [
            {
                "recipe": {
                    "components": [
                        {
                            "q": 250,
                            "item": "мясо"
                        },
                        {
                            "q": 2,
                            "item": "огурец"
                        }
                    ],
                    "name": "Салат «Русский»"
                },
                "dishes_count": 3
            },
            {
                "recipe": {
                    "components": [
                        {
                            "q": 500,
                            "item": "мясо"
                        },
                        {
                            "q": 3,
                            "item": "картофель"
                        }
                    ],
                    "name": "Салат «Ленинградский»"
                },
                "dishes_count": 2
            },
            {
                "recipe": {
                    "components": [
                        {
                            "q": 4,
                            "item": "огурец"
                        }
                    ],
                    "name": "Огурец нарезной"
                },
                "dishes_count": 1
            }
        ]
    }
