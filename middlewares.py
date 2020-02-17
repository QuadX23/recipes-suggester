from aiohttp import web
from pydantic import ValidationError


def create_error_middleware():
    @web.middleware
    async def error_middleware(request, handler):
        try:
            response = await handler(request)
        except web.HTTPException as e:
            return web.json_response({
                'message': str(e),
            }, status=e.status)
        except ValidationError as e:
            return web.json_response({
                'message': str(e),
                'errors': e.errors()
            }, status=400)
        else:
            return response

    return error_middleware


def setup_middlewares(app):
    error_middleware = create_error_middleware()
    app.middlewares.append(error_middleware)
