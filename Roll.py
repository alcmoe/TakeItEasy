import asyncio
import json

from graia.broadcast import Broadcast
from graia.application import Session, GraiaMiraiApplication as Slave

from application.KeepHowling.Everyday import Everyday
from application.URaNai.URaNaiListener import URaNaiListener
from application.Economy.EconomyListener import EconomyListener
from application.TalkToMe.TalkToMeListener import TalkToMeListener
from application.VideoRipper.VideoRipper import VideoRipperListener
from application.Capitalism.CapitalismListener import CapitalismListener
from application.YummyPicture.PictureRipperListener import PictureRipperListener

# from application.PrincessConnect.PrincessConnectListener import PrincessConnectListener

loop = asyncio.get_event_loop()

bcc = Broadcast(loop=loop)
app = Slave(
    broadcast=bcc,
    connect_info=Session(host="http://localhost:7737", authKey="xxxxx", account=123456, websocket=True)
)
Everyday(app).run()
TalkToMeListener(bcc).run()
URaNaiListener(bcc).run()
CapitalismListener(bcc).run()
EconomyListener(bcc).run()
VideoRipperListener(bcc).run()
PictureRipperListener(bcc).run()
# PrincessConnectListener(bcc).run()

app.launch_blocking()