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
    mime_main = file_data.mime_type.split('/')[0].strip()

    async with aiofiles.open('WebStreamer/template/media.html') as f:
        template = await f.read()

    if mime_main == 'video':
        heading = f'Watch {file_data.file_name}'
        media_content = f'<video controls playsinline src="{src}"></video>'
    elif mime_main == 'audio':
        heading = f'Listen {file_data.file_name}'
        media_content = f'<audio controls src="{src}"></audio>'
    else:
        # Para descarga, obtenemos el tamaño del archivo
        async with aiohttp.ClientSession() as session:
            async with session.head(src) as resp:
                content_length = resp.headers.get('Content-Length', '0')
                file_size = humanbytes(int(content_length))
        heading = f'Download {file_data.file_name}'
        media_content = f'<a href="{src}" download class="download-link">📥 Download {file_data.file_name}</a><p class="file-size">File size: {file_size}</p>'

    html = template.format(heading=heading, filename=file_data.file_name, media_content=media_content)
    return html
