from application.YummyPicture import logger


class JASearcherProxyNotFoundException(Exception):

    def __str__(self):
        logger.info("Can not find proxy,check setting.json")


class JASearcherSourceNotFoundException(Exception):

    def __str__(self):
        logger.info("Can not find searcher key,check setting.json")
