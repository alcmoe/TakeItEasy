from Config import Config
from Logger import APPLogger
from .InitConfig import contents

app: str = 'YummyPicture'
logger = APPLogger(app)

configs = {
    'setting': "setting.json",
    'yande': "yande.json",
    'konachan': "konachan.json",
    'anipic': "anipic.json",
    'ehentai': "ehentai.json"
}

ymConfig = Config(app, configs, {'setting': 'ripper'})
if empty := ymConfig.checkFiles():
    insert = {}
    for option in empty:
        insert[option] = contents[option]
    ymConfig.initConfigs(insert)
del contents
