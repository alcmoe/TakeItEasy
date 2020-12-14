from application.YummyPicture.yummy.yande.YandeRipper import *
from application.YummyPicture.yummy.konachan import KonachanData


class KonachanRipper(YandeRipper):

    def __init__(self):
        super(KonachanRipper, self).__init__()
        self.rip = 'https://konachan.com/'
        self.per_page = 21

    def _formatData(self, data: list):
        result: [KonachanData] = []
        for KonachanDataOne in data:
            konachan: KonachanData = KonachanData()
            yr = KonachanDataOne['rating']
            if self.has_action == RipperConst.POPULAR and ymConfig.getConfig('konachan').get('rating')[yr] > \
                    ymConfig.getConfig('konachan').get('rating')[self.has_rating]:
                continue
            konachan.__dict__.update(KonachanDataOne)
            result.append(konachan)
        return result
