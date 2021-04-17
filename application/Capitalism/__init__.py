from Logger import APPLogger
from Config import Config
from .InitConfig import contents

app: str = 'Capitalism'
logger = APPLogger(app)

configs = {
    'config': "config.json"
}

clConfig = Config(app, configs, {'config': ''})
if empty := clConfig.checkFiles():
    insert = {}
    for option in empty:
        insert[option] = contents[option]
    clConfig.initConfigs(insert)
del contents
