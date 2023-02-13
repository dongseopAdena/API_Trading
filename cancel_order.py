from decimal import Decimal
from api_trading_script import place_order, cancel_order, query_open_order
from pprint import pprint


'''
Binance cancel 은 symbol이 필수이기 때문에 base_asset, quote_asset을 인풋해야함     단 query open order는 전체 조회 가능
Bybit V2 는 cancel, query open order 에서 symbol이 필수이기 때문에 base_asset, quote_asset을 인풋해야함

OKX 는 모든  
'''

exchange = 'byb'  # 'byb', 'bnc', 'okx, 'upt'
base_asset = 'btc'   # 'eth'
quote_asset = 'usdt' # 'krw', 'usdt', 'busd'


if __name__ == "__main__":
    if base_asset is None:
        print('Base_asset이 None이면 전체 미체결된 모든 Open Order에 대한 취소입니다. (단, OKX만 가능)')
        quote_asset = None

    result = cancel_order(
        exchange=exchange,
        base_asset=base_asset,
        quote_asset=quote_asset,
    )

    pprint(result)