from Config import Config
from Logger import APPLogger
from .InitConfig import contents
app: str = 'Economy'
logger = APPLogger(app, 33)

configs = {
    'setting': "setting.json",
    'config': "config.json"
}

ecConfig = Config(app, configs, {'setting': '', 'config': ''})
if empty := ecConfig.checkFiles():
    insert = {}
    for option in empty:
        insert[option] = contents[option]
    ecConfig.initConfigs(insert)
del contents
