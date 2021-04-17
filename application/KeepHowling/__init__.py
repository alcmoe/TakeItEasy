from Config import Config
from Logger import APPLogger
from utils.thread import thread
from .InitConfig import contents

app: str = 'KeepHowling'
logger = APPLogger(app, 34)


configs = {
    'everyday': "everyday.json"
}

khConfig = Config(app, configs, {'everyday': ''})
if empty := khConfig.checkFiles():
    insert = {}
    for option in empty:
        insert[option] = contents[option]
    khConfig.initConfigs(insert)
del contents
