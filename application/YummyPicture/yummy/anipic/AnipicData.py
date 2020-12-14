import asyncio

import PIL.Image
import aiohttp
from aiohttp_socks import ProxyConnector

from application.YummyPicture import ymConfig
from application.YummyPicture.YummyData import YummyData


class AnipicData(YummyData):
    file_url: str
    small_preview: str
    medium_preview: str
    big_preview: str
    md5: str
    erotics: str

    async def get(self, check_size: bool = False, size="file") -> bytes:
        try:
            headers = {}
            connector: ProxyConnector = ProxyConnector()
            proxy = ymConfig.getConfig('setting').get('proxy')
            if proxy:
                connector = ProxyConnector.from_url(proxy)
            if size == "small":
                self.url = self.small_preview
            elif size == "medium":
                self.url = self.medium_preview
            elif size == "big":
                self.url = self.big_preview
            elif size == "file":
                self.url = self.file_url
            async with aiohttp.request('GET', self.url, headers=headers, connector=connector,
                                       timeout=aiohttp.ClientTimeout(600)) as resp:
                img_bytes: bytes = await resp.read()
                if connector:
                    await connector.close()
            if check_size:
                pass
                '''img: PIL.Image.Image = PIL.Image.open(BytesIO(initial_bytes=img_bytes))
                if img.size != (self.width, self.height):
                    raise ValueError(f'Image Size Error: expected {(self.width, self.height)} but got {img.size}')'''
        except (asyncio.TimeoutError, ValueError) as e:
            raise e
        except PIL.UnidentifiedImageError:
            raise ValueError(f'Image load fail {str(img_bytes[:20])}...')
        return img_bytes
