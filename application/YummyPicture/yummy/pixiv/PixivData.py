import asyncio

import PIL.Image
import aiohttp
from aiohttp_socks import ProxyConnector

from application.YummyPicture import ymConfig
from application.YummyPicture.YummyData import YummyData


class PixivData(YummyData):
    image_urls: dict
    meta_single_page: dict
    meta_pages: list

    async def get(self, check_size: bool = False, size="big") -> bytes:
        try:
            headers: dict = dict(Referer='https://pixiv.net')
            connector: ProxyConnector = ProxyConnector()
            proxy = ymConfig.getConfig('setting').get('proxy')
            if proxy:
                connector = ProxyConnector.from_url(proxy)
            if size == "small":
                self.url = self.image_urls['square_medium']
            elif size == "medium":
                self.url = self.image_urls['medium']
            elif size == "big":
                self.url = self.image_urls['large']
            elif size == "file":
                if self.meta_single_page:
                    self.url = self.meta_single_page['original_image_url']
                else:
                    self.url = self.meta_pages[0]['image_urls']['original']
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
