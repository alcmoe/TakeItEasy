from Config import Config
from Logger import APPLogger
from .InitConfig import contents

app: str = 'VideoRipper'
logger = APPLogger(app, 34)


configs = {
    'setting': "setting.json",
    'iwara': "iwara.json"
}

vrConfig = Config(app, configs, {'setting': 'ripper'})
if empty := vrConfig.checkFiles():
    insert = {}
    for option in empty:
        insert[option] = contents[option]
    vrConfig.initConfigs(insert)
del contents
