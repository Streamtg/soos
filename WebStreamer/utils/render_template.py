import urllib.parse
import aiofiles
import logging
import aiohttp
from WebStreamer.vars import Var
from WebStreamer.bot import StreamBot
from WebStreamer.utils.human_readable import humanbytes
from WebStreamer.utils.file_properties import get_file_ids
from WebStreamer.server.exceptions import InvalidHash

async def render_page(message_id, secure_hash):
    file_data = await get_file_ids(StreamBot, int(Var.BIN_CHANNEL), int(message_id))
    if file_data.unique_id[:6] != secure_hash:
        logging.debug(f'link hash: {secure_hash} - {file_data.unique_id[:6]}')
        logging.debug(f"Invalid hash for message with - ID {message_id}")
        raise InvalidHash

    src = urllib.parse.urljoin(Var.URL, f'{secure_hash}{str(message_id)}')
    main_type = file_data.mime_type.split('/')[0].strip() if file_data.mime_type else ""

    if main_type == 'video' or main_type == 'audio':
        # Usar plantilla única responsive para multimedia
        async with aiofiles.open('WebStreamer/template/req.html', encoding='utf-8') as r:
            heading = ('Watch' if main_type == 'video' else 'Listen') + f" {file_data.file_name}"
            tag_html = ''
            if main_type == 'video':
                tag_html = (
                    f'<video controls playsinline style="max-width:100%; height:auto;">'
                    f'<source src="{src}" type="{file_data.mime_type}">'
                    'Tu navegador no soporta video HTML5.'
                    '</video>'
                )
            elif main_type == 'audio':
                tag_html = (
                    f'<audio controls style="width:100%;">'
                    f'<source src="{src}" type="{file_data.mime_type}">'
                    'Tu navegador no soporta audio HTML5.'
                    '</audio>'
                )
            template = await r.read()
            html = template.replace('tag', tag_html) % (heading, file_data.file_name, tag_html)

    else:
        # Para otro contenido, usar plantilla de descarga con tamaño legible
        async with aiofiles.open('WebStreamer/template/dl.html', encoding='utf-8') as r:
            async with aiohttp.ClientSession() as s:
                async with s.head(src) as head_resp:
                    file_size = humanbytes(int(head_resp.headers.get('Content-Length', 0)))
            heading = f'Download {file_data.file_name}'
            template = await r.read()
            html = template % (heading, file_data.file_name, src, file_size)

    return html
