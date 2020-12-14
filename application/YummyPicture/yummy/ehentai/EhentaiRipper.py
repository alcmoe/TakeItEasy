import json
import random
import aiohttp
from aiohttp_socks import ProxyConnector
from bs4 import BeautifulSoup

from application.YummyPicture import ymConfig
from application.YummyPicture.Ripper import *
from application.YummyPicture.yummy.ehentai import EhentaiData


class EhentaiRipper(Ripper):
    per_pages: dict = dict(popular=50, detail=40, new=25, search=25, random=25)
    cats: dict = dict(doujinshi=2, manga=4, artist_cg=8, game_cg=16, western=512, non_h=256, image_set=32, cosplay=64,
                      asian_porn=128, misc=1)
    category: int = 1023 - cats['doujinshi'] - cats['manga'] - cats['image_set'] - cats['artist_cg']
    gr: str = 'h'
    gdr: str = ''
    api: str = 'https://api.e-hentai.org/api.php/'

    def __init__(self):
        super(EhentaiRipper, self).__init__()
        self.actions = dict(new='', search='', random='', popular='post/popular', detail='g')
        self.rip = 'https://e-hentai.org/'
        self.per_page = 25

    def __build(self):
        # build action
        self.parse(self.actions[self.has_action.value] + '?')
        # build option
        self.per_page = self.per_pages[self.has_action]
        # ...
        # build search
        if self.has_action == RipperConst.SEARCH:
            self.parm('f_search', self.tags2str())
        # build random
        if self.has_action == RipperConst.RANDOM:
            self.has_page = random.randint(0, 5000)
        if self.has_action == RipperConst.DETAIL:
            self.__buildSpecific()
        else:
            self.parm("f_cats", str(self.category))
        # '''others'''

        # build rating
        if self.has_action == self.actions[RipperConst.NEW.value]:  # post
            self.__buildRating()
        if self.has_action == RipperConst.DETAIL:
            self._buildVariant()
        else:
            super()._buildVariant()

    async def get(self) -> 'list':
        self.__build()
        cookies = {'nw': '1'}
        connector: ProxyConnector = ProxyConnector()
        proxy = ymConfig.getConfig('setting').get('proxy')
        if proxy:
            connector = ProxyConnector.from_url(proxy)
        if self.has_action != RipperConst.DETAIL:
            find = ['table', 'itg gltc']
        else:
            find = ['div', 'gdtm']
        result: [EhentaiData] = []
        for k, t in self.rips.items():
            logger.debug(k + f"\n[{t[0]}, {t[1]}]")
            async with aiohttp.request('GET', k, cookies=cookies, connector=connector) as response:
                soup = BeautifulSoup((await response.read()).decode("utf-8"), "lxml")
            sear = soup.find_all(find[0], class_=find[1])
            if self.has_action == RipperConst.DETAIL:
                sear = sear[t[0]:t[1]]  # no ads
                for one in sear:
                    link = one.contents[0].contents[0]['href']
                    async with aiohttp.request('GET', link, connector=connector) as oneInfo:
                        url = BeautifulSoup(await oneInfo.read(), "lxml").find_all('img', id='img')[0]['src']
                    ehentai: EhentaiData = EhentaiData()
                    ehentai.__dict__.update({'preview': url})
                    result.append(ehentai)
            else:
                rm = self.per_pages[self.has_action]
                tables = sear[0].contents[1:rm + 1]
                tables += sear[0].contents[rm + 2:]
                tables = tables[t[0]:t[1]]
                for ga in tables:
                    la = ga.contents[2].contents[0]['href'].split('/')
                    body = {"method": "gdata", "gidlist": [[int(la[-3]), la[-2]]], "namespace": 1}
                    json.dumps(body, indent=1)
                    async with aiohttp.request('POST', self.api, json=body, connector=connector,
                                               timeout=aiohttp.ClientTimeout(20)) as oneInfo:
                        one = json.loads(await oneInfo.read())
                    ehentai: EhentaiData = EhentaiData()
                    ehentai.__dict__.update(one['gmetadata'][0])
                    ehentai.gr = self.gr
                    ehentai.id = ehentai.gid
                    ehentai.preview = f"https://ehgt.org/m/{str(1000000000 + int(la[-3]))[1:7]}/{la[-3]}-00.jpg"
                    result.append(ehentai)
        await connector.close()
        return result

    def __buildSpecific(self):
        gallery = self.has_specific[0][0].split('/')
        db = self.has_specific[1]
        gid = gallery[0]
        try:
            token = db.database[gid]['token']
            self.gdr = db.database[gid]['gr']
            self.rip = self.rip.replace('/g?', '/g/')
            return self.parse(f'{gid}/{token}/')
        except KeyError:
            return self.parse(f'{gallery[0]}/{gallery[1]}/')

    def __buildRating(self) -> 'EhentaiRipper':
        if ymConfig.getConfig('setting').get('enable_rating_check') != 'disable' and self.has_rating:
            if self.has_action == RipperConst.DETAIL:
                if self.has_rating == 'h' and self.gdr and self.gdr == 'non-h':
                    self.rip = self.rip.replace('/g/', '/k/')
                    return self
            if self.has_rating == 'non-h':
                self.gr = 'non-h'
                self.category -= self.cats['non_h']
        return self

    def tags2str(self) -> str:
        taster = ''
        for tag in self.has_tags:
            if tag:
                taster += tag + '+'
        return taster[:-1]

    def offset(self, offset: str) -> 'EhentaiRipper':
        self.per_page = self.per_pages[self.has_action]
        self.has_page = int(offset) // self.per_page
        self.has_offset = int(offset) % self.per_page
        return self

    def _buildVariant(self, offset: int = 0):
        page = self.has_page + offset
        self.ripe = self.rip
        if self.has_offset + self.has_count > self.per_page:
            self.parm('p', str(page))
            self.rips[self.rip] = (self.has_offset, self.per_page)
            self.parm('p', str(int(page) + 1), True)
            self.rips[self.ripe] = (0, self.has_count - (self.per_page - self.has_offset))
        else:
            self.parm('p', str(page))
            self.rips[self.rip] = (self.has_offset, self.has_count + self.has_offset)

    def period(self, period: str) -> 'EhentaiRipper':
        self.per_page = self.per_pages[self.has_action]
        return self
