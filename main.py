import json
import logging
import os
from functools import partial
from uuid import uuid4

from aiohttp import web
from elasticsearch import NotFoundError
from elasticsearch_async import AsyncElasticsearch

from middlewares import setup_middlewares
from validators import ItemsValidator

ES_HOST = os.environ.get('ES_HOST', 'localhost')
ES_PORT = os.environ.get('ES_PORT', 9200)

RECIPES_INDEX = 'recipes'
logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger('aiohttp.server')

ElasticSearch = partial(AsyncElasticsearch, hosts=[f'{ES_HOST}:{ES_PORT}'])


def count_dishes(available_components: dict, recipe_components: dict):
    _components = {}
    for component, quantity in recipe_components.items():
        _components[component] = available_components[component] // quantity

    return min(_components.values())


async def suggest_recipes(request):
    items = ItemsValidator.parse_raw(await request.read())
    available_components = {item.item: item.q for item in items.items}
    request_id = uuid4().hex
    log.info(f'[{request_id}] Searching recipes for {available_components}...')
    es = ElasticSearch()
    try:
        result = await es.search(
            {
                "query": {
                    "terms_set": {
                        "ingredients": {
                            "terms": list(available_components.keys()),
                            "minimum_should_match_field": "required_matches"
                        }
                    }
                }
            },
            index=RECIPES_INDEX,
            doc_type='_doc',
            params={
                '_source': 'name,components'
            }
        )
    except NotFoundError:
        return web.json_response({
            'message': 'Please use GET /api/recipes/load for loading recipes book'
        })
    hits = result['hits']['hits']
    suggested_recipes = []
    for recipe in (h['_source'] for h in hits):
        recipe_components = {item['item']: item['q'] for item in recipe['components']}
        dishes_count = count_dishes(available_components, recipe_components)
        if dishes_count:
            suggested_recipes.append({
                'recipe': recipe,
                'dishes_count': dishes_count
            })

    log.info(f'[{request_id}] Found {len(suggested_recipes)} recipes: '
             f'{[r["recipe"]["name"] for r in suggested_recipes]}')
    return web.json_response({
        'recipes': suggested_recipes
    })


async def es_info(request):
    es = ElasticSearch()
    cluster_info = await es.info()
    return web.json_response(cluster_info)


async def load_recipes(request):
    log.info('Loading recipes...')
    es = ElasticSearch()
    if es.indices.exists(index=RECIPES_INDEX):
        log.info('Recipes index already exists')
    else:
        await es.index(index=RECIPES_INDEX, body={
            "mappings": {
                "properties": {
                    "name": {
                        "type": "text"
                    },
                    "components": {
                        "type": "nested",
                        "properties": {
                            "item": {
                                "type": "keyword"
                            },
                            "q": {
                                "type": "long"
                            }
                        }
                    },
                    "ingredients": {
                        "type": "keyword"
                    },
                    "required_matches": {
                        "type": "integer"
                    }
                }
            }
        })
    with open('task.json', encoding='utf-8') as f:
        recipes_book = json.load(f)

    recipes_body = []
    for i, recipe in enumerate(recipes_book['recipes'], 1):
        ingredients = [item['item'] for item in recipe['components']]

        recipes_body.append({'index': {'_id': i}})
        _recipe = {
            **recipe,
            'ingredients': ingredients,
            'required_matches': len(ingredients)
        }
        recipes_body.append(_recipe)
    await es.bulk(recipes_body, index=RECIPES_INDEX)
    log.info(f'inserted/updated {len(recipes_body) // 2} recipes')

    return web.json_response({
        'message': f'inserted/updated {len(recipes_body) // 2} recipes'
    })


async def create_app(loop=None):
    app = web.Application(loop=loop)
    app.router.add_route('GET', '/api/elasticsearch/info', es_info)
    app.router.add_route('GET', '/api/recipes/load', load_recipes)
    app.router.add_route('POST', '/api/recipes/suggest', suggest_recipes)
    setup_middlewares(app)
    return app


if __name__ == "__main__":
    web.run_app(create_app())
