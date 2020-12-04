import json
import os
from pathlib import Path

from application.YummyPicture import logger
from application.YummyPicture import YummyData


class Database:
    model: str = ''
    database: dict = {}
    databaseFile: str = ''

    def __init__(self):
        data_dir: str = os.path.join(os.path.dirname(__file__), f'save/data')
        Path(data_dir).mkdir(exist_ok=True)
        self.databaseFile = Path(data_dir).joinpath(self.model+'.json')
        self.load()

    async def save(self):
        try:
            f = open(self.databaseFile, 'w', encoding='utf-8')
            f.write(json.dumps(self.database, indent=1, ensure_ascii=False))
            f.close()
            logger.info(f"save {self.model} database successfully.")
        except IOError as e:
            raise e

    def load(self):
        if not os.path.exists(self.databaseFile):
            f = open(self.databaseFile, 'w')
            f.write(json.dumps({}))
            f.close()
        f = open(self.databaseFile, 'r', encoding='utf-8')
        self.database = json.loads(f.read())
        f.close()
        logger.info(f"read {self.model} database from local dict")

    async def find(self, id: str):
        try:
            return self.database[id]
        except KeyError:
            return {}

    async def addYummy(self, yummy: YummyData):
        exist: dict = await self.find(str(yummy.id))
        if not len(exist):
            self.database[str(yummy.id)] = yummy.__dict__
            await self.save()
            logger.info(f"add and save {str(yummy.id)} to {self.model} database")
        else:
            logger.info(f"{str(yummy.id)} already in {self.model} database")
