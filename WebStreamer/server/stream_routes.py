import re
import time
import math
import logging
import secrets
import mimetypes
import os
from aiohttp import web
from aiohttp.http_exceptions import BadStatusLine
from WebStreamer.bot import multi_clients, work_loads
from WebStreamer.server.exceptions import FIleNotFound, InvalidHash
from WebStreamer import Var, utils, StartTime, __version__, StreamBot
from WebStreamer.utils.render_template import render_page

routes = web.RouteTableDef()

# Ruta absoluta a la plantilla HTML
REQ_TEMPLATE_PATH = os.path.join("WebStreamer", "template", "req.html")

def render_player_html(file_name: str, stream_url: str) -> str:
    """Genera el HTML para el reproductor según el tipo de archivo."""
    mime_type, _ = mimetypes.guess_type(file_name)

    if mime_type and mime_type.startswith("video"):
        player_tag = f'<video src="{stream_url}" class="player" controls playsinline></video>'
    elif mime_type and mime_type.startswith("audio"):
        player_tag = f'<audio src="{stream_url}" class="player" controls></audio>'
    else:
        # Si no es audio ni video, mostramos enlace de descarga
        player_tag = f'<a href="{stream_url}" class="download-link" download>📥 Descargar {file_name}</a>'

    with open(REQ_TEMPLATE_PATH, "r", encoding="utf-8") as f:
        template = f.read()

    # Reemplaza los %s del template: título, header, contenido (reproductor o enlace)
    return template % (file_name, file_name, player_tag)


@routes.get("/", allow_head=True)
async def root_route_handler(_):
    """Estado básico del servidor"""
    return web.json_response(
        {
            "server_status": "running",
            "uptime": utils.get_readable_time(time.time() - StartTime),
            "telegram_bot": "@" + StreamBot.username,
            "connected_bots": len(multi_clients),
            "loads": dict(
                ("bot" + str(c + 1), l)
                for c, (_, l) in enumerate(
                    sorted(work_loads.items(), key=lambda x: x[1], reverse=True)
                )
            ),
            "version": __version__,
        }
    )


@routes.get(r"/watch/{path:\S+}", allow_head=True)
async def watch_route_handler(request: web.Request):
    """Página de vista previa estándar"""
    try:
        path = request.match_info["path"]
        match = re.search(r"^([a-zA-Z0-9_-]{6})(\d+)$", path)
        if match:
            secure_hash = match.group(1)
            message_id = int(match.group(2))
        else:
            message_id = int(re.search(r"(\d+)", path).group(1))
            secure_hash = request.rel_url.query.get("hash")
        return web.Response(text=await render_page(message_id, secure_hash), content_type='text/html')
    except InvalidHash as e:
        raise web.HTTPForbidden(text=e.message)
    except FIleNotFound as e:
        raise web.HTTPNotFound(text=e.message)


@routes.get(r"/dl/{path:\S+}", allow_head=True)
async def dl_player_handler(request: web.Request):
    """Plantilla responsive con reproductor integrado"""
    try:
        path = request.match_info["path"]
        match = re.search(r"^([a-zA-Z0-9_-]{6})(\d+)$", path)
        if match:
            secure_hash = match.group(1)
            message_id = int(match.group(2))
        else:
            message_id = int(re.search(r"(\d+)", path).group(1))
            secure_hash = request.rel_url.query.get("hash")

        # Cliente con menos carga
        index = min(work_loads, key=work_loads.get)
        faster_client = multi_clients[index]
        tg_connect = utils.ByteStreamer(faster_client)

        file_id = await tg_connect.get_file_properties(message_id)
        file_name = file_id.file_name or f"{secrets.token_hex(2)}.unknown"

        # URL interna para el stream (usando hash + id)
        stream_url = f"/{secure_hash}{message_id}"

        html_content = render_player_html(file_name, stream_url)
        return web.Response(text=html_content, content_type="text/html")

    except InvalidHash as e:
        raise web.HTTPForbidden(text=e.message)
    except FIleNotFound as e:
        raise web.HTTPNotFound(text=e.message)


@routes.get(r"/{path:\S+}", allow_head=True)
async def stream_handler(request: web.Request):
    """Streaming binario del archivo"""
    try:
        path = request.match_info["path"]
        match = re.search(r"^([a-zA-Z0-9_-]{6})(\d+)$", path)
        if match:
            secure_hash = match.group(1)
            message_id = int(match.group(2))
        else:
            message_id = int(re.search(r"(\d+)", path).group(1))
            secure_hash = request.rel_url.query.get("hash")
        return await media_streamer(request, message_id, secure_hash)
    except InvalidHash as e:
        raise web.HTTPForbidden(text=e.message)
    except FIleNotFound as e:
        raise web.HTTPNotFound(text=e.message)


class_cache = {}

async def media_streamer(request: web.Request, message_id: int, secure_hash: str):
    """Sirve el contenido binario desde Telegram"""
    range_header = request.headers.get("Range", 0)

    index = min(work_loads, key=work_loads.get)
    faster_client = multi_clients[index]

    if Var.MULTI_CLIENT:
        logging.info(f"Client {index} is now serving {request.remote}")

    if faster_client in class_cache:
        tg_connect = class_cache[faster_client]
    else:
        tg_connect = utils.ByteStreamer(faster_client)
        class_cache[faster_client] = tg_connect

    file_id = await tg_connect.get_file_properties(message_id)

    if file_id.unique_id[:6] != secure_hash:
        raise InvalidHash

    file_size = file_id.file_size

    if range_header:
        from_bytes, until_bytes = range_header.replace("bytes=", "").split("-")
        from_bytes = int(from_bytes)
        until_bytes = int(until_bytes) if until_bytes else file_size - 1
    else:
        from_bytes = 0
        until_bytes = file_size - 1

    req_length = until_bytes - from_bytes
    new_chunk_size = await utils.chunk_size(req_length)
    offset = await utils.offset_fix(from_bytes, new_chunk_size)
    first_part_cut = from_bytes - offset
    last_part_cut = (until_bytes % new_chunk_size) + 1
    part_count = math.ceil(req_length / new_chunk_size)

    body = tg_connect.yield_file(
        file_id, index, offset, first_part_cut, last_part_cut, part_count, new_chunk_size
    )

    mime_type = file_id.mime_type or mimetypes.guess_type(file_id.file_name)[0] or "application/octet-stream"
    file_name = file_id.file_name or f"{secrets.token_hex(2)}.unknown"

    return_resp = web.Response(
        status=206 if range_header else 200,
        body=body,
        headers={
            "Content-Type": f"{mime_type}",
            "Content-Range": f"bytes {from_bytes}-{until_bytes}/{file_size}",
            "Content-Disposition": f'attachment; filename="{file_name}"',
            "Accept-Ranges": "bytes",
        },
    )

    if return_resp.status == 200:
        return_resp.headers.add("Content-Length", str(file_size))

    return return_resp
