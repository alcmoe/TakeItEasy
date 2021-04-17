from pycoingecko import CoinGeckoAPI


class IcoApi:
    ico = CoinGeckoAPI()
    ico.session.proxies = {'http': 'http://127.0.0.1:1081', 'socks5': 'socks5://127.0.0.1:1080'}

    @staticmethod
    async def getPrice(name: str):
        # return IcoApi.ico.get_coin_history_by_id(name, '05-02-2021')
        return 1