import json
import aiohttp
from aiohttp_socks import ProxyConnector
from application.YummyPicture import ymConfig, logger
from application.YummyPicture.Ripper import *
from application.YummyPicture.yummy.yande import YandeData


class YandeRipper(Ripper):

    def __init__(self):
        super(YandeRipper, self).__init__()
        self.actions = dict(new='post', search='post', random='post', popular='post/popular_recent')
        self.periods = {'1d': '1d', '1w': '1w', '1m': '1m', '1y': '1y'}
        self.rip = 'https://yande.re/'
        self.per_page = 40

    def __build(self):
        # build action
        self.parse(self.actions[self.has_action.value] + '.json?')
        # build option
        # bind popular
        if self.has_action == RipperConst.POPULAR:
            self.parm('period', self.has_period)
        # build random
        if self.has_action == RipperConst.RANDOM:
            self.has_tags.append('order:random')
            self.has_tags.append('rating:e')
        # build search
        if self.has_action in [RipperConst.SEARCH, RipperConst.RANDOM]:
            self.parm('tags', self.tags2str())
        # '''others'''

        # build rating
        if self.has_action == self.actions[RipperConst.NEW.value]:  # post
            self.__buildRating()
        # build page and variant
        self._buildVariant(offset=1)

    async def get(self) -> 'list':
        # params = {}
        self.__build()
        connector: ProxyConnector = ProxyConnector()
        if proxy := ymConfig.getConfig('setting').get('proxy'):
            connector = ProxyConnector.from_url(proxy)
        data: list = []
        for k, t in self.rips.items():
            async with aiohttp.request('GET', k, connector=connector) as response:
                raw = await response.read()
            logger.debug(k + f"\n[{t[0]}, {t[1]}]")
            data = data + json.loads(raw)[t[0]:t[1]]
        result: list = self._formatData(data)
        await connector.close()
        return result

    def _formatData(self, data: list):
        result: [YandeData] = []
        for YandeDataOne in data:
            yande: YandeData = YandeData()
            yr = YandeDataOne['rating']
            if self.has_action == RipperConst.POPULAR and ymConfig.getConfig('yande').get('rating')[yr] > \
                    ymConfig.getConfig('yande').get('rating')[self.has_rating]:
                continue
            yande.__dict__.update(YandeDataOne)
            result.append(yande)
        return result

    def __buildRating(self):
        if ymConfig.getConfig('setting').get('enable_rating_check') != 'disable' and self.has_rating:
            pos = self.rip.find('rating:')
            if pos != -1:
                rating = self.rip[pos:pos + 8]
                self.rip = self.rip.replace(rating, 'rating:' + self.has_rating)
            else:
                if self.has_rating == 's':
                    self.rip = self.rip.replace('tags=', 'tags=rating:s+')
                elif self.has_rating == 'q':
                    self.rip = self.rip.replace('tags=', 'tags=-rating:e+')
                else:  # rating e
                    pass

    def tags2str(self) -> str:
        ts = ''
        for tag in self.has_tags:
            ts += tag + '+'
        return ts
