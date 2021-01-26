from application.YummyPicture.Database import Database


class PixivDatabase(Database):

    def __init__(self):
        super().__init__('pixiv')
