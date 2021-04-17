import random
import time

from graia.application import GraiaMiraiApplication as Slave, GroupMessage
from graia.application.message.elements.internal import Plain, At
from graia.application.message.chain import MessageChain as MeCh
from graia.broadcast.builtin.decoraters import Depend

from Listener import Listener
from application.Economy import Economy
from .HorseRacing import HorseRacing, Horse
from . import logger, clConfig
from .lang import lang as lg
from .Ico import IcoApi


class CapitalismListener(Listener):
    HORSE_RACING = {int: HorseRacing}
    APP_COMMANDS = ['赛马', '.SK', '.SKI', '.加攻', '.加血', '.加甲', '.加敏捷', '.加幸运', '签到', '打劫', 'ICO']
    HORSE_ADD_PERK = ['.加攻', '.加血', '.加甲', '.加敏捷', '.加幸运']
    HR = 'horse_racing'
    CL = 'economy'
    users: dict = clConfig.getConfig('config').getAll()
    command: dict = dict()

    def run(self):
        @self.bcc.receiver(GroupMessage, headless_decoraters=[Depend(self.cmdFilter)])
        async def groupCmdHandler(app: Slave, message: GroupMessage):
            await self.commandHandler(app, message)

    async def commandHandler(self, app: Slave, message: GroupMessage):
        # print(await IcoApi.getPrice('bitcoin'))
        commands: [str] = message.messageChain.asDisplay().split(' ')
        cmd = commands[0].upper()
        racing: HorseRacing
        lang_key = []
        msg = []
        type_: str = self.HR
        if cmd == '赛马':
            if racing := self.HORSE_RACING.get(message.sender.group.id):
                if racing.status == 2:
                    del self.HORSE_RACING[message.sender.group.id]
                    msg = await self.initRace(app, message)
                elif racing.status == 1:
                    lang_key = ['error_match_processing_please_wait']
                else:
                    lang_key = ['command_stake_tip']
            else:
                msg = await self.initRace(app, message)
        if cmd == '.SK':
            if racing := self.HORSE_RACING.get(message.sender.group.id):
                if racing.status == 0:
                    try:
                        if commands[1].isnumeric() and commands[2].isnumeric():
                            if (re := await racing.stake(message.sender.id, commands[1], int(commands[2])))[0]:
                                horse: Horse = racing.horses[commands[1]]
                                lang_key = ['stake_success', [horse.number, horse.nick, commands[2], Economy.unit]]
                            else:
                                msg_dict: dict = {
                                    1: '余额不足',
                                    2: '你已经吓下注过',
                                    3: f'[{commands[1]}号]马不存在',
                                }
                                msg = [Plain(msg_dict[re[1]])]
                        else:
                            lang_key = ['command_stake_tip']
                    except IndexError:
                        lang_key = ['command_stake_tip']
                else:
                    lang_key = ['error_not_prepare_stage']
            else:
                lang_key = ['error_not_prepare_stage']
        if cmd == '.SKI':
            if racing := self.HORSE_RACING.get(message.sender.group.id):
                msg = [Plain(await racing.displayGamblers())]
            else:
                lang_key = ['error_no_match']
        if cmd in self.HORSE_ADD_PERK:
            if racing := self.HORSE_RACING.get(message.sender.group.id):
                if racing.status == 1:
                    if len(commands) > 1:
                        target: str = commands[1]
                    else:
                        target: str = None
                    ty: int = self.HORSE_ADD_PERK.index(cmd) + 1
                    if (re := racing.addPerk(message.sender.id, target, ty))[0]:
                        lang_key = ['add_perk_success', [re[1][0], re[1][1], cmd[1:], re[1][2]]]
                    else:
                        msg_dict: dict = {
                            1: '传统赛马要讲武德',
                            2: '不在比赛阶段',
                            3: '这回合已经操作过',
                            4: f'你没有马' if not target else f'没有{commands[1]}号马',
                        }
                        msg = [Plain(msg_dict[re[1]])]
            if not lang_key:
                lang_key = ['add_my_ass']
        if cmd == '签到':
            type_ = self.CL
            if not (user := self.users.get(str(message.sender.id))):
                user: dict = self.insertUser(message.sender.id)
            diff: int = time.time() // (24 * 60 * 60) - user.get('last_sign') // (24 * 60 * 60)
            if diff:
                user['keep_days'] += 1 if diff == 1 else -user['keep_days'] + 1
                user['last_sign'] = time.time()
                keep: int = user['keep_days']
                await clConfig.save('config')
                rate: int = random.randint(0, 100 + keep)
                multi: int = 1
                if rate < keep:
                    multi = 2
                max_: int = random.randint(0, keep if keep <= 50 else 50)
                price: int = multi * (50 + max_ * 10)
                await Economy.Economy.addMoney(message.sender.id, price)
                await Economy.Economy.addValue(5)
                await Economy.Economy.saveMoney()
                lang_key = ['sign_success', [keep, price, Economy.unit, multi, 50, max_, 10, keep, keep + 100]]
            else:
                lang_key = ['signed_today']
        if cmd == '打劫':
            type_ = self.CL
            target: int = None
            if ats := message.messageChain.get(At):
                at: At = ats[0]
                target = at.target
            elif len(commands) > 1 and commands[1].isnumeric():
                target = int(commands[1])
            if target:
                if await Economy.Economy.has(str(target), create=False):
                    count = 10
                    if len(commands) > 2:
                        count = int(commands[2]) if commands[2].isnumeric() else count
                    count = 10 if count < 10 else count
                    if await Economy.Economy.pay(message.sender.id, Economy.capitalist, count):
                        if await Economy.Economy.pay(target, Economy.capitalist, count):
                            rd: int = random.randint(0, count + 10)
                            if rd < 10:
                                tax: int = int(count * .1)
                                await Economy.Economy.pay(Economy.capitalist, message.sender.id, 2 * count - tax)
                                lang_key = ['success_rob', [count - tax, Economy.unit, 10, count + 10]]
                            else:
                                await Economy.Economy.pay(Economy.capitalist, target, count + count // 4)
                                await Economy.Economy.pay(Economy.capitalist, message.sender.id, count // 2)
                                lang_key = ['fail_rob', [Economy.unit, count // 2, 10, count + 10]]
                        else:
                            await Economy.Economy.pay(Economy.capitalist, message.sender.id, count)
                            lang_key = ['target_not_enough_money', [Economy.unit, count]]
                    else:
                        lang_key = ['you_not_enough_money', [Economy.unit, count]]
                else:
                    lang_key = ['no_rob_target']
            else:
                lang_key = ['wrong_args']
        if not msg:
            text = await self.lang(type_, lang_key[0])
            if len(lang_key) > 1:
                text = text.format(*lang_key[1])
            msg = [Plain(text)]
        await app.sendGroupMessage(message.sender.group.id, MeCh.create(msg))

    async def startRacing(self, app: Slave, group: int, racing: HorseRacing):
        if await racing.start(racing.ready_time):
            field = await racing.display()
            await app.sendGroupMessage(group, MeCh.create([Plain('赛马开始\n' + field)]))
            await self.startTicking(app, group, racing)
        else:
            await app.sendGroupMessage(group, MeCh.create([Plain('人数不足，赛马结束,押注已退回')]))

    async def startTicking(self, app: Slave, group: int, racing: HorseRacing):
        if not (field := await racing.tick()):
            field: str = await racing.display()
            await app.sendGroupMessage(group, MeCh.create([Plain(field)]))
            await self.startTicking(app, group, racing)
        else:
            await app.sendGroupMessage(group, MeCh.create([Plain(field)]))
            msg = []
            for gambler in racing.winners:
                msg.append(At(gambler[0]))
                msg.append(Plain(f'赢得{gambler[1]}\n'))
            msg.append(Plain(f'庄家抽成{racing.own}只{Economy.unit} + 税{racing.tax}只{Economy.unit}'))
            await app.sendGroupMessage(group, MeCh.create(msg))

    async def initRace(self, app: Slave, message: GroupMessage):
        race = HorseRacing()
        rand = str(random.randint(1, race.horses_count))
        await race.stake(Economy.capitalist, rand, 5)
        logger.debug(f'bot staked {rand}')
        self.HORSE_RACING[message.sender.group.id] = race
        field: str = await race.display()
        app.broadcast.loop.create_task(self.startRacing(app, message.sender.group.id, race))
        return [Plain(field + f'\n\n已开启赛马输入[.sk num wager]进行押注,{race.ready_time}秒后开始')]

    @staticmethod
    async def lang(app: str, key: str) -> str:
        try:
            return lg[app][key]
        except KeyError:
            return ''

    @staticmethod
    def insertUser(user: int) -> dict:
        CapitalismListener.users[str(user)] = {
            "last_sign": 0.0,
            "keep_days": 0
        }
        return CapitalismListener.users.get(str(user))
