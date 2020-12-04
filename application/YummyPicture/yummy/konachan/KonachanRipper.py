from application.YummyPicture.yummy.yande.YandeRipper import *
from application.YummyPicture.yummy.konachan import KonachanData


class KonachanRipper(YandeRipper):

    rawUrl: str = 'https://konachan.com/'
    rip: str = 'https://konachan.com/'
    perPage: int = 21

    def _formatData(self, data: list):
        result: [KonachanData] = []
        for KonachanDataOne in data:
            konachan: KonachanData = KonachanData()
            yr = KonachanDataOne['rating']
            if self.hasAction == RipperConst.POPULAR and ymConfig.getConfig('konachan').get('rating')[yr] > \
                    ymConfig.getConfig('konachan').get('rating')[self.hasRating]:
                continue
            konachan.__dict__.update(KonachanDataOne)
            result.append(konachan)
        return result
