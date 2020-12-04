from Config import Config
from Logger import APPLogger

app: str = 'Economy'
logger = APPLogger(app)

configs = {
    'setting': "setting.json",
    'config': "config.json"
}

ecConfig = Config(app, configs, {'setting': '', 'config': ''})
