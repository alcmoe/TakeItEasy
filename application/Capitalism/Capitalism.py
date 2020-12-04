import random

from graia.application import GraiaMiraiApplication as Slave, GroupMessage
from graia.application.message.elements.internal import Plain, At
from graia.application.message.chain import MessageChain as MeCh

from application.Economy import Economy
from .HorseRacing import HorseRacing, Horse
from . import logger
from .lang import lang as lg

HORSE_RACING = {int: HorseRacing}
APP_COMMANDS = ['赛马', '.SK', '.SKI']
HORSE_ADD_PERK = ['.加攻', '.加血', '.加甲', '.加敏捷', '.加幸运']
HR = 'horse_racing'


async def Capitalism(app: Slave, message: GroupMessage, commands: list):
    if commands[0] in APP_COMMANDS + HORSE_ADD_PERK:
        await HorseRacingHandler(app, message, commands)


async def HorseRacingHandler(app: Slave, message: GroupMessage, commands: [str]):
    cmd: str = commands[0]
    racing: HorseRacing
    lang_key = []
    msg = []
    if cmd == '赛马':
        if racing := HORSE_RACING.get(message.sender.group.id):
            if racing.status == 2:
                del HORSE_RACING[message.sender.group.id]
                msg = await initRace(app, message)
            elif racing.status == 1:
                lang_key = ['error_match_processing_please_wait']
            else:
                lang_key = ['command_stake_tip']
        else:
            msg = await initRace(app, message)
    if cmd == '.SK':
        if racing := HORSE_RACING.get(message.sender.group.id):
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
        if racing := HORSE_RACING.get(message.sender.group.id):
            msg = [Plain(await racing.displayGamblers())]
        else:
            lang_key = ['error_no_match']
    if cmd in HORSE_ADD_PERK:
        if racing := HORSE_RACING.get(message.sender.group.id):
            if racing.status == 1:
                if len(commands) > 1:
                    target: str = commands[1]
                else:
                    target: str = None
                ty: int = HORSE_ADD_PERK.index(cmd) + 1
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
    if not msg:
        text = await lang(HR, lang_key[0])
        if len(lang_key) > 1:
            text = text.format(*lang_key[1])
        msg = [Plain(text)]
    await app.sendGroupMessage(message.sender.group.id, MeCh.create(msg))


async def startRacing(app: Slave, group: int, racing: HorseRacing):
    if await racing.start(racing.ready_time):
        field = await racing.display()
        await app.sendGroupMessage(group, MeCh.create([Plain('赛马开始\n' + field)]))
        await startTicking(app, group, racing)
    else:
        await app.sendGroupMessage(group, MeCh.create([Plain('人数不足，赛马结束,押注已退回')]))


async def startTicking(app: Slave, group: int, racing: HorseRacing):
    if not (field := await racing.tick()):
        field: str = await racing.display()
        await app.sendGroupMessage(group, MeCh.create([Plain(field)]))
        await startTicking(app, group, racing)
    else:
        await app.sendGroupMessage(group, MeCh.create([Plain(field)]))
        msg = []
        for gambler in racing.winners:
            msg.append(At(gambler[0]))
            msg.append(Plain(f'赢得{gambler[1]}\n'))
        msg.append(Plain(f'庄家抽成{racing.own}只{Economy.unit} + 税{racing.tax}只{Economy.unit}'))
        await app.sendGroupMessage(group, MeCh.create(msg))


async def initRace(app: Slave, message: GroupMessage):
    race = HorseRacing()
    rand = str(random.randint(1, race.horses_count))
    await race.stake(Economy.capitalist, rand, 5)
    logger.debug(f'bot staked {rand}')
    HORSE_RACING[message.sender.group.id] = race
    field: str = await race.display()
    app.broadcast.loop.create_task(startRacing(app, message.sender.group.id, race))
    return [Plain(field + f'\n\n已开启赛马输入[.sk num wager]进行押注,{race.ready_time}秒后开始')]


async def lang(app: str, key: str) -> str:
    try:
        return lg[app][key]
    except KeyError:
        return ''
