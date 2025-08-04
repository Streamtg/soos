import aiohttp_jinja2
import jinja2
from aiohttp import web
from WebStreamer.server import routes  # importa tus rutas

def web_server():
    app = web.Application()
    
    # Configurar Jinja2 con la carpeta de templates (ajusta ruta si hace falta)
    aiohttp_jinja2.setup(app, loader=jinja2.FileSystemLoader('WebStreamer/template'))

    # Registrar rutas
    app.add_routes(routes)

    return app
