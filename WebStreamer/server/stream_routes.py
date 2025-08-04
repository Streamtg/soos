import aiohttp_jinja2
from aiohttp import web
from WebStreamer.server.exceptions import InvalidHash, FIleNotFound

@routes.get(r"/watch/{path:\S+}", allow_head=True)
async def watch_route_handler(request: web.Request):
    try:
        path = request.match_info["path"]
        match = re.search(r"^([a-zA-Z0-9_-]{6})(\d+)$", path)
        if match:
            secure_hash = match.group(1)
            message_id = int(match.group(2))
        else:
            message_id = int(re.search(r"(\d+)(?:\/\S+)?", path).group(1))
            secure_hash = request.rel_url.query.get("hash")

        html = await render_page(request, message_id, secure_hash)
        return web.Response(text=html, content_type="text/html")
    
    except InvalidHash as e:
        raise web.HTTPForbidden(text=e.message)
    except FIleNotFound as e:
        raise web.HTTPNotFound(text=e.message)
    except Exception as e:
        logging.critical(e, exc_info=True)
        raise web.HTTPInternalServerError(text=str(e))
