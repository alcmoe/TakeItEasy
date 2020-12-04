import re as reg
import importlib
from typing import List

from graia.application import GraiaMiraiApplication as Slave, GroupMessage, enter_message_send_context, UploadMethods
from graia.application.message.chain import MessageChain as MeCh
from graia.application.group import Group
from graia.application.message.elements.internal import At, Plain, Image, Quote, Source
from graia.application.exceptions import UnknownTarget

from application.YummyPicture import logger, ymConfig
from utils.trim import *
from utils.network import *
from application.YummyPicture.Searcher import Searcher
from application.YummyPicture.JASearcher import JASearcher

ym = ymConfig.getConfig('setting').get('ripper')
pkg = importlib.import_module('application.YummyPicture.yummy.' + ym)
dataClass = getattr(pkg, f'{ym.capitalize()}Data')
ripperClass = getattr(pkg, f'{ym.capitalize()}Ripper')
databaseClass = getattr(pkg, f'{ym.capitalize()}Database')
db = databaseClass()
Tick = {}
ratings = {}
GCache = {}
APP_COMMANDS = ['.YM', '.AA', '.RA', '.GR', './N', './P', './S', './R', './D', './J']
try:
    from application.Economy import Economy
    from application.Economy.EconomyCommand import notEnough
    Economy = Economy
    price = 5
except ImportError:
    Economy = None
    notEnough = None


async def initYummyPicture():
    global ym, pkg, db, dataClass, databaseClass, ripperClass, ratings
    ymConfig.reload()
    ratings = {}
    ym = ymConfig.getConfig('setting').get('ripper')
    logger.debug('reload configs')
    pkg = importlib.import_module('application.YummyPicture.yummy.' + ym)
    dataClass = getattr(pkg, f'{ym.capitalize()}Data')
    ripperClass = getattr(pkg, f'{ym.capitalize()}Ripper')
    databaseClass = getattr(pkg, f'{ym.capitalize()}Database')
    db = databaseClass()


async def YummyPicture(app: Slave, message: GroupMessage, commands: list):
    match = ripeReg(message)
    if match:
        commands = match
    if commands[0] in APP_COMMANDS or commands[0][:3] in APP_COMMANDS:
        await MSGDeaHandler(app, message, commands)
        await RipperHandler(app, message, commands)  # TODO(Alcatraz) Will support friend chat later.
    await PicDeaHandler(app, message)


def Permitted(message: GroupMessage):
    return message.sender.id in ymConfig.getConfig('setting').get('admins')


def getRating(source, group, force=False):
    if group not in ratings.keys() or force:
        level = ymConfig.getConfig('setting').get('group_rate')[str(group)] if str(group) in ymConfig.getConfig(
            'setting').get('group_rate').keys() else ymConfig.getConfig('setting').get('rating')
        rs = {k: v for k, v in ymConfig.getConfig(source).get('rating').items() if v <= level}
        rating = sorted(rs.items(), key=lambda d: d[1], reverse=True)
        ratings[group] = rating[0][0]
        logger.info(f"rating {group} is {ratings[group]}")


