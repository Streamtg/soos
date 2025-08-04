import aiohttp_jinja2
import logging
from WebStreamer.utils.file_properties import get_file_ids
from WebStreamer.bot import StreamBot
from WebStreamer.vars import Var
from WebStreamer.utils.human_readable import humanbytes
import urllib.parse

async def render_page(request, message_id, secure_hash):
    file_data = await get_file_ids(StreamBot, int(Var.BIN_CHANNEL), int(message_id))
    if file_data.unique_id[:6] != secure_hash:
        logging.debug(f"Invalid hash for message with ID {message_id}")
        raise InvalidHash

    src = urllib.parse.urljoin(Var.URL, f'{secure_hash}{str(message_id)}')

    # Definir variables comunes para plantilla
    heading = ""
    tag = ""
    file_size = None
    template_name = "req_dl.html"  # Usaremos una plantilla unificada

    main_type = file_data.mime_type.split('/')[0].strip()

    if main_type == 'video':
        heading = f"Watch {file_data.file_name}"
        tag = "video"
    elif main_type == 'audio':
        heading = f"Listen {file_data.file_name}"
        tag = "audio"
    else:
        heading = f"Download {file_data.file_name}"
        tag = "download"
        # Obtener tamaño archivo remoto
        async with aiohttp.ClientSession() as session:
            async with session.head(src) as resp:
                content_length = resp.headers.get('Content-Length')
                if content_length:
                    file_size = humanbytes(int(content_length))
                else:
                    file_size = None

    env = aiohttp_jinja2.get_env(request.app)
    template = env.get_template(template_name)
    html = template.render(
        heading=heading,
        file_name=file_data.file_name,
        src=src,
        file_size=file_size,
        tag=tag
    )
    return html
