from Config import Config
from Logger import APPLogger
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
