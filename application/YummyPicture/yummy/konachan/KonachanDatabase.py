from application.YummyPicture.Database import Database


class KonachanDatabase(Database):

    def __init__(self):
        super().__init__('konachan')
