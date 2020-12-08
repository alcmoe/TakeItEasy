from Config import Config
from Logger import APPLogger
from .InitConfig import contents

app: str = 'UraNai'
logger = APPLogger(app)

configs = {
    'config': "config.json"
}

urnConfig = Config(app, configs, {'config': ''})
if empty := urnConfig.checkFiles():
    insert = {}
    for option in empty:
        insert[option] = contents[option]
    urnConfig.initConfigs(insert)
del contents
