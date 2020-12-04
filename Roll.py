import asyncio

from graia.application.exceptions import AccountMuted
from graia.broadcast import Broadcast
from graia.application.interrupt import InterruptControl
from graia.application import GraiaMiraiApplication as Slave, Session, GroupMessage

from application.YummyPicture.Entrance import YummyPicture
from application.TalkToMe.TalkToMe import TalkToMe
from application.URaNai.URaNai import URaNai
from application.Economy.EconomyCommand import Economy
from application.Capitalism.Capitalism import Capitalism
from Logger import logger

loop = asyncio.get_event_loop()

bcc = Broadcast(loop=loop)
app = Slave(
    broadcast=bcc,
    connect_info=Session(host="http://localhost:7737", authKey="", account=111111111, websocket=True)
)
inc = InterruptControl(bcc)


@bcc.receiver("GroupMessage")
async def group_message_handler(message: GroupMessage):
    commands: [str] = message.messageChain.asDisplay().split(' ')
    commands[0] = commands[0].upper()
    try:
        await YummyPicture(app, message, commands)
        await TalkToMe(app, message, commands)
        await URaNai(app, message, commands)
        await Economy(app, message, commands)
        await Capitalism(app, message, commands)
    except AccountMuted:
        logger.info(f'我被狗禁言了！！！')


app.launch_blocking()
