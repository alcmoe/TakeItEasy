from . import logger, ymConfig
from application.YummyPicture.YummyData import YummyData
from utils.network import aiohttp, ClientConnectorError, ProxyConnector


class RandomData(YummyData):
    AbandonUrl = []
    rip: str = 'https://setu.awsl.ee/api/setu!'

    async def get(self, check_size: bool = False, size="sample") -> bytes:
        if size == "sample":
            try:
                connector = ProxyConnector()
                if proxy := ymConfig.getConfig('setting').get('proxy'):
                    connector = ProxyConnector.from_url(proxy)
                async with aiohttp.request('GET', self.rip, connector=connector) as r:
                    img_bytes = await r.read()
                    if connector:
                        await connector.close()
                    self.url = r.url.__str__()
                    logger.debug(self.url)
                    if img_bytes.__len__() < 50:
                        self.AbandonUrl.append(self.url)
                        logger.debug(f'abandon {self.url}')
                        return await self.get()
                    self.id = self.url.split('/')[-1].split('.')[0]
                    self.tags = 'no tags'
            except ClientConnectorError:
                return await self.get()
        if check_size:
            pass
        return img_bytes
