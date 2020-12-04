from Config import Config
from Logger import APPLogger

app: str = 'TalkToMe'
logger = APPLogger(app)

configs = {
    'setting': "setting.json",
}

ttkConfig = Config(app, configs, {'setting': ''})
