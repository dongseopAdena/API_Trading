from decimal import Decimal
from api_trading_script import place_order

# 'byb', 'bnc', 'okx, 'upt'
exchange = 'byb'

# 'spot', 'perp'
instrument_type = 'spot'

base_asset = 'eth'
quote_asset = 'USDT'
# 'krw', 'usdt', 'busd'

side = 'buy'  # 'sell', 'buy's
order_type = 'limit'   # 'market', 'limit'

qty = Decimal('0.01')
price = Decimal('1200')    # upbit인 경우 KRW 기준



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