from application.YummyPicture import logger


class SearcherProxyNotFoundException(Exception):

    def __str__(self):
        logger.info("Can not find proxy,check setting.json")


class SearcherKeyNotFoundException(Exception):

    def __str__(self):
        logger.info("Can not find searcher key,check setting.json")
