import asyncio
import os
import random
import time

from graia.application import GraiaMiraiApplication as Slave, GroupMessage, UploadMethods
from graia.application.group import MemberPerm
from graia.application.message.chain import MessageChain as MeCh
from graia.application.message.elements.internal import At, Plain, Quote

from . import ttkConfig, logger
from utils.network import requestText, sentiment, refreshSentimentToken, json

Tick = {}
BlockedKeywords = ['x2', '图源', '好', '我不喜欢']
nm_api = ttkConfig.getConfig('setting').get('nm_api')
n_api = ttkConfig.getConfig('setting').get('n_api')
chp_api = ttkConfig.getConfig('setting').get('chp_api')
fy_api = ttkConfig.getConfig('setting').get('fy_api')
APP_COMMANDS = ['啊？', '骂他', '吃什么', '不']
try:
    from application.Economy import Economy

    Economy = Economy
    price = 5
except ImportError:
    Economy = None


async def TalkToMe(app: Slave, message: GroupMessage, commands: list):
    try:
        if any(acm in commands[0] for acm in APP_COMMANDS):
            await commandHandler(app, message, commands)
        await shutTheFuckUp(app, message)
        await fencing(app, message)
    except IndexError:
        print(f'!!!!!!!!!!!!!!!!!!!!!!!!!!!!!{commands}\n{message.messageChain}')


async def commandHandler(app: Slave, message: GroupMessage, commands: list):
    cmd: str = commands[0]
    if cmd == '啊？':
        await sendPhilosophy(app, message)
    if cmd == '骂他':
        '''if message.sender.permission == MemberPerm.Member:
            await app.sendGroupMessage(message.sender.group, MeCh.create([Plain('你骂你爹呢')]))
            return
        '''
        if Economy:
            if not await Economy.Economy.pay(message.sender.id, Economy.capitalist, 500):
                info: dict = await Economy.Economy.money(message.sender.id)
                plain: Plain = Plain(f"你的{Economy.unit}不足,你还剩{info['balance']}只{Economy.unit},单价500只{Economy.unit}")
                await app.sendGroupMessage(message.sender.group, MeCh.create([plain]))
                return
        else:
            if message.sender.permission == MemberPerm.Member:
                await app.sendGroupMessage(message.sender.group, MeCh.create([Plain('你骂你爹呢')]))
                return
        if ats := message.messageChain.get(At):
            for a in range(0, random.randint(2, 10)):
                msg = ats.copy()
                love = await requestText(nm_api)
                msg.append(Plain(love[0]))
                await app.sendGroupMessage(message.sender.group, MeCh.create(msg))
                await asyncio.sleep(2)
                msg.clear()
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
    '''
    if cmd == 'reo':
        di = ttkConfig.getConfig('setting').get('what_we_eat')
        c = list(set(
            di + ["馄饨", "拉面", "烩面", "热干面", "刀削面", "油泼面", "炸酱面", "炒面", "重庆小面", "米线", "酸辣粉", "土豆粉", "螺狮粉", "凉皮儿", "麻辣烫",
                  "肉夹馍", "羊肉汤", "炒饭", "盖浇饭", "卤肉饭", "烤肉饭", "黄焖鸡米饭", "驴肉火烧", "川菜", "麻辣香锅", "火锅", "酸菜鱼", "烤串", "披萨", "烤鸭",
                  "汉堡", "炸鸡", "寿司", "蟹黄包", "煎饼果子", "生煎", "炒年糕"]
            ))
        ttkConfig.getConfig('setting').set('what_we_eat', c)
        await ttkConfig.save()
    '''


async def shutTheFuckUp(app: Slave, message: GroupMessage):
    rands = [random.randint(0, 999) for _ in range(0, 4)]
    if rands[0] < 20:
        plain: Plain = message.messageChain.get(Plain)
        if plain:
            await app.sendGroupMessage(message.sender.group.id, MeCh.create(plain))
    if rands[1] < 20:
        await app.sendGroupMessage(message.sender.group.id, MeCh.create([Plain('确实')]))
    if rands[2] < 12:
        if random.randint(1, 3) < 2:
            msg = MeCh.create([At(message.sender.id), Plain('我爱你')])
            await app.sendGroupMessage(message.sender.group.id, msg)
        else:
            Tick[message.sender.group.id] = 2
    if rands[3] < 12:
        await sendPhilosophy(app, message)


async def fencing(app: Slave, message: GroupMessage):
    if message.sender.group.id in Tick.keys():
        Tick[message.sender.group.id] -= 1
    else:
        Tick[message.sender.group.id] = 0
    if message.messageChain.has(Quote) or message.messageChain.has(At):
        quote: Quote = message.messageChain.get(Quote)[0] if message.messageChain.has(Quote) else ''
        at: At = message.messageChain.get(At)[0] if message.messageChain.has(At) else ''
        qq = app.connect_info.account
        if (quote and quote.senderId == qq) or (at and at.target == qq):
            if message.messageChain.has(Plain):
                plains: [Plain] = message.messageChain.get(Plain)
                if any(plain.text.strip() in BlockedKeywords for plain in plains):
                    return
                if text := getFirstTrimText(plains):
                    sent = await trySentiment(text)
                    if sent[0] == 0:
                        url = nm_api if sent[1] > 0.5 else nm_api
                    elif sent[0] == 2:
                        url = chp_api
                    else:
                        return
                    love = await requestText(url)
                    msg = [At(message.sender.id), Plain(love[0])]
                    await app.sendGroupMessage(message.sender.group, MeCh.create(msg))
                else:
                    return
        if quote:
            plains: [Plain] = message.messageChain.get(Plain)
            if any('翻译翻译' in plain.text.strip() for plain in plains):
                if text := getFirstTrimText(quote.origin.get(Plain)):
                    items: dict = (await requestText(fy_api, 'POST', data={'text': text}, raw=False))[0]
                    msg = [Plain('能不能好好说话')]
                    for item in items:
                        if 'trans' not in item.keys():
                            continue
                        msg.append(Plain(f"\n{item['name']}->{json.dumps(item['trans'], ensure_ascii=False)}"))
                    await app.sendGroupMessage(message.sender.group, MeCh.create(msg))

    if Tick[message.sender.group.id] > 0:
        if message.messageChain.has(Plain):
            plain: Plain = message.messageChain.get(Plain)[0]
            sent = await trySentiment(plain.text)
            if sent[0] == 0:
                url = nm_api if sent[1] > 0.7 else nm_api
            else:
                return
            love = await requestText(url)
            msg = [At(message.sender.id), Plain(love[0])]
            await app.sendGroupMessage(message.sender.group, MeCh.create(msg))


async def trySentiment(words: str) -> list:
    access_token = ttkConfig.getConfig('setting').get('bd_sentiment_access_token')
    try:
        return await sentiment(words, access_token)
    except KeyError:
        api_key = ttkConfig.getConfig('setting').get('bd_sentiment_API_key')
        secret_key = ttkConfig.getConfig('setting').get('bd_sentiment_secret_key')
        new_token = await refreshSentimentToken(api_key, secret_key)
        ttkConfig.getConfig('setting').set('bd_sentiment_access_token', new_token)
        await ttkConfig.save('setting')
        logger.debug('bd sentiment token saved')
        return await sentiment(words, new_token)


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


def getFirstTrimText(plains: [Plain]) -> str:
    text = ''
    for plain in plains:
        if plain.text.strip():
            text = plain.text.strip()
            break
    return text
