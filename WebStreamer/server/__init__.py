# WebStreamer/server/__init__.py
# Encargado de exponer las rutas y levantar el servidor web con aiohttp

from aiohttp import web
from .stream_routes import routes # Importa las rutas desde tu archivo principal de rutas

def web_server():
    """
    Crea y configura la aplicación web de aiohttp para el bot.
    """
    app = web.Application()

    # Agregar las rutas definidas en stream_routes.py
    app.add_routes(routes)

    # Guardar la app en el contexto para que otros módulos puedan acceder a ella si es necesario
    app['config'] = {
        'server_name': 'TG-FileStreamBot',
    }

    return app
