from enum import Enum

from .Const import RipperConst
from .exception.RipperExceptions import *


class Ripper:

    def __init__(self):
        self.rips = {}
        self.has_action: Enum = None
        self.actions: dict = None
        self.has_tags: list = None
        self.has_rating: str = None
        self.has_count: int = 0
        self.has_offset: int = 0
        self.has_page: int = 0
        self.has_period: str = None
        self.has_specific: list = None
        self.has_parm: int = 0
        self.rip: str = ''
        self.ripe: str = None
        self.periods: dict = None
        self.per_page: int = None

    def new(self) -> 'Ripper':
        return self.action(RipperConst.NEW)

    def search(self) -> 'Ripper':
        return self.action(RipperConst.SEARCH)

    def popular(self) -> 'Ripper':
        return self.action(RipperConst.POPULAR)

    def random(self) -> 'Ripper':
        return self.action(RipperConst.RANDOM)

    def detail(self) -> 'Ripper':
        return self.action(RipperConst.DETAIL)

    def action(self, action) -> 'Ripper':
        if action.name in list(RipperConst.__members__.keys()) and not self.has_action:
            self.has_action = action
            return self
        else:
            raise RipperUnknownActionException(action)

    def offset(self, offset: str) -> 'Ripper':
        self.has_page = int(offset) // self.per_page
        self.has_offset = int(offset) % self.per_page
        return self

    def tags(self, tags: []) -> 'Ripper':
        self.verifyAction(self.has_action, 'TAGS')
        self.has_tags = tags
        return self

    def tags2str(self) -> str:
        pass

    def count(self, count: int) -> 'Ripper':
        self.has_count = count
        return self

    def period(self, period: str) -> 'Ripper':
        self.verifyAction(RipperConst.POPULAR, 'PERIOD')
        if period in self.periods.keys():
            self.has_period = period
            return self
        else:
            raise RipperNoPeriodException(period)

    def specific(self, specific: []):
        self.has_specific = specific
        return

    def verifyAction(self, action: str, method):
        if self.has_action != action:
            raise RipperErrorActionException(action, method)

    async def get(self) -> 'list':
        pass

    def rating(self, rating: str) -> 'Ripper':
        self.has_rating = rating
        return self

    def parse(self, parse: str, variant: bool = False) -> 'Ripper':
        if variant:
            self.ripe += parse
        else:
            self.rip += parse
        return self

    def parm(self, k: str, v: str = '', variant: bool = False) -> 'Ripper':
        if self.has_action:
            if v:
                v = "=" + v
            if self.has_parm:
                k = "&" + k
            if not variant:
                self.has_parm += 1
            return self.parse(k + v, variant)
        else:
            raise RipperNoActionException

    def __buildRating(self):
        pass

    def _buildVariant(self, offset: int = 0):
        page = self.has_page + offset
        self.ripe = self.rip
        if self.has_offset + self.has_count > self.per_page:
            self.parm('page', str(page))
            self.rips[self.rip] = (self.has_offset, self.per_page)
            self.parm('page', str(int(page) + 1), True)
            self.rips[self.ripe] = (0, self.has_count - (self.per_page - self.has_offset))
        else:
            self.parm('page', str(page))
            self.rips[self.rip] = (self.has_offset, self.has_count + self.has_offset)
