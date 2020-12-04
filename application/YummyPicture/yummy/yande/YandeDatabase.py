from application.YummyPicture.Database import Database


class YandeDatabase(Database):

    def __init__(self):
        self.model = 'yande'
        super().__init__()
