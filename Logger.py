import os
from pathlib import Path

import colorlog
import logging
from logging import handlers

level = logging.DEBUG
log_colors_config = {
    'DEBUG': 'bold_white',  # cyan white
    'INFO': 'bold_green',
    'WARNING': 'bold_yellow',
    'ERROR': 'red',
    'EXCEPTION': 'bold_red',
}
fmt = "%(log_color)s[%(log_color)s%(asctime)s][%(levelname)s]: %(log_color)s%(message)s%(reset)s"
# logging.root.setLevel(level)
formatter = colorlog.ColoredFormatter(fmt, log_colors=log_colors_config)
stream = logging.StreamHandler()
log_dir: str = os.path.join(os.path.dirname(__file__), f'log')
Path(log_dir).mkdir(exist_ok=True)
th = handlers.TimedRotatingFileHandler(filename='log/bot_take_it_easy.log', when='D', backupCount=3, encoding='utf-8')
# stream.setLevel(level)
stream.setFormatter(formatter)
logger = logging.getLogger()
logger.setLevel(level)
logger.addHandler(stream)
logger.addHandler(th)


class APPLogger:
    app: str = ''
    lead: str = ''

    def __init__(self, app: str):
        self.app = app
        self.lead = f"[{self.app}]: "

    def info(self, msg):
        return logger.info(self.lead + msg)

    def error(self, msg):
        return logger.error(self.lead + msg)

    def debug(self, msg):
        return logger.debug(self.lead + msg)

    def warning(self, msg):
        return logger.warning(self.lead + msg)

    def exception(self, msg):
        return logger.exception(self.lead + msg)
