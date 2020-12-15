import os
import asyncio
import random

from graia.application import GraiaMiraiApplication as Slave, GroupMessage, UploadMethods
from graia.application.group import MemberPerm
from graia.application.message.chain import MessageChain as MeCh, MessageChain
from graia.application.message.elements.internal import At, Plain, Quote, Image
from graia.broadcast import ExecutionStop, Broadcast
from graia.broadcast.builtin.decoraters import Depend

from . import ttkConfig, logger
from utils.network import requestText, sentiment, refreshSentimentToken, json, request
from application.YummyPicture.PictureRipperListener import PictureRipperListener
from Listener import Listener


class TalkToMeListener(Listener):
    bcc: Broadcast
    try:
        from application.Economy import Economy

        Economy = Economy
        price = 5
    except ImportError:
        Economy = None

    APP_COMMANDS = ['啊？', '吃什么', '不']
    APP_QUOTE_AT_COMMANDS = ['骂他', '翻译翻译']
    nm_api = ttkConfig.getConfig('setting').get('nm_api')
    n_api = ttkConfig.getConfig('setting').get('n_api')
    chp_api = ttkConfig.getConfig('setting').get('chp_api')
    fy_api = ttkConfig.getConfig('setting').get('fy_api')
    capitalist = 0

    def run(self):
        @self.bcc.receiver(GroupMessage, headless_decoraters=[Depend(self.atOrQuoteFilter)])
        async def groupAtOrQuoteHandler(app: Slave, message: GroupMessage):
            await self.atOrQuoteHandler(app, message)

        @self.bcc.receiver(GroupMessage, headless_decoraters=[Depend(self.cmdFilter)])
        async def groupCmdHandler(app: Slave, message: GroupMessage):
            await self.commandHandler(app, message)

        @self.bcc.receiver(GroupMessage)
        async def groupMessageHandler(app: Slave, message: GroupMessage):
            await self.shutTheFuckUp(app, message)
            if self.Economy:
                add = 0
                if images := message.messageChain.get(Image):
                    image: Image
                    for image in images:
                        by: bytes = await request(url=image.url)
                        add += 1 if len(by) > 100000 else 0
                else:
                    add += 1 if random.randint(0, 10) < 2 else 0
                if add:
                    for _ in range(0, add):
                        await self.Economy.Economy.addMoney(message.sender.id, 5)
                        await self.Economy.Economy.addValue(5)
                await self.Economy.Economy.trySave()

    def cmdFilter(self, message: MessageChain):
        if cmd := message.asDisplay().split(' '):
            cmd = cmd[0].upper()
            if not any(app_cmd in cmd for app_cmd in self.APP_COMMANDS):
                raise ExecutionStop()
            message.__dict__.update(cmd=cmd)
        else:
            raise ExecutionStop()

    @staticmethod
    def atOrQuoteFilter(message: MessageChain):
        if not message.has(Quote) and not message.has(At):
            raise ExecutionStop()
        cmd = None
        if plains := message.get(Plain):
            for text in plains:
                if text.__dict__['text'].strip() in PictureRipperListener.QUOTE_COMMANDS:
                    raise ExecutionStop()
                if text.__dict__['text'].strip() in TalkToMeListener.APP_QUOTE_AT_COMMANDS:
                    cmd = text.__dict__['text'].strip().upper() if not cmd else cmd
        at: At
        quote: Quote
        target = [at.target for at in message.get(At)] + [quote.senderId for quote in message.get(Quote)]
        quote = message.get(Quote)[0] if message.get(Quote) else []
        text = message.get(Plain) + (quote.origin.get(Plain) if quote else quote)
        message.__dict__.update(target=target, cmd=cmd, text=text)

    async def commandHandler(self, app: Slave, message: GroupMessage):
        cmd: str = message.messageChain.__dict__.get('cmd')
        if cmd == '啊？':
            await self.sendPhilosophy(app, message)
        if '不' in cmd and len(cmd) > 2:
            if (pos := cmd.find('不')) != -1:
                if cmd[pos - 1] == cmd[pos + 1]:
                    msg = [Plain(cmd[pos - 1] if random.randint(0, 1) else f'不{cmd[pos - 1]}')]
                    await app.sendGroupMessage(message.sender.group, MeCh.create(msg))
        if cmd == '吃什么':
            rate = random.randint(0, 100)
            if rate < 2:
                eat = '吃屎吧'
            else:
                what_we_eat = ttkConfig.getConfig('setting').get('what_we_eat')
                index = random.randint(0, len(what_we_eat) - 1)
                eat = f'吃{what_we_eat[index]}'
            await app.sendGroupMessage(message.sender.group, MeCh.create([Plain(eat)]))

    async def atOrQuoteHandler(self, app, message: GroupMessage):
        logger.debug('TalkToMe at handler act')
        cmd: str = message.messageChain.__dict__.get('cmd')
        target = list(set(message.messageChain.__dict__.get('target')))
        if fencing := app.connect_info.account in target:
            target.remove(app.connect_info.account)

        if cmd == self.APP_QUOTE_AT_COMMANDS[0]:
            if self.Economy:
                if not await self.Economy.Economy.pay(message.sender.id, self.Economy.capitalist, 500):
                    info: dict = await self.Economy.Economy.money(message.sender.id)
                    plain: Plain = Plain(
                        f"你的{self.Economy.unit}不足,你还剩{info['balance']}只{self.Economy.unit},单价500只{self.Economy.unit}")
                    await app.sendGroupMessage(message.sender.group, MeCh.create([plain]))
                    return
            else:
                if message.sender.permission == MemberPerm.Member:
                    await app.sendGroupMessage(message.sender.group, MeCh.create([Plain('你骂你爹呢')]))
                    return
            if target:
                for _ in range(0, random.randint(2, 10)):
                    msg = [At(target) for target in target]
                    love = await requestText(self.nm_api)
                    msg.append(Plain(love[0]))
                    await app.sendGroupMessage(message.sender.group, MeCh.create(msg))
                    await asyncio.sleep(2)
                    msg.clear()
            return
        if cmd == self.APP_QUOTE_AT_COMMANDS[1]:
            if text := self.getFirstTrimText(message.messageChain.__dict__.get('text')):
                items: dict = (await requestText(self.fy_api, 'POST', data={'text': text}, raw=False))[0]
                msg = [Plain('能不能好好说话')]
                for item in items:
                    if 'trans' not in item.keys():
                        continue
                    msg.append(Plain(f"\n{item['name']}->{json.dumps(item['trans'], ensure_ascii=False)}"))
                await app.sendGroupMessage(message.sender.group, MeCh.create(msg))
            return
        if fencing:  # call bot
            if text := self.getFirstTrimText(message.messageChain.__dict__.get('text')):
                sent = await self.trySentiment(text)
                if sent[0] == 0:
                    url = self.nm_api if sent[1] > 0.5 else self.nm_api
                elif sent[0] == 2:
                    url = self.chp_api
                else:
                    return
                love = await requestText(url)
                msg = [At(message.sender.id), Plain(love[0])]
                await app.sendGroupMessage(message.sender.group, MeCh.create(msg))
            else:
                return

    async def shutTheFuckUp(self, app: Slave, message: GroupMessage):
        rands = [random.randint(0, 999) for _ in range(0, 4)]
        if rands[0] < 12:
            plain: Plain = message.messageChain.get(Plain)
            if plain:
                await app.sendGroupMessage(message.sender.group.id, MeCh.create(plain))
        if rands[1] < 12:
            await app.sendGroupMessage(message.sender.group.id, MeCh.create([Plain('确实')]))
        if rands[2] < 12:
            if random.randint(1, 3) < 2:
                msg = MeCh.create([At(message.sender.id), Plain('我爱你')])
                await app.sendGroupMessage(message.sender.group.id, msg)
            else:
                if message.messageChain.has(Plain):
                    plain: Plain = message.messageChain.get(Plain)[0]
                    sent = await self.trySentiment(plain.text)
                    if sent[0] == 0:
                        url = self.nm_api if sent[1] > 0.7 else self.nm_api
                    else:
                        return
                    love = await requestText(url)
                    msg = [At(message.sender.id), Plain(love[0])]
                    await app.sendGroupMessage(message.sender.group, MeCh.create(msg))
        if rands[3] < 12:
            await self.sendPhilosophy(app, message)

    @staticmethod
    async def trySentiment(words: str) -> list:
        access_token = ttkConfig.getConfig('setting').get('bd_sentiment_access_token')
        try:
            return await sentiment(words, access_token)
        except KeyError:
            logger.debug(words)
            api_key = ttkConfig.getConfig('setting').get('bd_sentiment_API_key')
            secret_key = ttkConfig.getConfig('setting').get('bd_sentiment_secret_key')
            new_token = await refreshSentimentToken(api_key, secret_key)
            ttkConfig.getConfig('setting').set('bd_sentiment_access_token', new_token)
            await ttkConfig.save('setting')
            logger.debug('bd sentiment token saved')
            return await sentiment(words, new_token)

    @staticmethod
    async def sendPhilosophy(app: Slave, message):
        path = f'res/voice/philosophy/'
        files = os.listdir(f'res/voice/philosophy/')
        randint = random.randint(0, len(files) - 1)
        file = path + files[randint]
        logger.info(file)
        with open(file=file, mode='rb') as f:
            voice = await app.uploadVoice(f.read(), UploadMethods.Group)
        mc = MeCh.create([voice])
        f.close()
        await app.sendGroupMessage(message.sender.group, mc)

    @staticmethod
    def getFirstTrimText(plains: [Plain]) -> str:
        text = None
        for plain in plains:
            if plain.text.strip() and plain.text.strip() not in TalkToMeListener.APP_QUOTE_AT_COMMANDS:
                text = plain.text.strip()
                break
        return text
