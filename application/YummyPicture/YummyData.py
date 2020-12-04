class YummyData:
    id: int = None
    score: int = None
    tags: str = []
    url: str

    def __hash__(self):
        return hash(self.url)

    async def get(self, check_size: bool = False, size: str = '') -> bytes:
        pass
