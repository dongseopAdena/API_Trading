from decimal import Decimal
from api_trading_script import place_order

exchange = 'upt'  # 'byb', 'bnc', 'okx, 'upt'
instrument_type = 'spot' # 'spot', 'perp'

base_asset = 'eth'
quote_asset = 'krw' # 'krw', 'usdt', 'busd'

side = 'buy'  # 'sell', 'buy'
order_type = 'limit'  # 'market', 'limit'

qty = Decimal('0.01')
price = Decimal('1_900_000')    # upbit인 경우 KRW 기준

# place_order(exchange=exchange,instrument_type=instrument_type,base_asset=base_asset,quote_asset=quote_asset,side=side,qty=qty,order_type=order_type,price=price)



if __name__ == "__main__":

    place_order(
        exchange=exchange,
        instrument_type=instrument_type,
        base_asset=base_asset,
        quote_asset=quote_asset,
        side=side,
        qty=qty,
        order_type=order_type,
        price=price
    )
