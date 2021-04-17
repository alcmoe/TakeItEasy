from bs4 import BeautifulSoup

from graia.application import GraiaMiraiApplication as Slave, GroupMessage
from graia.application.message.chain import MessageChain as MeCh, MessageChain
from graia.application.message.elements.internal import Plain
from graia.broadcast import ExecutionStop, Broadcast
from graia.broadcast.builtin.decoraters import Depend

from . import logger
from utils.network import request
from Listener import Listener


class CSGOListener(Listener):
    bcc: Broadcast
    command: dict = dict()
    neKo_url = 'https://rank.nicotine.vip//?page=profiles&search=3&profile='
    try:
        from application.Economy import Economy

        Economy = Economy
        price = 5
    except ImportError:
        Economy = None

    APP_COMMANDS = ['.NE']
    capitalist = 0

    def run(self):
        @self.bcc.receiver(GroupMessage, headless_decoraters=[Depend(self.cmdFilter)])
        async def groupCmdHandler(app: Slave, message: GroupMessage):
            await self.commandHandler(app, message)

    def cmdFilter(self, message: MessageChain):
        if cmd := message.asDisplay().split(' '):
            args = cmd[1:]
            cmd = cmd[0].upper()
            if not any(app_cmd in cmd for app_cmd in self.APP_COMMANDS):
                raise ExecutionStop()
            CSGOListener.command.update(cmd=cmd, args=args)
        else:
            raise ExecutionStop()

    async def commandHandler(self, app: Slave, message: GroupMessage):
        cmd: str = CSGOListener.command.get('cmd')
        if cmd == self.APP_COMMANDS[0]:
            args = CSGOListener.command.get('args')
            msg: list = await self.ripNeKoInfo(args[0])
            msg = '\n'.join(msg)
            await app.sendGroupMessage(message.sender.group, MeCh.create([Plain(msg)]))

    async def ripNeKoInfo(self, steam_id: str):
        url = self.neKo_url + steam_id
        raw_data = await request('GET', url)
        soup = BeautifulSoup(raw_data, "lxml")
        left = soup.find_all('div', class_='left-stats-block')
        right = soup.find_all('div', class_='right-stats-block')
        msg = []
        for idx in range(1, 12, 2):
            name = left[0].contents[1].contents[idx].string
            value = right[0].contents[1].contents[idx].string
            msg.append(name + ' ' + value)
        return msg

