import aiohttp_jinja2
import jinja2
import logging
import secrets
import urllib.parse
from WebStreamer.vars import Var
from WebStreamer.bot import StreamBot
from WebStreamer.utils.human_readable import humanbytes
from WebStreamer.utils.file_properties import get_file_ids
from WebStreamer.server.exceptions import InvalidHash
import aiohttp

import os

# Inicializa Jinja2 (asegúrate de llamar esto una vez en el app, por ejemplo en main.py o __init__.py)
def setup_jinja(app):
    aiohttp_jinja2.setup(app, loader=jinja2.FileSystemLoader(os.path.join(os.path.dirname(__file__), '..', 'template')))

# Renderizar plantilla media.html con variables
async def render_page(message_id, secure_hash):
    file_data = await get_file_ids(StreamBot, int(Var.BIN_CHANNEL), int(message_id))
    if file_data.unique_id[:6] != secure_hash:
        logging.debug(f"link hash: {secure_hash} - {file_data.unique_id[:6]}")
        logging.debug(f"Invalid hash for message with ID {message_id}")
        raise InvalidHash
    src = urllib.parse.urljoin(Var.URL, f"{secure_hash}{str(message_id)}")
    
    mime_main = file_data.mime_type.split('/')[0].strip() if file_data.mime_type else ''
    
    # Para descarga calcula tamaño
    file_size = None
    if mime_main not in ['video', 'audio']:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.head(src) as resp:
                    file_size = humanbytes(int(resp.headers.get('Content-Length', 0)))
        except Exception as e:
            logging.error(f"Error getting file size: {e}")
    
    context = {
        "title": f"{'Watch' if mime_main == 'video' else 'Listen' if mime_main == 'audio' else 'Download'} {file_data.file_name}",
        "media_type": mime_main,
        "src": src,
        "file_name": file_data.file_name,
        "file_size": file_size,
    }
    
    # Renderiza la plantilla con jinja2
    import aiohttp_jinja2
    # Usamos render_template_string porque estamos dentro de una función async
    # Pero para mejor rendimiento es preferible configurar jinja en el app principal y usar aiohttp_jinja2.render_template
    template_path = 'media.html'
    
    env = aiohttp_jinja2.get_env()
    template = env.get_template(template_path)
    return template.render(**context)
