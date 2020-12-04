import json
import os.path
from pathlib import Path

from ConfigExcetions import *


class Config:
    options = {}
    Configs: dict = {}
    nowConfig: str = ''
    path: str = ''
    app: str = ''
    loads: dict = ''

    def __init__(self, app: str, options: dict, loads: dict):
        self.app = app
        self.path = os.path.join(os.path.dirname(__file__), f'application/{app}/config')
        self.options = options
        self.loads = loads
        self.Configs = {}
        for k, v in loads.items():
            self.load(k)
            if v:
                self.load(self.Configs[k][v])

    async def save(self, option: str = ''):
        if not option or option in self.options.keys():
            saves = []
            if not option:
                saves = list(self.options.keys())
            else:
                saves.append(option)
            for save in saves:
                config = Path(self.path).joinpath(self.options[save])
                try:
                    f = open(config, 'w')
                    f.write(json.dumps(self.Configs[save], indent=1))
                    f.close()
                    logger.info(f"save [{self.app} {save}]  dict successfully.")
                except IOError as e:
                    raise e
        else:
            raise ConfigNotFoundException(option)

    def load(self, option: str = ''):
        if not option or option in self.options.keys():
            loads = {}
            if not option:
                loads = self.options
            else:
                loads[option] = self.options[option]
            for (key, load) in loads.items():
                config = Path(self.path).joinpath(load)
                try:
                    if not os.path.exists(config):
                        f = open(config, 'w', encoding='UTF-8')
                        f.write(json.dumps({}, indent=1))
                        f.close()
                    f = open(config, 'r', encoding='UTF-8')
                    self.Configs[key] = json.loads(f.read())
                    f.close()
                    logger.info(f"read [{self.app} {load}]  from local dict")
                except IOError as e:
                    raise e
        return self

    def getConfig(self, option: str = ''):
        if option and option in self.options.keys():
            self.nowConfig = option
            return self
        else:
            raise ConfigNotFoundException(option)

    def get(self, key: str):
        try:
            return self.Configs[self.nowConfig][key]
        except KeyError:
            return None

    def set(self, key: str, value: any):
        self.Configs[self.nowConfig][key] = value
        return True

    def addList(self, key: str, value):
        if value not in self.Configs[self.nowConfig][key]:
            self.Configs[self.nowConfig][key].append(value)
        return True

    def rmList(self, key: str, value):
        if value in self.Configs[self.nowConfig][key]:
            self.Configs[self.nowConfig][key].remove(value)
        return True

    def addDict(self, dic: str, key, value):
        self.Configs[self.nowConfig][dic][key] = value
        return True

    def reload(self):
        self.__init__(self.app, self.options, self.loads)
        return self
