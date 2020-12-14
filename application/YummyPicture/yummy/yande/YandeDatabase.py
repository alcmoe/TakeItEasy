from application.YummyPicture.Database import Database


class YandeDatabase(Database):

    def __init__(self):
        super().__init__('yande')
