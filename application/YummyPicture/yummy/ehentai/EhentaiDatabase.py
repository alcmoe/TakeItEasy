from application.YummyPicture.Database import Database


class EhentaiDatabase(Database):

    def __init__(self):
        super().__init__('ehentai')
