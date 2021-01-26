import hashlib
import json
import time
from datetime import datetime, timezone

import aiohttp
from aiohttp_socks import ProxyConnector
from application.YummyPicture import ymConfig
from application.YummyPicture.Ripper import *
from application.YummyPicture.yummy.pixiv.PixivData import PixivData


class PixivRipper(Ripper):
    token = ''
    user = dict()
    client_id = 'KzEZED7aC0vird8jWyHM38mXjNTY'
    client_secret = 'W9JZoJe00qPvJsiyCGT3CCtC6ZUtdpKpzMbNlUGP'
    login_secret = '28c1fdd170a5204386cb1313c7077b34f83e4aaf4aa829ce78c231e05b0bae2c'
    token_url = 'https://oauth.secure.pixiv.net/auth/token'
    periods_list: list = [{'1d': 'day', '1w': 'week', '1m': 'month', 'dm': 'day_male', 'df': 'day_female',
                           'wo': 'week_original', 'wr': 'week_rookie', 'dmn': 'day_manga', 'wg': 'week'},
                          {'1d': 'day_r18', '1w': 'week_r18', '1m': 'month_r18',
                           'dm': 'day_male_r18', 'df': 'day_female_r18', 'wg': 'week_r18g'}
                          ]

    # 每日 | http: // www.pixiv.net / ranking.php?format = json & mode = daily & p = 1
    # 每日r18 | http: // www.pixiv.net / ranking.php?format = json & mode = daily_r18 & p = 1
    # 每日r18g | http: // www.pixiv.net / ranking.php?format = json & mode = daily_r18g & p = 1
    # 每周 | http: // www.pixiv.net / ranking.php?format = json & mode = weekly & p = 1
    # 每周r18 | http: // www.pixiv.net / ranking.php?format = json & mode = weekly_r18 & p = 1
    # 每日
    # r18g | http: // www.pixiv.net / ranking.php?format = json & mode = weekly_r18g & p =
    def __init__(self):
        super(PixivRipper, self).__init__()
        post: str = 'search/illust'
        recommend: str = 'illust/recommended'
        self.actions = dict(new=recommend, search=post, random=recommend, popular='illust/ranking')
        self.periods = self.periods_list[0]
        self.rip = 'https://app-api.pixiv.net/v1/'
        self.per_page = 30
        self.access_token = ymConfig.getConfig('pixiv').get('access_token')
        self.restrict = 1

    async def __build(self):
        # build action
        self.parse(self.actions[self.has_action.value] + '?')
        # build option
        if self.has_action == RipperConst.NEW:
            self.parm('content_type', 'illust').parm('include_ranking_label', 'true')
        # build rating
        self.__buildRating()
        # bind popular
        if self.has_action == RipperConst.POPULAR:
            self.parm('mode', self.periods[self.has_period])
        # build search
        if self.has_action == RipperConst.SEARCH:
            self.parm('word', self.tags2str()).parm('search_target', 'partial_match_for_tags').parm('sort', 'date_desc')
        # build random
        if self.has_action == RipperConst.RANDOM:
            self.parm('content_type', 'illust').parm('include_ranking_label', 'true')
        # '''others'''
        self.parm('filter', 'for_ios')
        # build rating
        if self.has_action == self.actions[RipperConst.NEW.value]:  # post
            pass
        # build token
        await self.__buildToken()
        self.__buildVariant()

    async def get(self) -> 'list':
        await self.__build()
        connector: ProxyConnector = self.getConnector()
        data: list = []
        headers: dict = dict(Authorization='Bearer ' + self.access_token)
        for k, t in self.rips.items():
            logger.debug(k + f"\n[{self.has_offset}, {self.has_offset + self.has_count}]")
            async with aiohttp.request('GET', k, connector=connector, headers=headers) as response:
                raw = await response.read()
            data = data + json.loads(raw)['illusts'][t[0]: t[1]]
        await connector.close()
        result: [PixivData] = []
        for one in data:
            pixiv: PixivData = PixivData()
            pixiv.__dict__.update(one)
            result.append(pixiv)
        return result

    async def __buildToken(self):
        expire_time = ymConfig.getConfig('pixiv').get('time')
        if expire_time < time.time():
            logger.info('token expired! fetching!')
            await self.fetchToken()

    def __buildVariant(self):
        self.parm('offset', self.has_offset.__str__())
        self.rips[self.rip] = (0, self.has_count)

    def __buildRating(self) -> 'PixivRipper':
        if int(self.has_rating) < 6:
            self.periods = self.periods_list[0]
        else:
            self.periods = self.periods_list[1]
        return self

    def tags2str(self) -> str:
        taster = ''
        for tag in self.has_tags:
            if tag:
                taster += tag + '%20'
        taster = taster[:-3].replace('&&', '%26%26')
        return taster

    @classmethod
    def getConnector(cls):
        connector: ProxyConnector = ProxyConnector()
        if proxy := ymConfig.getConfig('setting').get('proxy'):
            connector = ProxyConnector.from_url(proxy)
        return connector

    async def fetchToken(self) -> 'str':
        connector: ProxyConnector = self.getConnector()
        client_time = datetime.utcnow().replace(microsecond=0).replace(tzinfo=timezone.utc).isoformat()
        username = ymConfig.getConfig('pixiv').get('username')
        password = ymConfig.getConfig('pixiv').get('password')
        refresh_token = ymConfig.getConfig('pixiv').get('refresh_token')
        if refresh_token:
            gt = 'refresh_token'
            int_key: dict = dict(refresh_token=refresh_token)
            logger.info('using token')
        elif username and password:
            gt = 'password'
            int_key: dict = dict(username=username, password=password)
            logger.info('using password')
        else:
            raise KeyError()
        data: dict = dict(client_id=self.client_id, client_secret=self.client_secret, get_secure_url=1, grant_type=gt)
        data.update(int_key)
        headers = {'X-Client-Time': client_time,
                   'X-Client-Hash': hashlib.md5((client_time + self.login_secret).encode('utf-8')).hexdigest()}
        async with aiohttp.request('POST', self.token_url, data=data, connector=connector, headers=headers) as result:
            ret = json.loads(await result.read())
            ymConfig.getConfig('pixiv').set('access_token', ret['response']['access_token'])
            ymConfig.getConfig('pixiv').set('refresh_token', ret['response']['refresh_token'])
            ymConfig.getConfig('pixiv').set('time', ret['expires_in'] + time.time())
            self.access_token = ret['response']['access_token']
            await ymConfig.save('pixiv')
            await connector.close()

    async def do_illustration(self):
        pass
