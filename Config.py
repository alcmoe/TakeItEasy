import json
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
        self.path = Path.cwd().joinpath(f'application/{app}/config')
        Path(self.path).mkdir(exist_ok=True, parents=True)
        self.options = options
        self.loads = loads
        self.Configs = {}
        self.empty_config = []
        for k, v in loads.items():
            if not self.load(k):
                return
            if v:
                self.load(self.Configs[k][v])

    def checkFiles(self) -> list:
        for k, v in self.options.items():
            if not Path(self.path).joinpath(v).is_file():
                self.empty_config.append(k)
        return self.empty_config

    def initConfigs(self, contents: dict):
        for k, v in contents.items():
            config = Path(self.path).joinpath(self.options[k])
            f = open(config, 'w')
            f.write(json.dumps(v, indent=1))
            f.close()
            logger.info(f"init [{self.app} {k}]  dict successfully.")
            self.empty_config.remove(k)
        self.reload()

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
                    if not Path(config).is_file():
                        return False
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

    def getAll(self):
        return self.Configs[self.nowConfig]

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
