from threading import Thread

from . import logger
from . import asyncio
from .trim import getTimeCircle


async def repeatSchedule(hour: int, minute: int, second: int, function: callable, args):
    times: int = 0
    while True:
        circle: int = 24 * 60 * 60
        if not times % 5:  # 5 days to correct sleep time
            circle: int = getTimeCircle(hour, minute, second)
        logger.info(f'task {function.__name__} will run in {circle} seconds')
        await asyncio.sleep(int(circle))
        await function(*args)
        times += 1


async def repeatDelaySchedule(second: int, function: callable, args):
    while True:
        await function(*args)
        logger.info(f'task {function.__name__} will repeat in {second} seconds')
        await asyncio.sleep(second)


class ThreadTask(Thread):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    def __init__(self):
        super().__init__()

    def createTask(self, fun):
        self.loop.create_task(fun)


thread = ThreadTask()
thread.start()
