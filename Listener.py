from graia.application import MessageChain
from graia.application.message.elements.internal import At, Quote, Plain
from graia.broadcast import Broadcast, ExecutionStop


class Listener:
    bcc: Broadcast
    command: dict
    APP_COMMANDS: list
    APP_QUOTE_COMMAND: list

    def __init__(self, bcc: Broadcast):
        self.bcc = bcc
        self.task()

    def run(self):
        pass

    def task(self):
        pass

    def cmdFilter(self, message: MessageChain):
        dis: str = message.asDisplay().split(' ')
        if dis[0].upper() not in self.APP_COMMANDS:
            raise ExecutionStop()
        else:
            self.command.update(cmd=dis[0].upper())

    @staticmethod
    def atFilter(message: MessageChain):
        if not message.has(At):
            raise ExecutionStop()

    @staticmethod
    def quoteFilter(message: MessageChain):
        if not message.has(Quote):
            raise ExecutionStop()

    def quoteCMDFilter(self, message: MessageChain):
        if not message.has(Quote):
            raise ExecutionStop()
        if plains := message.get(Plain):
            plain: Plain
            for cmd in (plain for plain in plains if plain.text.strip().upper() in self.APP_QUOTE_COMMAND):
                self.command.update(cmd=cmd.text.strip().upper())
                quote: Quote = message.get(Quote)[0]
                self.command.update(quote=quote)
                return
        raise ExecutionStop()

    @staticmethod
    def atOrQuoteFilter(message: MessageChain):
        if not message.has(Quote) and not message.has(At):
            raise ExecutionStop()
