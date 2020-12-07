from enum import Enum

from .Const import RipperConst
from .exception.RipperExceptions import *


class Ripper:
    actions: dict
    hasAction: Enum = None
    hasTags: list
    hasRating: str
    hasCount: int
    hasOffset: int
    hasPage: int
    hasPeriod: str
    hasSpecific: list
    hasParm: int = 0
    rawUrl: str
    rip: str
    ripe: str
    periods: dict
    perPage: int

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

    def __init__(self):
        self.rips = {}

    def action(self, action) -> 'Ripper':
        if action.name in list(RipperConst.__members__.keys()) and not self.hasAction:
            self.hasAction = action
            return self
        else:
            raise RipperUnknownActionException(action)

    def offset(self, offset: str) -> 'Ripper':
        self.hasPage = int(offset) // self.perPage
        self.hasOffset = int(offset) % self.perPage
        return self

    def tags(self, tags: []) -> 'Ripper':
        self.verifyAction(self.hasAction, 'TAGS')
        self.hasTags = tags
        return self

    def tags2str(self) -> str:
        pass

    def count(self, count: int) -> 'Ripper':
        self.hasCount = count
        return self

    def period(self, period: str) -> 'Ripper':
        self.verifyAction(RipperConst.POPULAR, 'PERIOD')
        if period in self.periods.keys():
            self.hasPeriod = period
            return self
        else:
            raise RipperNoPeriodException(period)

    def specific(self, specific: []):
        self.hasSpecific = specific
        return

    def verifyAction(self, action: str, method):
        if self.hasAction != action:
            raise RipperErrorActionException(action, method)

    async def get(self) -> 'list':
        pass

    def rating(self, rating: str) -> 'Ripper':
        self.hasRating = rating
        return self

    def clear(self) -> 'Ripper':
        self.rip = self.rawUrl
        self.hasAction = ''
        self.hasParm = 0
        return self

    def parse(self, parse: str, variant: bool = False) -> 'Ripper':
        if variant:
            self.ripe += parse
        else:
            self.rip += parse
        return self

    def parm(self, k: str, v: str = '', variant: bool = False) -> 'Ripper':
        if self.hasAction:
            if v:
                v = "=" + v
            if self.hasParm:
                k = "&" + k
            if not variant:
                self.hasParm += 1
            return self.parse(k + v, variant)
        else:
            raise RipperNoActionException

    def __buildRating(self):
        pass

    def _buildVariant(self, offset: int = 0):
        page = self.hasPage + offset
        self.ripe = self.rip
        if self.hasOffset + self.hasCount > self.perPage:
            self.parm('page', str(page))
            self.rips[self.rip] = (self.hasOffset, self.perPage)
            self.parm('page', str(int(page) + 1), True)
            self.rips[self.ripe] = (0, self.hasCount - (self.perPage - self.hasOffset))
        else:
            self.parm('page', str(page))
            self.rips[self.rip] = (self.hasOffset, self.hasCount + self.hasOffset)
