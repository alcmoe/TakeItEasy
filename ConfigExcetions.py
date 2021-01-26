from Logger import APPLogger

logger = APPLogger('Config', 36)


class ConfigNotFoundException(Exception):

    def __init__(self, config: str):
        self.config = config

    def __str__(self):
        logger.exception("Unknown config " + self.config)


class ConfigKeyNotFoundException(Exception):
    def __init__(self, key: str):
        self.key = key

    def __str__(self):
        logger.exception("Unknown key " + self.key)
