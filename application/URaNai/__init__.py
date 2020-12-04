from Config import Config
from Logger import APPLogger

app: str = 'UraNai'
logger = APPLogger(app)

configs = {
    'setting': "setting.json",
    'config': "config.json"
}

urnConfig = Config(app, configs, {'setting': '', 'config': ''})