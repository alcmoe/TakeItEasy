class YummyData:
    id: int = None
    score: int = None
    tags: str = []
    url: str
    rating: str

    async def get(self, check_size: bool = False, size: str = '') -> bytes:
        pass
