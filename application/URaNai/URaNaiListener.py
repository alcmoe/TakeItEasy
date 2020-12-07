import io
import os
import random
from datetime import datetime
from PIL import Image as PImage, ImageDraw, ImageFont
from graia.application.message.elements.internal import At, Image, Plain
from graia.application.message.chain import MessageChain as MeCh
from graia.application import GraiaMiraiApplication as Slave, GroupMessage
from graia.broadcast.builtin.decoraters import Depend

from Listener import Listener
from .URaNaiDesc import URaNaiDesc
from .URaNaiType import URaNaiType
from application.URaNai import logger, urnConfig
from utils.trim import PATH_IMAGE, PATH_RES, PATH_FONT


class URaNaiListener(Listener):
    APP_COMMANDS = ['运势', '转运']
    PATH_URN = PATH_RES + PATH_IMAGE + 'URaNai/'

    try:
        from application.Economy import Economy

        Economy = Economy
        price = 5
    except ImportError:
        Economy = None

    def run(self):
        @self.bcc.receiver(GroupMessage, headless_decoraters=[Depend(self.cmdFilter)])
        async def groupCmdHandler(app: Slave, message: GroupMessage):
            await self.commandHandler(app, message)

    async def commandHandler(self, app: Slave, message: GroupMessage):
        cmd: str = message.messageChain.asDisplay().split(' ')[0]
        random.seed(datetime.now().strftime('%Y%m%d'))
        pack = 'princess/' if random.randint(0, 1) else 'kiZuNaAi/'
        random.seed(None)

        async def sendURaNai(force=False):
            files = os.listdir(self.PATH_URN + pack)
            random.seed(seed)
            randint = random.randint(1, len(files))
            if pack == 'princess/':
                bio = io.BytesIO()
                self.drawing_pic(randint, pack).save(bio, format='JPEG')
                img: Image = Image.fromUnsafeBytes(bio.getvalue())
            else:
                img: Image = Image.fromLocalFile(self.PATH_URN + pack + f'URaNai{randint}.jpg')
            msg = [At(message.sender.id), img]
            if force:
                msg.append(Plain(f'已花费5只{self.Economy.unit}'))
            await app.sendGroupMessage(message.sender.group.id, MeCh.create(msg))
            random.seed(None)

        if cmd == '运势':
            seed = await self.generateSeed(message.sender.id)
            await sendURaNai()
        if cmd == '转运':
            if self.Economy:
                if await self.Economy.Economy.pay(message.sender.id, self.Economy.capitalist, 5):
                    seed = await self.generateSeed(message.sender.id, True)
                    await sendURaNai(True)
                else:
                    info: dict = await self.Economy.Economy.money(message.sender.id)
                    plain: Plain = Plain(f"你的{self.Economy.unit}不足,你还剩{info['balance']}只{self.Economy.unit}")
                    await app.sendGroupMessage(message.sender.group.id, MeCh.create([plain]))

    def drawing_pic(self, chara_id: int, pack: str, type_id=None) -> PImage:
        chara_id = str(chara_id)
        path_font = {
            'title': f'{PATH_RES + PATH_FONT}MameLon.otf',
            'text': f'{PATH_RES + PATH_FONT}SaKuRa.ttf'
        }
        img = PImage.open(self.PATH_URN + pack + f'frame_{chara_id}.jpg')
        # Draw title
        draw = ImageDraw.Draw(img)
        text, title = self.get_info(chara_id, type_id)
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
        result = self.decrement(text)
        if not result[0]:
            return Exception('Unknown error in daily luck')
        for i in range(0, result[0]):
            font_height = len(result[i + 1]) * (font_size + 4)
            vertical_text = self.vertical(result[i + 1])
            x = int(image_font_center[0] + (result[0] - 2) * font_size / 2 + (result[0] - 1) * 4 - i * (font_size + 4))
            y = int(image_font_center[1] - font_height / 2)
            draw.text((x, y), vertical_text, fill=color, font=font)
        return img

    def get_info(self, cid: str, type_id: int = None) -> str:
        for i in URaNaiDesc:
            if cid in i['chara_id']:
                type_words = i['type']
                if type_id is None:
                    desc = random.choice(type_words)
                else:
                    desc = type_words[type_id]
                return desc, self.get_luck_type(desc)
        raise Exception('luck description not found')

    @staticmethod
    def get_luck_type(desc):
        target_luck_type = desc['good-luck']
        for i in URaNaiType:
            if i['good-luck'] == target_luck_type:
                return i['name']
        raise Exception('luck type not found')

    @staticmethod
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

    @staticmethod
    def vertical(text: str):
        result = []
        for s in text:
            result.append(s)
        return '\n'.join(result)

    @staticmethod
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
