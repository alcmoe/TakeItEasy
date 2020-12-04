from enum import Enum


class RipperConst(Enum):
    NEW = 'new'
    SEARCH = 'search'
    POPULAR = 'popular'
    RANDOM = 'random'
    DETAIL = 'detail'


class YandeConst(Enum):
    NEW: str = 'post'
    SEARCH: str = 'post'
    RANDOM: str = 'post'
    POPULAR: str = 'post/popular_recent'
