import re
import time

from aiohttp_socks import ProxyConnector
from bs4 import BeautifulSoup

from utils.network import request, requestText, aiohttp
from utils.thread import asyncio
from application.VideoRipper import vrConfig, logger


class IwaraRipper:
    host = 'https://ecchi.iwara.tv'
    url = 'https://ecchi.iwara.tv/users/Alcatraz_Mentha/following'
    download_api = 'https://ecchi.iwara.tv/api/video/'
    ripper = vrConfig.getConfig('setting').get('ripper')
    user = vrConfig.getConfig(ripper).get('user')

    def __init__(self):
        self.following = vrConfig.getConfig(self.ripper).get('following')
        self.user_videos = vrConfig.getConfig(self.ripper).get('user_videos')
        self.id2users: dict = vrConfig.getConfig(self.ripper).get('id2users')

    async def getFollowing(self, user_link):  # /users/Alcatraz_Mentha'必须从主页开始,
        my_id_info = await self.userId(user_link, False)
        await self.getFollowingList(my_id_info[0], my_id_info[1])

    async def getFollowingList(self,  my_id: str, user_follow_link: str) -> 'list':
        connector: ProxyConnector = await IwaraRipper.getConnector()
        find = ['div', 'field-content']
        logger.info('checking following ' + self.host + user_follow_link)
        raw_data = await request('GET', self.host + user_follow_link, connector=connector)
        soup = BeautifulSoup(raw_data, "lxml")
        sear = soup.find_all(find[0], class_=find[1])
        for user_element in sear:
            user_link: str = user_element.contents[0]['href']
            user_avatar_link: str = user_element.contents[0].contents[0]['src']
            if 'pictures/picture-' in user_avatar_link:
                user_id = '/user/' + user_avatar_link.split('-')[1]
            else:
                user_id = await self.userId(user_link)
            if not self.following.get(my_id):
                self.following[my_id] = []
            self.following[my_id].append(user_id)
        page_find = ['li', 'pager-next']
        pager = soup.find_all(page_find[0], class_=page_find[1])
        if pager:
            next_page = pager[0].contents[0]['href']
            await self.getFollowingList(my_id, next_page)
        else:
            await vrConfig.save('iwara')

    async def userId(self, user, only_id: bool = True):
        if user in self.id2users.values() and only_id:
            rev: dict = dict(zip(self.id2users.values(), self.id2users.keys()))
            return rev[user]
        else:
            uid_info = await IwaraRipper.getUserId(user, only_id)
            uid = uid_info if only_id else uid_info[0]
            logger.info(f'fetched {user} の　real id {uid}')
            self.id2users[uid] = user
            await vrConfig.save('iwara')
            return uid_info

    async def checkFollowing(self):
        await self.getFollowing(f'/users/{self.user}/following')

    @staticmethod
    async def loginKey():
        logger.info('getting login key')
        connector: ProxyConnector = await IwaraRipper.getConnector()
        html = await request('GET', 'https://ecchi.iwara.tv/user/login', connector=connector)
        full = BeautifulSoup(html, "html.parser")
        h = full.find("head")
        capture = h.find("script", text=re.compile("antibot")).string.strip()
        start = capture.find("\"key\":") + 7  # "key":"
        end = capture.find("\"", start)
        return capture[start:end]

    @staticmethod
    async def getUserId(user_link: str, only_id: bool):
        logger.info(f'getting [{user_link}] real id')
        connector: ProxyConnector = await IwaraRipper.getConnector()
        html = await request('GET', IwaraRipper.host + user_link, connector=connector)
        full = BeautifulSoup(html, "html.parser")
        h = full.find("head")
        capture = h.find("script", text=re.compile("views")).string.strip()
        start = capture.find("\"view_path\":") + 13
        end = capture.find("\"", start)
        result = '/' + capture[start:end].replace('\\', '')
        if not only_id:
            following = full.find('div', class_='more-link').contents[1]['href']
            result = [result, following]
        return result

    async def checkCookie(self):
        cookie_str = vrConfig.getConfig('iwara').get('cookies')
        cookie_exp = vrConfig.getConfig('iwara').get('cookies_expire')
        if not cookie_str or time.time() > cookie_exp + 15 * 24 * 60 * 60:
            logger.info('cookie expired. fetching')
            cookie = await self.fetchCookie()
            logger.info('new cookie fetched')
            vrConfig.getConfig('iwara').set('cookies', cookie)
            vrConfig.getConfig('iwara').set('cookies_expire', time.time())
            await vrConfig.save('iwara')

    async def fetchCookie(self):
        login_key = await self.loginKey()
        data = {
            'name': self.user,
            'pass': vrConfig.getConfig(self.ripper).get('password'),
            'form_build_id': "form-jacky",
            'form_id': 'user_login',
            'antibot_key': login_key,
            'op': '%E3%83%AD%E3%82%B0%E3%82%A4%E3%83%B3'
        }
        connector: ProxyConnector = await IwaraRipper.getConnector()
        async with aiohttp.ClientSession(connector=connector) as session:
            async with session.post("https://ecchi.iwara.tv/user/login", data=data) as _:
                cookie = session.cookie_jar.filter_cookies("https://ecchi.iwara.tv/user/login")
                if connector:
                    await connector.close()
                logger.info('fetching cookie ' + cookie.__str__()[12:])
        return cookie.__str__()[12:]

    async def getVideoTask(self):
        tasks = []
        if not vrConfig.getConfig('iwara').get(self.user):
            for user in self.following:
                task = asyncio.create_task(self.getUserVideos(user))
                await asyncio.wait([task], timeout=1)
            await asyncio.wait(tasks)

    async def checkSubscriptionsUpdate(self):
        await self.checkCookie()
        cookie_map: list = vrConfig.getConfig('iwara').get('cookies').split('=')
        cookie = {cookie_map[0]: cookie_map[1]}
        new_videos = await self.getUserVideos('', '/subscriptions', cookie)
        return new_videos

    async def getUserVideos(self, user_link, videos: str = '/videos', cookie=None) -> 'list':
        co: str = user_link + videos
        connector: ProxyConnector = await IwaraRipper.getConnector()
        logger.info('get user videos ' + self.host + co)
        raw_data = await request('GET', self.host + co, cookies=cookie, connector=connector)
        soup = BeautifulSoup(raw_data, "lxml")
        find = ['div', 'node node-video node-teaser node-teaser clearfix']
        sear = soup.find_all(find[0], class_=find[1])
        new_videos = []
        for video_col_element in sear:
            is_public = 0 if video_col_element.contents[3].attrs['class'][0] == 'private-video' else 1
            user_link = video_col_element.contents[-2]['href']
            author = video_col_element.contents[-2].string
            user_id = await self.userId(user_link)
            find = ['div', 'field-item even']
            video_element = video_col_element.find_all(find[0], class_=find[1])
            try:
                video_link = video_element[0].contents[0]['href']
            except IndexError:
                logger.info('test,' + self.host+co)
                return

            is_video = 0 if 'images' in video_link else 1
            video_thumbnail = video_element[0].contents[0].contents[0]['src']
            is_youtube = 1 if 'youtube' in video_thumbnail else 0
            if not self.user_videos.get(user_id):
                self.user_videos[user_id] = {}
            if not self.user_videos[user_id].get(video_link):
                video_dict = dict(video_id=video_link[8:], author=author, public=is_public, video=is_video,
                                  url=video_link, thumbnail=video_thumbnail, youtube=is_youtube)
                new_videos.append([user_id, video_link])
                self.user_videos[user_id][video_link] = video_dict
        await vrConfig.save('iwara')
        return new_videos

    async def getVideo(self, video_link) -> 'list':
        connector: ProxyConnector = await IwaraRipper.getConnector()
        raw_data = await request('GET', self.host + video_link, connector=connector)
        logger.info('get video info ' + self.host + video_link)
        soup = BeautifulSoup(raw_data, "lxml")
        find = ['div', 'node node-video node-full clearfix']
        sear = soup.find_all(find[0], class_=find[1])[0]
        info_find = ['div', 'node-info']
        video_info_node = sear.find_all(info_find[0], class_=info_find[1])
        video_title = video_info_node[0].contents[1].contents[3].string
        video_time = video_info_node[0].contents[1].contents[6].strip()
        description_find = ['div', 'field field-name-body field-type-text-with-summary field-label-hidden']
        description_node = video_info_node[0].find_all(description_find[0], class_=description_find[1])
        video_info = ''
        if description_node:
            video_infos = description_node[0].contents[0].contents[0].contents[0].contents
            for info in video_infos:
                if isinstance(info, str):
                    video_info += info
                else:
                    try:
                        video_info += info.string
                    except TypeError:
                        pass
        user_info_node = video_info_node[0].contents[1].contents[5]
        user_link = user_info_node['href']
        user_id = await self.userId(user_link)
        video = self.user_videos[user_id][video_link]
        video['title'] = video_title
        video['info'] = video_info
        video['time'] = video_time
        if not video['youtube'] or not video['video']:
            thumbnail_find = ['video', 'video-js vjs-default-skin hidden']
            video_thumbnail = sear.find_all(thumbnail_find[0], class_=thumbnail_find[1])[0]['poster']
            connector: ProxyConnector = await IwaraRipper.getConnector()
            links = await requestText(self.download_api + video_link[8:], connector=connector, raw=False)
            for i, _ in enumerate(links[0]):
                links[0][i]['uri'] = 'https:' + links[0][i]['uri']
            video_links = links[0]
            video['thumbnail'] = 'https:' + video_thumbnail
            video['downloads'] = video_links
        await vrConfig.save('iwara')
        return video

    @staticmethod
    async def getConnector() -> ProxyConnector:
        connector: ProxyConnector = ProxyConnector()
        if proxy := vrConfig.getConfig('setting').get('proxy'):
            connector = ProxyConnector.from_url(proxy)
        return connector
