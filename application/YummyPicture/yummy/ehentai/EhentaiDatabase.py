from application.YummyPicture.Database import Database


class EhentaiDatabase(Database):

    def __init__(self):
        self.model = 'ehentai'
        super().__init__()
