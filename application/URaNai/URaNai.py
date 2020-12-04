import io
import os
import random
from datetime import datetime
from PIL import Image as PImage, ImageDraw, ImageFont
from graia.application.message.elements.internal import At, Image, Plain
from graia.application.message.chain import MessageChain as MeCh
from graia.application import GraiaMiraiApplication as Slave, GroupMessage

from .URaNaiDesc import URaNaiDesc
from .URaNaiType import URaNaiType
from application.URaNai import logger, urnConfig
from utils.trim import PATH_IMAGE, PATH_RES, PATH_FONT

random.seed(datetime.now().strftime('%Y%m%d'))
PACK = 'princess/' if random.randint(0, 1) else 'kiZuNaAi/'
random.seed(None)
PATH_URN = PATH_RES + PATH_IMAGE + 'URaNai/'
APP_COMMANDS = ['运势', '转运']
try:
    from application.Economy import Economy

    Economy = Economy
    price = 5
except ImportError:
    Economy = None


async def URaNai(app: Slave, message: GroupMessage, commands: list):
    if commands[0] in APP_COMMANDS:
        await URaNaiCommand(app, message, commands)


async def URaNaiCommand(app: Slave, message: GroupMessage, commands: list):
    async def sendURaNai(force=False):
        files = os.listdir(PATH_URN + PACK)
        random.seed(seed)
        randint = random.randint(1, len(files))
        if PACK == 'princess/':
            bio = io.BytesIO()
            drawing_pic(randint).save(bio, format='JPEG')
            img: Image = Image.fromUnsafeBytes(bio.getvalue())
        else:
            img: Image = Image.fromLocalFile(PATH_URN + PACK + f'URaNai{randint}.jpg')
        msg = [At(message.sender.id), img]
        if force:
            msg.append(Plain(f'已花费5只{Economy.unit}'))
        await app.sendGroupMessage(message.sender.group.id, MeCh.create(msg))
        random.seed(None)

    cmd = commands[0]
    '''
    if cmd == 'TEST':
        print(11)
        imgs = []
        for x in range(1, 67):
            for t in URaNaiDesc:
                if str(x) in t['chara_id']:
                    for a, b in enumerate(t['type']):
                        img = drawing_pic(x, a)
                        imgs.append(img)
        save_name = 'aa.gif'
        imgs[0].save(save_name, save_all=True, append_images=imgs, duration=0.2)
        print(22)
    '''

    if cmd == '运势':
        seed = await generateSeed(message.sender.id)
        await sendURaNai()
    if cmd == '转运':
        if Economy:
            if await Economy.Economy.pay(message.sender.id, Economy.capitalist, 5):
                seed = await generateSeed(message.sender.id, True)
                await sendURaNai(True)
            else:
                info: dict = await Economy.Economy.money(message.sender.id)
                plain: Plain = Plain(f"你的{Economy.unit}不足,你还剩{info['balance']}只{Economy.unit}")
                await app.sendGroupMessage(message.sender.group.id, MeCh.create([plain]))


def drawing_pic(chara_id, type_id=None) -> PImage:
    chara_id = str(chara_id)
    path_font = {
        'title': f'{PATH_RES + PATH_FONT}MameLon.otf',
        'text': f'{PATH_RES + PATH_FONT}SaKuRa.ttf'
    }
    img = PImage.open(PATH_URN + PACK + f'frame_{chara_id}.jpg')
    # Draw title
    draw = ImageDraw.Draw(img)
    text, title = get_info(chara_id, type_id)
    text = text['content']
    font_size = 45
    color = '#F5F5F5'
    image_font_center = (140, 99)
    font = ImageFont.truetype(path_font['title'], font_size)
    font_length = font.getsize(title)
    xy = (image_font_center[0] - font_length[0] / 2, image_font_center[1] - font_length[1] / 2)
    draw.text(xy, title, fill=color, font=font)
    # Text rendering
    font_size = 25
    color = '#323232'
    image_font_center = [140, 297]
    font = ImageFont.truetype(path_font['text'], font_size)
    result = decrement(text)
    if not result[0]:
        return Exception('Unknown error in daily luck')
    for i in range(0, result[0]):
        font_height = len(result[i + 1]) * (font_size + 4)
        vertical_text = vertical(result[i + 1])
        x = int(image_font_center[0] + (result[0] - 2) * font_size / 2 + (result[0] - 1) * 4 - i * (font_size + 4))
        y = int(image_font_center[1] - font_height / 2)
        draw.text((x, y), vertical_text, fill=color, font=font)
    return img


def get_info(cid: str, type_id: int = None) -> str:
    for i in URaNaiDesc:
        if cid in i['chara_id']:
            type_words = i['type']
            if type_id is None:
                desc = random.choice(type_words)
            else:
                desc = type_words[type_id]
            return desc, get_luck_type(desc)
    raise Exception('luck description not found')


def get_luck_type(desc):
    target_luck_type = desc['good-luck']
    for i in URaNaiType:
        if i['good-luck'] == target_luck_type:
            return i['name']
    raise Exception('luck type not found')


def decrement(text):
    length = len(text)
    result = []
    cardinality = 9
    if length > 4 * cardinality:
        return [False]
    cols = (length - 1) // cardinality + 1
    result.append(cols)
    # Optimize for two columns
    space = ' '
    length = len(text)
    if cols == 2:
        if length % 2 == 0:
            # even
            fill = space * int(9 - length / 2)
            return [cols, text[:int(length / 2)] + fill, fill + text[int(length / 2):]]
        else:
            # odd number
            fill = space * int(9 - (length + 1) / 2)
            return [cols, text[:int((length + 1) / 2)] + fill,
                    fill + space + text[int((length + 1) / 2):]]
    for i in range(0, cols):
        if i == cols - 1 or cols == 1:
            result.append(text[i * cardinality:])
        else:
            result.append(text[i * cardinality:(i + 1) * cardinality])
    return result


def vertical(text: str):
    result = []
    for s in text:
        result.append(s)
    return '\n'.join(result)


async def generateSeed(qq: int, new=False):
    ymd = str(datetime.now().strftime('%Y%m%d'))
    if user := urnConfig.getConfig('config').get(str(qq)):
        user_seed: str = user['seed']
        if user_seed.split('-')[0] != ymd or new:  # next day
            seed = f"{ymd}-{str(qq)}-{datetime.now()}"
            user['seed'] = seed
            await urnConfig.save('config')
            logger.debug(f'new seed for {qq}')
        else:
            seed = user_seed
    else:
        seed = f"{ymd}-{str(qq)}-{datetime.now()}"
        urnConfig.getConfig('config').set(str(qq), {'seed': seed})
        await urnConfig.save('config')
    return seed
