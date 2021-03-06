PATH_RES = 'res/'
PATH_IMAGE = 'image/'
PATH_FONT = 'font/'


def formatParm(raw: [str]):
    if raw[0][3:] and not raw[0][3:].isnumeric():
        return
    if raw[0][:3] == './N':
        return search(raw, 'n')
    elif raw[0][:3] == './P':
        return search(raw, 'p')
    elif raw[0][:3] == './S':
        return search(raw, 's')
    elif raw[0][:3] == './R':
        return search(raw, 'r')
    elif raw[0][:3] == './D':
        return search(raw, 'd')
    elif raw[0][:3] == './J':
        limit: str = raw[0][3:]
        limit = int(limit) if limit.isnumeric() else 3
        if len(raw) == 1:
            return False
        else:
            if not raw[1]:
                return False
            gid = raw[1]
        return {'key': 'j', 'id': gid, 'offset': 0, 'limit': limit}
    else:
        return False


def formatToNumber(stx: str) -> int:
    s = {'一': 1, '两': 2, '二': 2, '三': 3,
         '四': 4, '五': 5, '六': 6, '七': 7,
         '八': 8, '九': 9, '十': 10}
    if not stx:
        return 1
    elif stx in s.keys():
        return s[stx]
    elif stx.isdecimal():
        return int(stx)
    else:
        return 1


def search(raw: list, key: str) -> dict:
    limit = int(raw[0][3:]) if raw[0][3:].isnumeric() else 1
    if raw[-1].isnumeric():
        offset = int(raw.pop()) - 1
        raw.pop(0)
    else:
        offset = 0
        raw.pop(0)
    return {'key': key, 'tags': raw, 'offset': offset, 'count': limit, 'period': ''.join(raw) if ''.join(raw) else '1d'}