async def RipperHandler(app: Slave, message: GroupMessage, commands: list):
    if './' in commands[0]:
        args = formatParm(commands)
        if not args:
            # await app.sendGroupMessage(message.sender.group, [At(message.sender.id), Plain('格式错误')])
            return
        if Economy:
            count: int = args['count']
            if not await Economy.Economy.pay(message.sender.id, Economy.capitalist, count * 5):
                await notEnough(app, message, 5)
                return
        ripper: ripperClass = ripperClass()
        gid = message.sender.group.id
        getRating(ym, gid)
        if args['key'] == 'n':
            ripper.new()
        if args['key'] == 'p':
            ripper.popular().period(args['period'])
        if args['key'] == 's':
            ripper.search().tags(args['tags'])
        if args['key'] == 'r':
            ripper.random().tags(args['tags'])
        if args['key'] == 'd':
            ripper.detail().specific([args['tags'], db])
        if args['key'] == 'j':
            ja: JASearcher = JASearcher()
            ja.useProxy().setID(args['id'])
            result: dict = await ja.get(args['offset'], args['limit'])
            msg = []
            for re in result:
                if 'image' in re.keys():
                    msg.append(Image.fromUnsafeBytes(re['image']))
                if 'text' in re.keys():
                    msg.append(Plain(re['text']))
            if not msg:
                await app.sendGroupMessage(message.sender.group, MeCh.create([Plain('未搜索到')]))
                return
            await app.sendGroupMessage(message.sender.group, MeCh.create(msg))
            return
        tasks: List[asyncio.Task] = []
        try:
            result = await ripper.offset(args['offset']).count(args['count']).rating(ratings[gid]).get()
        except ClientConnectorError:
            msg = [At(message.sender.id), Plain('不给发，爬')]
            await app.sendGroupMessage(message.sender.group, MeCh.create(msg))
            return
        number = len(result)
        if not number:
            msg = [At(message.sender.id), Plain('未搜索到')]
            await app.sendGroupMessage(message.sender.group, MeCh.create(msg))
            return
        for i, yande in enumerate(result):
            prefix = f'[{i + 1}/{number}]' if number > 1 else ''
            task = asyncio.create_task(send(app, [yande], message.sender.group, prefix))
            if hasattr(yande, 'id'):
                await db.addYummy(yande)
            tasks.append(task)
            await asyncio.wait([task], timeout=5)
        done, pending = await asyncio.wait(tasks, timeout=120)
        exceptions = [task.exception() for task in done if task.exception()]
        timeouts = [t.cancel() for t in pending]
        es = len(exceptions)
        ts = len(timeouts)
        if es or ts:
            t_message = f'{ts}个任务超时' if ts else ''
            e_message = f'{es}个任务异常' if es else ''
            await app.sendGroupMessage(message.sender.group, MeCh.create([Plain(e_message + t_message)]))
            logger.warning(f'exceptions{exceptions} timeouts{timeouts}')


async def MSGDeaHandler(app: Slave, message: GroupMessage, commands):
    cmd = commands[0]
    if not Permitted(message):
        return
    msg = [At(message.sender.id)]
    try:
        if cmd == APP_COMMANDS[0]:  # ym
            ymConfig.getConfig(commands[1]).set(commands[2], commands[3])
            await ymConfig.save(commands[1])
            await initYummyPicture()
            msg.append(Plain('Success'))
        if cmd == APP_COMMANDS[1]:  # aa
            if commands[1].isnumeric():
                ymConfig.getConfig('setting').addList('admins', int(commands[1]))
                await ymConfig.save('setting')
                msg.append(Plain('Added'))
            else:
                msg.append(Plain('Wrong param'))
        if cmd == APP_COMMANDS[2]:  # ra
            if commands[1].isnumeric():
                ymConfig.getConfig('setting').rmList('admins', int(commands[1]))
                await ymConfig.save('setting')
                msg.append(Plain('Removed'))
            else:
                msg.append(Plain('Wrong param'))
        if cmd == APP_COMMANDS[3]:  # gr
            if commands[1].isnumeric() and commands[2].isnumeric():
                ymConfig.getConfig('setting').addDict('group_rate', str(commands[1]), int(commands[2]))
                getRating(ym, message.sender.group.id, True)
                await ymConfig.save('setting')
                msg.append(Plain('Success'))
    except IndexError:
        msg.append(Plain('Wrong param'))
    if len(msg) > 1:
        await app.sendGroupMessage(message.sender.group, MeCh.create(msg))


async def reCallYms(app, mid, t):
    await asyncio.sleep(t)
    await app.revokeMessage(mid)


