import threading

from graia.application import MessageChain
from graia.application.message.elements.internal import At, Quote
from graia.broadcast import Broadcast, ExecutionStop


class Listener(threading.Thread):
    bcc: Broadcast
    APP_COMMANDS: list

    def __init__(self, bcc: Broadcast):
        super().__init__()
        self.bcc = bcc

    def active(self):
        pass

    def cmdFilter(self, message: MessageChain):
        dis: str = message.asDisplay().split(' ')
        if dis[0].upper() not in self.APP_COMMANDS:
            raise ExecutionStop()

    @staticmethod
    def atFilter(message: MessageChain):
        if not message.has(At):
            raise ExecutionStop()

    @staticmethod
    def quoteFilter(message: MessageChain):
        if not message.has(Quote):
            raise ExecutionStop()

    @staticmethod
    def atOrQuoteFilter(message: MessageChain):
        if not message.has(Quote) and not message.has(At):
            raise ExecutionStop()
