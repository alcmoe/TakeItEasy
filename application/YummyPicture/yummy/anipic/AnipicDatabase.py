from application.YummyPicture.Database import Database


class AnipicDatabase(Database):

    def __init__(self):
        self.model = 'anipic'
        super().__init__()