async def PicDeaHandler(app: Slave, message: GroupMessage):
    if Economy:
        add = 0
        if images := message.messageChain.get(Image):
            for image in images:
                by: bytes = await request(url=image.url)
                add += 1 if len(by) > 100000 else 0
        else:
            add += 1 if random.randint(0, 10) < 2 else 0
        if add:
            for _ in range(0, add):
                await Economy.Economy.addMoney(message.sender.id, 5)
                await Economy.Economy.addValue(5)
        await Economy.Economy.trySave()
    if message.messageChain.has(Quote) and message.messageChain.has(Plain):
        texts: [Plain] = message.messageChain.get(Plain)
        quote: Quote = message.messageChain.get(Quote)[0]
        if any(text.__dict__['text'].strip() == '好' for text in texts):
            if not Permitted(message):
                # await app.sendGroupMessage(message.sender.group, [At(message.sender.id), Plain('权限不足')])
                pass
            else:
                plain: Plain = quote.origin.get(Plain)[0]
                if plain.text == '[图片]':  # quoto 获取不到图片;从http插件重新获取,等mirai
                    if (message.sender.group.id << 32) + quote.id in GCache.keys():
                        cache = GCache[(message.sender.group.id << 32) + quote.id]
                        image: Image = cache[0]
                        ext = cache[1]
                    else:
                        try:
                            quote_source: GroupMessage = await app.messageFromId(quote.id)
                            image: Image = quote_source.messageChain.get(Image)[0]
                            ext = 'jpg'
                        except UnknownTarget:
                            mec = MeCh.create([At(message.sender.id), Plain('不在本地与消息缓存中,无法保存')])
                            await app.sendGroupMessage(message.sender.group, mec)
                            return
                    te = await saveUrlPicture(image.url, image.imageId,
                                              f'application/YummyPicture/yummy/{ym}/data/save', ext)
                    msg = [At(message.sender.id), Plain(te)]
                    await app.sendGroupMessage(message.sender.group, MeCh.create(msg))
        elif any(text.__dict__['text'].strip() == '图源' for text in texts):
            plain: Plain = quote.origin.get(Plain)[0]
            if plain and plain.text in ['[图片]', '[动画表情]']:
                try:
                    if (k := (message.sender.group.id << 32) + quote.id) in GCache.keys():
                        url = GCache[k][0].url
                    else:
                        quote_source: GroupMessage = await app.messageFromId(quote.id)
                        image: Image = quote_source.messageChain.get(Image)[0]
                        url = image.url
                    searcher: Searcher = Searcher()
                    result = await searcher.useApiKey().setUrl(url).get()
                    msg = []
                    connector: ProxyConnector = ProxyConnector()
                    if proxy := ymConfig.getConfig('setting').get('proxy'):
                        connector = ProxyConnector.from_url(proxy)
                    for one in result:
                        if float(sim := one['header']['similarity']) < 50:
                            continue
                        img_byte = await request(url=one['header']['thumbnail'], connector=connector, close=False)
                        img = Image.fromUnsafeBytes(img_byte)
                        msg.append(img)
                        if 'ext_urls' in one['data']:
                            ext = one['data']['ext_urls']
                        else:
                            ext = one['header']['thumbnail']
                        msg.append(Plain(f"相似度{sim}%,链接{ext}"))
                    if connector:
                        await connector.close()
                    if len(msg) == 0:
                        msg.append(Plain('未搜索到'))
                    await app.sendGroupMessage(message.sender.group, MeCh.create(msg))
                except ClientConnectorError:
                    msg = [At(message.sender.id), Plain('爬，老子不开心了')]
                    await app.sendGroupMessage(message.sender.group, MeCh.create(msg))
                except UnknownTarget:
                    msg = [At(message.sender.id), Plain('不在本地与消息缓存中,无法搜索,请重发图片')]
                    await app.sendGroupMessage(message.sender.group, MeCh.create(msg))
        elif any(text.__dict__['text'].strip().lower() == 'x2' for text in texts):
            if not Permitted(message):
                # await app.sendGroupMessage(message.sender.group, [At(message.sender.id), Plain('权限不足')])
                # return
                pass
            plains = quote.origin.asDisplay()
            if plains in ['[图片]', '[动画表情]']:
                connector: ProxyConnector = None
                if proxy := ymConfig.getConfig('setting').get('proxy'):
                    connector = ProxyConnector.from_url(proxy)
                if (message.sender.group.id << 32) + quote.id in GCache.keys():  # bot的图片python sdk不支持customMessage
                    cache = GCache[(message.sender.group.id << 32) + quote.id]
                    url = cache[0]
                else:
                    quote_source: GroupMessage = await app.messageFromId(quote.id)
                    image: Image = quote_source.messageChain.get(Image)[0]
                    url = image.url
                try:
                    data = await w2x(url, connector)
                    img = Image.fromUnsafeBytes(data[0])
                    with enter_message_send_context(UploadMethods.Group):
                        msg_chain = await MeCh.create([img]).build()
                    image: Image = msg_chain.__root__[0]
                    m = await app.sendGroupMessage(message.sender.group, msg_chain)
                    GCache[(message.sender.group.id << 32) + m.messageId] = [image, data[2], -1]
                except UnknownTarget:
                    msg = [At(message.sender.id), Plain('不在本地与消息缓存中,无法放大')]
                    await app.sendGroupMessage(message.sender.group, MeCh.create(msg))
                if connector:
                    await connector.close()
        elif any(text.__dict__['text'].strip().lower() == '我不喜欢' for text in texts):
            if not Permitted(message):
                msg = [At(message.sender.id), Plain('没叫你喜欢，滚')]
                await app.sendGroupMessage(message.sender.group, MeCh.create(msg))
                return
            else:
                qid: int = quote.id
                sender: int = quote.senderId
                qq = app.connect_info.account
                if sender != qq and message.sender.permission == "MEMBER":
                    msg = [At(message.sender.id), Plain('你不喜欢也没办法')]
                    await app.sendGroupMessage(message.sender.group, MeCh.create(msg))
                else:
                    await app.sendGroupMessage(message.sender.group, MeCh.create([Plain('行')]))
                    await reCallYms(app, qid, 1)
                    if message.sender.permission == "OWNER" or (  # b b m
                            message.sender.permission != "MEMBER" and message.sender.permission == "MEMBER"):
                        await reCallYms(app, message.messageChain.get(Source), 1)


