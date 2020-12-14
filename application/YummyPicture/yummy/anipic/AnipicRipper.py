import json
import time
import random
import aiohttp
from aiohttp_socks import ProxyConnector
from application.YummyPicture import ymConfig
from application.YummyPicture.Ripper import *
from application.YummyPicture.yummy.anipic import AnipicData


class AnipicRipper(Ripper):

    token = ''

    def __init__(self):
        super(AnipicRipper, self).__init__()
        post: str = 'pictures/view_posts'
        self.actions = dict(new=post, search=post, random=post, popular=post)
        self.periods = {'1d': '3', '1w': '1', '1m': '2', '6m': '4', '1y': '5', '2y': '6', '3y': '7'}
        self.rip = 'https://anime-pictures.net/'
        self.per_page = 60

    async def __build(self):
        # build action
        self.parse(self.actions[self.has_action.value] + '/0?')
        # build option
        # bind popular
        if self.has_action == RipperConst.POPULAR:
            self.parm('order_by', 'views').parm('ldate', self.periods[self.has_period])
        # build search
        if self.has_action == RipperConst.SEARCH:
            self.parm('search_tag', self.tags2str())
        # build random
        if self.has_action == RipperConst.RANDOM:
            self.has_page = random.randint(0, 5000)
        # '''others'''

        # build rating
        if self.has_action == self.actions[RipperConst.NEW.value]:  # post
            self.__buildRating()
        # build token
        await self.__buildToken()
        self.parm('type', 'json')
        self.__buildVariant()

    async def get(self, offest=0, limit=40) -> 'list':
        await self.__build()
        # params = {}
        connector: ProxyConnector = ProxyConnector()
        proxy = ymConfig.getConfig('setting').get('proxy')
        if proxy:
            connector = ProxyConnector.from_url(proxy)
        data: list = []
        for k, t in self.rips.items():
            async with aiohttp.request('GET', k, connector=connector) as response:
                raw = await response.read()
            logger.debug(k + f"\n[{t[0]}, {t[1]}]")
            data = data + json.loads(raw)['posts'][t[0]:t[1]]
        result: [AnipicData] = []
        for one in data:
            anipic: AnipicData = AnipicData()
            one['file_url'] = f"https://images.anime-pictures.net/{one['md5'][0:3]}/{one['md5'] + one['ext']}"
            anipic.__dict__.update(one)
            async with aiohttp.request('GET', f'https://anime-pictures.net/pictures/view_post/{anipic.id}?type=json',
                                       connector=connector,
                                       timeout=aiohttp.ClientTimeout(20)) as oneInfo:
                meta = json.loads(await oneInfo.read())
                anipic.tags = meta['tags']
            result.append(anipic)
        if connector:
            await connector.close()
        return result

    async def __buildToken(self):
        token: str = ymConfig.getConfig('anipic').get('token')
        if not token:
            token = 'a_0'
        token_arr = token.split('_')
        if int(time.time()) - int(token_arr[1]) > 60 * 60 * 24 * 30:
            token = await self.fetToken
            ymConfig.getConfig('anipic').set('token', token + (f'_{int(time.time())}' if token else ''))
            self.token = token
            await ymConfig.save('anipic')
            logger.debug('Token expired! fetched!')
        else:
            self.token = token_arr[0]
            logger.info('Token usable!')
        if self.token:
            self.parm('token', self.token)

    def __buildVariant(self, offset: int = 0):
        page = self.has_page
        self.ripe = self.rip
        if self.has_offset + self.has_count >= self.per_page:
            self.rip = self.rip.replace('s/0?', f's/{page}?')
            self.rips[self.rip] = (self.has_offset, self.per_page)
            self.ripe = self.ripe.replace('s/0?', f's/{page + 1}?')
            self.rips[self.ripe] = (0, self.has_count - (self.per_page - self.has_offset))
        else:
            self.rip = self.rip.replace('s/0?', f's/{page}?')
            self.rips[self.rip] = (self.has_offset, self.has_count + self.has_offset)

    def __buildRating(self) -> 'AnipicRipper':
        if self.has_action == RipperConst.NEW:
            if ymConfig.getConfig('setting').get('enable_rating_check') != 'disable' and self.has_rating:
                pos = self.rip.find('erotic')
                if pos != -1:
                    if self.has_rating != '2':
                        self.rip = self.rip.replace('erotic', '')
                        self.parm('denied_tags', 'erotic')
                else:
                    if self.has_rating != '2':
                        self.parm('denied_tags', 'erotic')
                # info(f"new url {self.rip}")
        return self

    def tags2str(self) -> str:
        taster = ''
        for tag in self.has_tags:
            if tag:
                taster += tag + '%20'
        taster = taster[:-3].replace('&&', '%26%26')
        return taster

    @property
    async def fetToken(self) -> 'str':
        connector: ProxyConnector = ProxyConnector()
        proxy = ymConfig.getConfig('setting').get('proxy')
        if proxy:
            connector = ProxyConnector.from_url(proxy)
        user = ymConfig.getConfig('anipic').get('user')
        password = ymConfig.getConfig('anipic').get('password')

        async with aiohttp.request('POST', 'https://anime-pictures.net/login/submit',
                                   params={'login': user, 'password': password}, connector=connector) as response:
            raw = await response.read()
            if connector:
                await connector.close()
        result = json.loads(raw)
        if result['success']:
            return result['token']
        else:
            return ''
