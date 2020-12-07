import asyncio

from graia.broadcast import Broadcast
from graia.application.exceptions import AccountMuted
from graia.application import Session, GraiaMiraiApplication as Slave

from application.YummyPicture.PictureRipperListener import PictureRipperListener
from application.TalkToMe.TalkToMeListener import TalkToMeListener
from application.URaNai.URaNaiListener import URaNaiListener
from application.Economy.EconomyListener import EconomyListener
from application.Capitalism.CapitalismListener import CapitalismListener
from application.VideoRipper.VideoRipper import VideoRipperListener
from Logger import logger

loop = asyncio.get_event_loop()

bcc = Broadcast(loop=loop)
app = Slave(
    broadcast=bcc,
    connect_info=Session(host="http://localhost:7737", authKey="xxxx", account=1234, websocket=True)
)
try:
    TalkToMeListener(bcc).start()
    URaNaiListener(bcc).start()
    CapitalismListener(bcc).start()
    EconomyListener(bcc).start()
    VideoRipperListener(bcc).start()
    PictureRipperListener(bcc).start()
except AccountMuted:
    logger.info(f'我被狗禁言了！！！')

app.launch_blocking()