async def send(app: Slave, yummy: [], group: Group, prefix: str):
    try:
        yande = yummy[0]
        img_byte: bytes = await yande.get()
        msg = [Image.fromUnsafeBytes(img_byte)]
        if ym == "ehentai" and hasattr(yande, 'gid'):
            msg.append(Plain(f'{yande.gid}/{yande.token}'))
        with enter_message_send_context(UploadMethods.Group):
            msg_chain = await MeCh.create(msg).build()
        image: Image = msg_chain.__root__[0]
        bot_message = await app.sendGroupMessage(group, msg_chain)  # At(sender.id), Plain(prefix_ + data_.purl),
        if len(GCache) >= 150:
            GCache.pop(list(GCache.keys())[0])
            logger.info('Cache is full,pop first one')
        ext = yande.url.split('.')[-1]
        GCache[(group.id << 32) + bot_message.messageId] = [image, ext, yande.id]
        logger.info(f"{prefix}sent，tags：{yande.tags}")
        await reCallYms(app, bot_message.messageId, 100)
    except asyncio.TimeoutError as e:
        logger.exception("[YummyPictures]: " + 'Timeout' + str(e))
        raise e
    except ValueError as e:
        logger.exception("[YummyPictures]: " + 'Size check failed' + str(e))
        raise e


def ripeReg(message: GroupMessage) -> list:
    if match := reg.match(r'(?:.*?([\d一二两三四五六七八九十]*)张|来点)?(.{0,10}?)的?色图$', message.messageChain.asDisplay()):
        if number := formatToNumber(match[1]) > 10:
            number = 1
        keyword = match[2]
        return [f'./R{number}'] + keyword.split(' ')
    else:
        return False
