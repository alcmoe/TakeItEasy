from application.YummyPicture.Database import Database


class AnipicDatabase(Database):

    def __init__(self):
        super().__init__('anipic')
