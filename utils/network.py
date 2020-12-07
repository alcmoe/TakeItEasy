from . import *


async def saveUrlPicture(url: str, name: str, folder: str = '', ext: str = '', connector=None) -> str:
    try:
        ext = url.split('.')[-1] if not ext else ext
        save_path = os.path.join(os.path.dirname(__file__), '..', folder)
        Path(save_path).mkdir(exist_ok=True)
        if os.path.exists(Path(save_path).joinpath(f'{name}.{ext}')):
            return '已经存下了-b'
        data = await request('GET', url, connector=connector)
        image: PImage = PImage.open(BytesIO(data))
        if connector:
            await connector.close()
        logger.debug(f'{name}.{ext}')
        image.save(Path(save_path).joinpath(f'{name}.{ext}'))
        return '帮你存下了-b'
    except ClientConnectorError:
        return '代理炸了-b'
    except IOError:
        return 'IO炸了'
    except (asyncio.TimeoutError, ValueError) as e:
        raise e


async def requestText(url: str, method: str = 'GET', headers: dict = None, params: dict = None, body=None,
                      connector: ProxyConnector = None, data=None, raw=True) -> list:
    raw_data = await request(method, url, headers=headers, body=body, connector=connector, data=data)
    if raw:
        return [str(raw_data, encoding='utf8')]
    else:
        return [json.loads(raw_data)]


async def request(method: str = 'GET', url: str = '', headers: dict = None, params: dict = None, body=None,
                  connector: ProxyConnector = None, data=None, cookies=None, close=True):
    async with aiohttp.request(method, url, headers=headers, params=params, json=body, connector=connector,
                               data=data, cookies=cookies) as response:
        raw_data = await response.read()
        if connector and close:
            await connector.close()
        return raw_data


async def w2x(url: str, connector: ProxyConnector = None) -> 'list':
    header = {'api-key': 'b26e98d9-9ce8-4a60-9479-20993ebe9f85'}
    parm = {'image': url}
    url = 'https://api.deepai.org/api/waifu2x'
    logger.debug(f'w2x -> {url}')
    re: dict = json.loads(await request('POST', url, headers=header, data=parm))
    if 'err' in re.keys():
        logger.debug(re['err'])
        x2 = 'https://deepai.org/static/images/heart-red.png'
        ext = 'png'
    else:
        x2 = re['output_url']
        ext = x2.split('.')[-1]
    return [await request(url=x2, connector=connector), x2, ext]


async def sentiment(text: str, access_token: str) -> list:
    url = f'https://aip.baidubce.com/rpc/2.0/nlp/v1/sentiment_classify?charset=UTF-8&access_token={access_token}'
    body = {
        "text": text
    }
    result = await requestText(url, 'POST', body=body, raw=False)
    result = result[0]['items'][0]
    if result['confidence'] < 0.8:
        re = [abs(result['sentiment']), result['negative_prob']]
        logger.info(f"{[result['sentiment'], result['confidence'], result['negative_prob']]} -> {re}")
    else:
        re = [result['sentiment'], result['negative_prob']]
    return re


async def refreshSentimentToken(api_key: str, secret_key: str) -> str:
    g_type = 'client_credentials'
    url = f'https://aip.baidubce.com/oauth/2.0/token?grant_type={g_type}&client_id={api_key}&client_secret={secret_key}'
    result = await requestText(url, 'POST', raw=False)
    if 'access_token' in result[0].keys():
        token = result[0]['access_token']
    else:
        token = ''
        logger.error('fetch bd_sentiment_token failed, check your api_key or secret_keys')
    return token
