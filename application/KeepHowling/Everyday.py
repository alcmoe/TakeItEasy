from graia.application import GraiaMiraiApplication as Slave, Image
from graia.application.message.chain import MessageChain as MeCh

from Listener import Listener
from utils.network import request
from utils.thread import repeatSchedule
from . import logger, thread, khConfig
from bs4 import BeautifulSoup


class Everyday(Listener):

    @staticmethod
    async def fetchNews(app):
        groups: list = khConfig.getConfig('everyday').get('news_subscript_groups')
        link = 'https://mp.weixin.qq.com/s/ymjoh0HTgsniyYsOjy79-A'
        logger.info('fetching' + link)
        data = await request('GET', link)
        full = BeautifulSoup(data, "html.parser")
        element = full.find_all('div', {'class': 'share_media'})[0].find('img')['src']
        image: Image = Image.fromUnsafeAddress(element)
        for group in groups:
            await app.sendGroupMessage(group, MeCh.create([image]))

    def task(self):
        from Roll import app
        thread.createTask(repeatSchedule(9, 0, 0, self.fetchNews, (app,)))
