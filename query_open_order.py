from decimal import Decimal
from api_trading_script import place_order, cancel_order, query_open_order
from pprint import pprint

'''
Bybit V2 는 cancel, query open order 에서 symbol이 필수이기 때문에 base_asset, quote_asset을 인풋해야함 

Binance는 base_asset 을 None으로 주면 전체 open order 조회. symbol로 따로 조회할 필요 없이....   단 취소는 base_asset 필수 
OKX 는  base_asset 을 None으로 주면 전체 open order 조회. symbol로 따로 조회할 필요 없이
'''

exchange = 'byb'  # 'byb', 'bnc', 'okx, 'upt'

base_asset = 'btc' # 'eth'
quote_asset = 'usdt' # 'krw', 'usdt', 'busd'


if __name__ == "__main__":
    if base_asset is None:
        print('Base_asset이 None이면 모든 종목의 Open Order 조회입니다. (단, OKX, Binance만 가능)')
        quote_asset = None

    result = query_open_order(
        exchange=exchange,
        base_asset=base_asset,
        quote_asset=quote_asset,
    )

    pprint(result)