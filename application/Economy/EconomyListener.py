import json

from graia.application import GraiaMiraiApplication as Slave, GroupMessage
from graia.application.message.chain import MessageChain as MeCh, MessageChain
from graia.application.message.elements.internal import At, Plain, Quote
from graia.broadcast import ExecutionStop
from graia.broadcast.builtin.decoraters import Depend

from Listener import Listener
from . import Economy as EconomyAPI


class EconomyListener(Listener):
    APP_COMMANDS = ['.MM', '.PM', '.TOP', '.PAY']
    command: dict = dict()

    def run(self):

        @self.bcc.receiver(GroupMessage, headless_decoraters=[Depend(self.cmdFilter)])
        async def groupCmdHandler(app: Slave, message: GroupMessage):
            await self.commandHandler(app, message)

    def cmdFilter(self, message: MessageChain):
        if cmd := message.asDisplay().split(' '):
            cmd = cmd[0].upper()
            if cmd not in self.APP_COMMANDS:
                raise ExecutionStop()
            self.command.update(cmd=cmd)
            if cmd != self.APP_COMMANDS[3]:
                return
            args = []
            if ats := message.get(At):
                at: At = ats[0]
                args.append(at.target)
            plain: Plain
            txs: list = ' '.join([plain.text.strip() for plain in message.get(Plain) if plain.text.strip()]).split(' ')
            le: int = 2 - len(args)
            args.extend(txs[1: 1 + le])
            if len(args) < 2:
                raise ExecutionStop()
            self.command.update(args=args)
        else:
            raise ExecutionStop()

    async def commandHandler(self, app: Slave, message: GroupMessage):
        commands: [str] = message.messageChain.asDisplay().split(' ')
        cmd = commands[0].upper()
        msg = []
        if cmd == self.APP_COMMANDS[0]:
            info: dict = await EconomyAPI.Economy.money(message.sender.id)
            b = Plain(f"\n余额:  {info['balance']}只{EconomyAPI.unit}")
            al = info['credit_pay_adjust'] + EconomyAPI.credit_pay['base_balance']
            c = Plain(f"\n{EconomyAPI.unit}呗:\n  已用额度: {info['credit_pay_use']}\n  总额度: {al}")
            p = Plain(f"\n支付方式: {EconomyAPI.payments[info['payment']]}")
            m = Plain(f"\n.pm 切换支付方式")
            msg = [At(message.sender.id), b, c, p, m]
        if cmd == self.APP_COMMANDS[1]:
            try:
                if (payment := int(commands[1])) in [1, 3, 2, 4]:
                    await EconomyAPI.Economy.payment(message.sender.id, payment)
                    msg.append(Plain(f"切换到{EconomyAPI.payments[payment]}"))
                else:
                    msg.append(Plain(f"\n{json.dumps(EconomyAPI.payments, ensure_ascii=False)}"))
            except (ValueError, IndexError):
                msg.append(Plain('.pm 1|2|3|4'))
        if cmd == self.APP_COMMANDS[2]:
            member_list: list = await app.memberList(message.sender.group)
            users: dict = await EconomyAPI.Economy.users()
            top_users = [[x.name, users[str(x.id)]['balance']] for x in member_list if str(x.id) in users.keys()]
            top_users.sort(key=lambda k: k[1], reverse=True)
            top_users = top_users[:20]
            top: str = '财富榜'
            for user in top_users:
                name, balance = user
                top += f"\n{name}: {balance}{EconomyAPI.unit}"
            msg = [Plain(top)]
        if cmd == self.APP_COMMANDS[3]:
            args: list = self.command.get('args')
            print(args)
            if isinstance(args[0], int):
                args[0] = str(args[0])
            if args[0].isnumeric() and args[1].isnumeric() and int(args[1]) > 0:
                target: int = int(args[0])
                count: int = int(args[1])
                if await EconomyAPI.Economy.has(str(target), create=False):
                    if await EconomyAPI.Economy.pay(message.sender.id, EconomyAPI.capitalist, count):
                        tax: int = int(count * .1)
                        await EconomyAPI.Economy.pay(EconomyAPI.capitalist, target, count - tax)
                        msg.extend([Plain(f'成功付给'), At(target), Plain(f'{count - tax} {EconomyAPI.unit}')])
                    else:
                        msg.append(Plain(f'你的{EconomyAPI.unit}不足'))
                else:
                    msg.append(Plain(f'你给鬼打{EconomyAPI.unit}呢？'))
            else:
                msg.append(Plain('参数错误'))
        await app.sendGroupMessage(message.sender.group.id, MeCh.create(msg))

    @staticmethod
    async def notEnough(app: Slave, message: GroupMessage, price: int):
        msg = [At(message.sender.id), Plain(f'\n余额不足:) [.mm]查看余额\n单价{price}只{EconomyAPI.unit}')]
        await app.sendGroupMessage(message.sender.group, MeCh.create(msg))
