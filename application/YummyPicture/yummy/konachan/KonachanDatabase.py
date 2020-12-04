from application.YummyPicture.Database import Database


class KonachanDatabase(Database):

    def __init__(self):
        self.model = 'konachan'
        super().__init__()
