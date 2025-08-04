# This file is a part of TG-FileStreamBot

import sys
import asyncio
import logging
from aiohttp import web
from pyrogram import idle

from .vars import Var
from WebStreamer import utils, StreamBot
from WebStreamer.server import stream_routes  # Importa las rutas
from WebStreamer.bot.clients import initialize_clients
import aiohttp_jinja2
import jinja2

logging.basicConfig(
    level=logging.INFO,
    datefmt="%d/%m/%Y %H:%M:%S",
    format='[%(asctime)s] {%(pathname)s:%(lineno)d} %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(stream=sys.stdout),
        logging.FileHandler("streambot.log", mode="a", encoding="utf-8"),
    ],
)

logging.getLogger("aiohttp").setLevel(logging.ERROR)
logging.getLogger("pyrogram").setLevel(logging.ERROR)
logging.getLogger("aiohttp.web").setLevel(logging.ERROR)


def web_server():
    # Crear la app aiohttp
    app = web.Application()

    # Configurar Jinja2
    aiohttp_jinja2.setup(
        app,
        loader=jinja2.FileSystemLoader("WebStreamer/template"),
        autoescape=True,
    )

    # Registrar rutas desde stream_routes.py
    app.add_routes(stream_routes.routes)

    return app


server = web.AppRunner(web_server())

if sys.version_info[1] > 9:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
else:
    loop = asyncio.get_event_loop()


async def start_services():
    print()
    print("-------------------- Initializing Telegram Bot --------------------")
    await StreamBot.start()
    bot_info = await StreamBot.get_me()
    StreamBot.username = bot_info.username
    print("------------------------------ DONE ------------------------------")
    print()
    print("---------------------- Initializing Clients ----------------------")
    await initialize_clients()
    print("------------------------------ DONE ------------------------------")

    if Var.ON_HEROKU:
        print("------------------ Starting Keep Alive Service ------------------")
        print()
        asyncio.create_task(utils.ping_server())

    print("--------------------- Initializing Web Server ---------------------")
    await server.setup()
    bind_address = "0.0.0.0" if Var.ON_HEROKU else Var.BIND_ADDRESS
    await web.TCPSite(server, bind_address, Var.PORT).start()
    print("------------------------------ DONE ------------------------------")
    print()
    print("------------------------- Service Started -------------------------")
    print(f"                        bot =>> {bot_info.first_name}")
    if bot_info.dc_id:
        print(f"                        DC ID =>> {bot_info.dc_id}")
    print(f"                        server ip =>> {bind_address}:{Var.PORT}")
    if Var.ON_HEROKU:
        print(f"                        app running on =>> {Var.FQDN}")
    print("------------------------------------------------------------------")

    await idle()


async def cleanup():
    await server.cleanup()
    await StreamBot.stop()


if __name__ == "__main__":
    try:
        loop.run_until_complete(start_services())
    except KeyboardInterrupt:
        pass
    except Exception as err:
        logging.error(err.with_traceback(None))
    finally:
        loop.run_until_complete(cleanup())
        loop.stop()
        print("------------------------ Stopped Services ------------------------")
