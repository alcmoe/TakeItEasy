import asyncio
from bs4 import BeautifulSoup
import aiohttp
from aiohttp_socks import ProxyConnector
from utils.network import requestText
from application.YummyPicture import ymConfig, logger
from application.YummyPicture.exception.JASearcherExcetions import JASearcherProxyNotFoundException, \
    JASearcherSourceNotFoundException


class JASearcher:
    sources = ['https://www.javbus.com/uncensored/search/', 'https://www.javbus.com/search/',
               'https://btsow.com/search/']
    source = 2
    url = sources[2]
    api_key = ymConfig.getConfig('setting').get('search_key')
    connector: ProxyConnector = None

    def setSource(self, source: int):
        if len(self.sources) > source > 0:
            self.source = source
            self.url = self.sources[source]
            return self
        else:
            raise JASearcherSourceNotFoundException

    def setID(self, gid: str):
        if self.source == 2:
            self.url += gid
            return self

    def useProxy(self):
        if proxy := ymConfig.getConfig('setting').get('proxy'):
            self.connector = ProxyConnector.from_url(proxy)
            return self
        else:
            raise JASearcherProxyNotFoundException

    async def getList(self, num: int = 3):
        headers = {}
        try:
            async with aiohttp.request('GET', self.url, headers=headers, connector=self.connector,
                                       timeout=aiohttp.ClientTimeout(600)) as resp:
                logger.info(self.url)
                soup = BeautifulSoup(await resp.read(), "lxml")
                '''
                if self.source == 0:
                    movies = soup.find_all("a", class_="movie-box")
                    for movie in movies:
                        frame = movie.contents[1].contents[1]
                        detailLink = movie['href']
                        picLink = frame['src']
                        picInfo = frame['title']
                        async with aiohttp.request('GET', detailLink, headers=headers, connector=self.connector,
                                                   timeout=aiohttp.ClientTimeout(600)) as res:
                            subSoup = BeautifulSoup(await res.read(), "lxml")
                            subs = subSoup.find_all("td")
                            info(detailLink)
                            print(subs)
                            return
                '''
                if self.source == 2:
                    sear = soup.find_all("div", class_="data-list")
                    result = []
                    if sear:
                        movies = sear[0].contents[3::2]
                        for movie in movies:
                            if num < 1:
                                break
                            num -= 1
                            magnet = 'magnet:?xt=urn:btih:' + movie.contents[1]['href'].split('/')[-1]
                            title = movie.contents[1]['title']
                            intel = movie.contents[1].contents[3].string
                            result.append({'text': f'{title}\n{intel}\n{magnet}\n\n'})
                    if self.connector:
                        await self.connector.close()
                    return result
        except (asyncio.TimeoutError, ValueError) as e:
            raise e
        return

    async def get(self, offset: int = 0, limit: int = 3) -> list:
        bts = await self.getList(limit)
        if self.source == 0:
            return bts
        if self.source == 2:
            return bts
        headers = {}
        try:
            data = await requestText(self.url, headers=headers, connector=self.connector, raw=False)
            logger.info(self.url)
            result = data['results']
            if self.connector:
                await self.connector.close()
        except (asyncio.TimeoutError, ValueError) as e:
            raise e
        return result
