import asyncio
import json

import aiohttp
from aiohttp_socks import ProxyConnector
from application.YummyPicture import ymConfig, logger
from application.YummyPicture.exception.SearcherExcetions import SearcherKeyNotFoundException, SearcherProxyNotFoundException


class Searcher:
    url = 'https://saucenao.com/search.php?db=999&output_type=2&testmode=1&numres=5'
    api_key = ymConfig.getConfig('setting').get('search_key')
    connector: ProxyConnector = None

    def setUrl(self, url: str):
        self.url += f'&url={url}'
        return self

    def useApiKey(self):
        if self.api_key:
            self.url += f'&api_key={self.api_key}'
            return self
        else:
            raise SearcherKeyNotFoundException

    def useProxy(self):
        proxy = ymConfig.getConfig('setting').get('proxy')
        if proxy:
            self.connector = ProxyConnector.from_url(proxy)
            return self
        else:
            raise SearcherProxyNotFoundException

    async def get(self) -> list:
        headers = {}
        try:
            async with aiohttp.request('GET', self.url, headers=headers, connector=self.connector,
                                       timeout=aiohttp.ClientTimeout(600)) as resp:
                logger.info(self.url)
                result = json.loads(await resp.read())['results']
                if self.connector:
                    await self.connector.close()
        except (asyncio.TimeoutError, ValueError) as e:
            raise e
        return result
