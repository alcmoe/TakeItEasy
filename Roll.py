import asyncio

from graia.broadcast import Broadcast
from graia.application import Session, GraiaMiraiApplication as Slave

from application.YummyPicture.PictureRipperListener import PictureRipperListener
from application.TalkToMe.TalkToMeListener import TalkToMeListener
from application.URaNai.URaNaiListener import URaNaiListener
from application.Economy.EconomyListener import EconomyListener
from application.Capitalism.CapitalismListener import CapitalismListener
from application.VideoRipper.VideoRipper import VideoRipperListener

loop = asyncio.get_event_loop()

bcc = Broadcast(loop=loop)
app = Slave(
    broadcast=bcc,
    connect_info=Session(host="http://localhost:7737", authKey="xxxx", account=123456, websocket=True)
)
TalkToMeListener(bcc).run()
URaNaiListener(bcc).run()
CapitalismListener(bcc).run()
EconomyListener(bcc).run()
VideoRipperListener(bcc).run()
PictureRipperListener(bcc).run()
app.launch_blocking()
