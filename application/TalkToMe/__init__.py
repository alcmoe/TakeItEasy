from Config import Config
from Logger import APPLogger
from .InitConfig import contents

app: str = 'TalkToMe'
logger = APPLogger(app)

configs = {
    'setting': "setting.json",
}
ttkConfig = Config(app, configs, {'setting': ''})
if empty := ttkConfig.checkFiles():
    insert = {}
    for option in empty:
        insert[option] = contents[option]
    ttkConfig.initConfigs(insert)
del contents
