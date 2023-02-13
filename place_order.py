from decimal import Decimal
from api_trading_script import place_order
from pprint import pprint

'''
OKX Market Buy 주문은 quote_asset 수량 기준으로 내야 하기 때문에, limit order로 제출 필요.
Bybit  Market Buy 주문은 quote_asset 수량 기준으로 내야 하기 때문에, limit order로 제출 필요.
Upbit  Market Buy/Sell 주문은 quote_asset 수량 기준으로 내야 하기 때문에, limit order로 제출 필요.

'''

# 'byb', 'bnc', 'okx, 'upt'
exchange = 'byb'

# 'spot', 'perp'
instrument_type = 'spot'

base_asset = 'btc'
quote_asset = 'USDT'
# 'krw', 'usdt', 'busd'

side = 'buy'  # 'sell', 'buy'
order_type = 'limit'   # 'market', 'limit'

qty = Decimal('0.15')
price = Decimal('18_000')    # upbit인 경우 KRW 기준



if __name__ == "__main__":

    result = place_order(
        exchange=exchange,
        instrument_type=instrument_type,
        base_asset=base_asset,
        quote_asset=quote_asset,
        side=side,
        qty=qty,
        order_type=order_type,
        price=price
    )

    pprint(result)