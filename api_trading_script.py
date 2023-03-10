import pandas as pd
import datetime
from api import get_api_key_pair, binance, bybit, okx, upbit
from pprint import pprint
from collections import defaultdict
from decimal import Decimal
from typing import Literal
import re

# bnc_futures = binance.FuturesTestnetApiClient(get_api_key_pair('binance_testnet'))
bnc_futures = binance.FuturesApiClient(get_api_key_pair('binance'))
bnc_spot = binance.SpotApiClient(get_api_key_pair('binance'))
#byb = bybit.TestnetApiClient(get_api_key_pair('bybit_testnet'))
byb = bybit.ApiClient(get_api_key_pair('bybit'))
# okx = okx.ApiClient(get_api_key_pair('okx_testnet'), 'Shinhan@1',is_demo=True)
okx = okx.ApiClient(get_api_key_pair('okx'), 'Shinhan@1', is_demo=False)
upt = upbit.ApiClient(get_api_key_pair('upbit'))


def place_order(
        exchange,
        instrument_type,
        base_asset,
        quote_asset,
        side,
        qty,
        order_type,
        price,
):
    if exchange == 'bnc' and instrument_type == 'spot':
        result = place_order_binance_spot(
            base_asset,
            quote_asset,
            side,
            qty,
            order_type,
            price
        )

    if exchange == 'bnc' and instrument_type == 'perp':
        result = place_order_binance_perpetual(
            base_asset,
            quote_asset,
            side,
            qty,
            order_type,
            price
        )

    ########## BYBIT ################
    ################
    if exchange == 'byb' and instrument_type == 'spot':
        result = place_order_bybit_spot(
            base_asset,
            quote_asset,
            side,
            qty,
            order_type,
            price
        )

    if exchange == 'byb' and instrument_type == 'perp':
        result = place_order_bybit_perpetual(
            base_asset,
            quote_asset,
            side,
            qty,
            order_type,
            price
        )

    if exchange == 'okx' and instrument_type == 'spot':
        result = place_order_okx_spot(
            base_asset,
            quote_asset,
            side,
            qty,
            order_type,
            price
        )

    if exchange == 'okx' and instrument_type == 'perp':
        result = place_order_okx_perpetual(
            base_asset,
            quote_asset,
            side,
            qty,
            order_type,
            price
        )

    if exchange == 'upt' and instrument_type == 'spot':
        result = place_order_upbit_spot(
            base_asset,
            quote_asset,
            side,
            qty,
            order_type,
            price
        )

    return result


def cancel_order(
        exchange: str,
        base_asset: str | None = None,
        quote_asset: str | None = None
):
    if exchange == 'bnc':
        result = cancel_order_binance(
            base_asset,
            quote_asset,

        )

    if exchange == 'byb':
        result = cancel_order_bybit(
            base_asset,
            quote_asset,
        )

    if exchange == 'okx':
        result = cancel_order_okx()

    if exchange == 'upt':
        result = cancel_order_upbit()

    return result


def query_open_order(
        exchange: str,
        base_asset: str | None = None,
        quote_asset: str | None = None
):
    if exchange == 'bnc':
        result = open_order_binance(
            base_asset,
            quote_asset,
        )

    if exchange == 'byb':  # byb V2 ??? Symbol ??? ?????????.
        result = open_order_bybit(
            base_asset,
            quote_asset,

        )

    if exchange == 'okx':
        result = open_order_okx(
            base_asset,
            quote_asset,
        )

    if exchange == 'upt':
        result = open_order_upbit()

    return result


#######################
######## OKX ####################
#######################

def place_order_okx_perpetual(
        base_asset: str,
        quote_asset: str,
        side: str,
        qty: Decimal | int | str,
        order_type: str,
        price: str | int | None = None
):
    '''OKX Contract Value'''
    res = okx.request(
        method='get',
        endpoint='/api/v5/public/instruments',
        params={
            'instType': 'SWAP',
        },
        require_signature=True,
    )

    ok_ctVal_dict = dict([(row['instId'], Decimal(row['ctVal'])) for row in res.json()['data']])
    ok_ctVal = ok_ctVal_dict[f'{base_asset.upper()}-{quote_asset.upper()}-SWAP']

    result = okx.request(
        method='post',
        endpoint='/api/v5/trade/order',
        params={

            'instId': f'{base_asset.upper()}-{quote_asset.upper()}-SWAP',
            'tdMode': 'cross',
            'side': side,
            'ordType': order_type,  # ?????? input ?????? ?????? ??????
            'sz': str(int(qty / ok_ctVal)),
            'px': str(price),
            # 'timeInForce' : 'GTC'
        },
        require_signature=True,
    ).json()

    return result


def place_order_okx_spot(
        base_asset: str,
        quote_asset: str,
        side: str,
        qty: Decimal | int | str,
        order_type: str,
        price: str | int | None = None
):
    if side == 'buy' and order_type == 'market':
        raise ValueError(f"""

    OKX Spot Market Buy ????????? {quote_asset}??? ?????? ??????????????? ?????? ????????? ?????????????????????. 
    ????????? ???????????? ??????????????????.
    order_type = "limit" ??? ?????? ??????!
                         """)

    result = okx.request(
        method='post',
        endpoint='/api/v5/trade/order',
        params={

            'instId': f'{base_asset.upper()}-{quote_asset.upper()}',
            'tdMode': 'cash',
            # Account Mode ??? ????????? ?????????.  ???????????? single-currecy ????????? cash ??????. ???????????? cross ?????????. ????????? ?????? ????????? ???????????? ???.
            'side': side,
            'ordType': order_type,  # ?????? input ?????? ?????? ??????
            'sz': str(qty),
            'px': str(price),
            # 'timeInForce' : 'GTC'
        },
        require_signature=True,
    ).json()

    return result


def open_order_okx(
        base_asset: str | None = None,
        quote_asset: str | None = None,
):
    if base_asset:
        params_perp = {
            'instId': f'{base_asset.upper()}-{quote_asset.upper()}-SWAP'
        }
        params_spot = {
                          'instId': f'{base_asset.upper()}-{quote_asset.upper()}'
                      },

        res_ = okx.request(
            method='get',
            endpoint='/api/v5/trade/orders-pending',
            params=params_perp,
            require_signature=True,
        ).json()

        result = res_['data']

        for i in range(len(result)):
            result[i]['instrument_type'] = 'perp'

        res_spot_ = okx.request(
            method='get',
            endpoint='/api/v5/trade/orders-pending',
            params=params_spot,
            require_signature=True,
        ).json()

        result_spot = res_spot_['data']

        for i in range(len(result_spot)):
            result_spot[i]['instrument_type'] = 'spot'

        result.extend(result_spot)

    else:
        params = {}
        result_ = okx.request(
            method='get',
            endpoint='/api/v5/trade/orders-pending',
            params=params,
            require_signature=True,
        ).json()
        result = result_['data']

    return result


def cancel_order_okx(
        base_asset: str | None = None,
        quote_asset: str | None = None,
):
    if base_asset:
        open_order_res_ = okx.request(
            method='get',
            endpoint='/api/v5/trade/orders-pending',
            params={
                'instId': f'{base_asset.upper()}-{quote_asset.upper()}-SWAP'
            },
            require_signature=True,
        ).json()

        open_order_res = open_order_res_['data']

        open_order_res_spot_ = okx.request(
            method='get',
            endpoint='/api/v5/trade/orders-pending',
            params={
                'instId': f'{base_asset.upper()}-{quote_asset.upper()}'
            },
            require_signature=True,
        ).json()

        open_order_res_spot = open_order_res_spot_['data']

        open_order_res.extend(open_order_res_spot)

        result = []
        for i in range(len(open_order_res)):
            res = okx.request(
                method='post',
                endpoint='/api/v5/trade/cancel-order',
                params={
                    'instId': open_order_res[i]['instId'],
                    'ordId': open_order_res[i]['ordId']
                },
                require_signature=True
            ).json()

            result.append(res)
    else:
        open_order_res_ = okx.request(
            method='get',
            endpoint='/api/v5/trade/orders-pending',
            params={},
            require_signature=True,
        ).json()

        open_order_res = open_order_res_['data']

        result = []
        for i in range(len(open_order_res)):
            res = okx.request(
                method='post',
                endpoint='/api/v5/trade/cancel-order',
                params={
                    'instId': open_order_res[i]['instId'],
                    'ordId': open_order_res[i]['ordId']
                },
                require_signature=True
            ).json()

    return result


##########################################
##############BYBIT############
###############################
def place_order_bybit_perpetual(
        base_asset: str,
        quote_asset: str,
        side: str,
        qty: Decimal | int | str,
        order_type: str,
        price: str | int | None = None
):
    if order_type == 'limit' and not price:
        raise ValueError('????????? ????????? ????????? ???????????? ?????????. Should !!')
    elif order_type == 'market' and price is not None:
        print('????????? ????????? ????????? ???????????? ????????? ?????????...(????????? ???????????????)')

    # params_v2 = {
    #              'side': 'Buy' if side == 'buy' else 'Sell',
    #              'symbol': f'{base_asset.upper()}{quote_asset.upper()}',
    #              'order_type': "Limit" if order_type == 'limit' else 'Market',
    #              'qty': str(qty),
    #              'price': str(price),
    #              'close_on_trigger': False,
    #              'time_in_force': 'GoodTillCancel',
    #              'reduce_only': False,
    #              'position_idx': 0
    #          }

    params = {
        'category': 'linear',
        'symbol': f'{base_asset.upper()}{quote_asset.upper()}',
        'side': 'Buy' if side == 'buy' else 'Sell',
        'orderType': "Limit" if order_type == 'limit' else 'Market',
        'qty': str(qty),
        'price': str(price),
    }

    result = byb.request(
        method='post',
        endpoint='/v5/order/create',
        params=params,
        require_signature=True
    ).json()

    return result


def place_order_bybit_spot(
        base_asset: str,
        quote_asset: str,
        side: str,
        qty: Decimal | int | str,
        order_type: str,
        price: str | int | None = None

):
    if side == 'buy' and order_type == 'market':
        raise ValueError(f"""

    Bybit Spot Market Buy ????????? {quote_asset}??? ?????? ??????????????? ?????? ????????? ?????????????????????. 
    ????????? ???????????? ??????????????????.
    order_type = "limit" ??? ?????? ??????!
                         """)

    if order_type == 'limit' and not price:
        raise ValueError('????????? ????????? ????????? ???????????? ?????????. Should !!')
    elif order_type == 'market' and price is not None:
        print('????????? ????????? ????????? ???????????? ????????? ?????????...(????????? ???????????????)')

    # params_v2 = {
    #     'side': 'Buy' if side == 'buy' else 'Sell',
    #     'symbol': f'{base_asset.upper()}{quote_asset.upper()}',
    #     'type': "Limit" if order_type == 'limit' else 'Market',
    #     'qty': str(qty),
    #     'price': str(price),
    #     'close_on_trigger': False,
    #     'time_in_force': 'GoodTillCancel',
    # }

    params = {
        'category': 'spot',
        'symbol': f'{base_asset.upper()}{quote_asset.upper()}',
        'side': 'Buy' if side == 'buy' else 'Sell',
        'orderType': "Limit" if order_type == 'limit' else 'Market',
        'qty': str(qty),
        'price': str(price),
    }

    result = byb.request(
        method='post',
        endpoint='/v5/order/create',
        params=params,
        require_signature=True
    ).json()

    return result


def open_order_bybit(
        base_asset: str | None = None,
        quote_asset: str | None = None,
):
    # result_ = byb.request(
    #     method='get',
    #     endpoint='/private/linear/order/search',
    #     params={'symbol':f'{base_asset.upper()}{quote_asset.upper()}'},
    #     require_signature=True
    # ).json()

    result_ = byb.request(
        method='get',
        endpoint='/v5/order/realtime',
        params={'symbol': f'{base_asset.upper()}{quote_asset.upper()}',
                'category': 'linear'},
        require_signature=True
    ).json()

    result = result_['result']['list']

    for i in range(len(result)):
        result[i]['instrument_type'] = 'perp'

    result_spot_ = byb.request(
        method='get',
        endpoint='/v5/order/realtime',
        params={'symbol': f'{base_asset.upper()}{quote_asset.upper()}',
                'category': 'spot'},
        require_signature=True
    ).json()

    result_spot = result_spot_['result']['list']

    for i in range(len(result_spot)):
        result_spot[i]['instrument_type'] = 'spot'

    result.extend(result_spot)

    return result


def cancel_order_bybit(
        base_asset: str | None = None,
        quote_asset: str | None = None,

):
    # open_order_res_ = byb.request(
    #     method='get',
    #     endpoint='/private/linear/order/search',
    #     params={'symbol':f'{base_asset.upper()}{quote_asset.upper()}'},
    #     require_signature=True
    # ).json()
    #
    # open_order_res = open_order_res_['result']
    #
    open_order_res_ = byb.request(
        method='get',
        endpoint='/v5/order/realtime',
        params={'symbol': f'{base_asset.upper()}{quote_asset.upper()}',
                'category': 'linear'},
        require_signature=True
    ).json()

    open_order_res = open_order_res_['result']['list']

    result = []
    for i in range(len(open_order_res)):
        res = byb.request(
            method='post',
            endpoint='/v5/order/cancel',
            params={'symbol': f'{base_asset.upper()}{quote_asset.upper()}',
                    'orderId': open_order_res[i]['orderId'],
                    'category': 'linear',
                    },
            require_signature=True
        ).json()

        result.append(res)

    open_order_res_spot_ = byb.request(
        method='get',
        endpoint='/v5/order/realtime',
        params={'symbol': f'{base_asset.upper()}{quote_asset.upper()}',
                'category': 'spot'},
        require_signature=True
    ).json()

    open_order_res_spot = open_order_res_spot_['result']['list']

    result_spot = []
    for i in range(len(open_order_res_spot)):
        res_spot = byb.request(
            method='post',
            endpoint='/v5/order/cancel',
            params={'symbol': f'{base_asset.upper()}{quote_asset.upper()}',
                    'orderId': open_order_res_spot[i]['orderId'],
                    'category': 'spot',
                    },
            require_signature=True
        ).json()

        result_spot.append(res_spot)

    result.extend(result_spot)

    return result


#######################
######## BINANCE ####################
#######################


def place_order_binance_perpetual(
        base_asset: str,
        quote_asset: str,
        side: str,
        qty: Decimal | int | str,
        order_type: str,
        price: str | int | None = None
):
    if order_type == 'limit' and not price:
        raise ValueError('????????? ????????? ????????? ???????????? ?????????. Should !!')
    elif order_type == 'market' and price is not None:
        print('????????? ????????? ????????? ???????????? ????????? ?????????...(????????? ???????????????)')

    params_bnc = {
        'side': 'BUY' if side == 'buy' else 'SELL',
        'symbol': f'{base_asset.upper()}{quote_asset.upper()}',
        'type': 'LIMIT' if order_type == 'limit' else 'MARKET',
        'quantity': str(qty),
    }

    if order_type == 'limit':
        params_bnc['timeInForce'] = 'GTC'
        params_bnc['price'] = str(price)

    result = bnc_futures.request(
        method='post',
        endpoint='/fapi/v1/order',
        params=params_bnc,
        require_signature=True
    ).json()

    return result


def place_order_binance_spot(

        base_asset: str,
        quote_asset: str,
        side: str,
        qty: Decimal | int | str,
        order_type: str,
        price: str | None = None

):
    if order_type == 'limit' and not price:
        raise ValueError('????????? ????????? ????????? ???????????? ?????????. Should !!')
    elif order_type == 'market' and price is not None:
        print('????????? ????????? ????????? ???????????? ????????? ?????????...(????????? ???????????????)')

    params_bnc = {
        'side': 'BUY' if side == 'buy' else 'SELL',
        'symbol': f'{base_asset.upper()}{quote_asset.upper()}',
        'type': 'LIMIT' if order_type == 'limit' else 'MARKET',
        'quantity': str(qty),
    }

    if order_type == 'limit':
        params_bnc['timeInForce'] = 'GTC'
        params_bnc['price'] = str(price)

    result = bnc_spot.request(
        method='post',
        endpoint='/api/v3/order',
        params=params_bnc,
        require_signature=True
    ).json()

    return result


def open_order_binance(
        base_asset: str | None = None,
        quote_asset: str | None = None,

):
    if base_asset:
        result = bnc_futures.request(
            method='get',
            endpoint='/fapi/v1/openOrders',
            params={'symbol': f'{base_asset.upper()}{quote_asset.upper()}'},
            require_signature=True
        ).json()

        for i in range(len(result)):
            result[i]['instrument_type'] = 'perp'

        result_spot = bnc_spot.request(
            method='get',
            endpoint='/api/v3/openOrders',
            params={'symbol': f'{base_asset.upper()}{quote_asset.upper()}'},
            require_signature=True
        ).json()

        for i in range(len(result_spot)):
            result_spot[i]['instrument_type'] = 'spot'

        result.extend(result_spot)

    else:
        result = bnc_futures.request(
            method='get',
            endpoint='/fapi/v1/openOrders',
            params={},
            require_signature=True
        ).json()

        for i in range(len(result)):
            result[i]['instrument_type'] = 'perp'

        result_spot = bnc_spot.request(
            method='get',
            endpoint='/api/v3/openOrders',
            params={},
            require_signature=True
        ).json()

        for i in range(len(result_spot)):
            result_spot[i]['instrument_type'] = 'spot'

        result.extend(result_spot)

    return result


def cancel_order_binance(
        base_asset: str,
        quote_asset: str,
):
    open_order_res = bnc_futures.request(
        method='get',
        endpoint='/fapi/v1/openOrders',
        # params= params_bnc,
        require_signature=True
    ).json()

    result = []

    for i in range(len(open_order_res)):
        res = bnc_futures.request(
            method='delete',
            endpoint='/fapi/v1/order',
            params={'symbol': f'{base_asset.upper()}{quote_asset.upper()}',
                    'orderId': open_order_res[i]['orderId']},
            require_signature=True
        ).json()

        result.append(res)

    result_spot = []
    open_order_spot_res = bnc_spot.request(
        method='get',
        endpoint='/api/v3/openOrders',
        # params= params_bnc,
        require_signature=True
    ).json()

    for i in range(len(open_order_spot_res)):
        res_spot = bnc_spot.request(
            method='delete',
            endpoint='/api/v3/order',
            params={'symbol': f'{base_asset.upper()}{quote_asset.upper()}',
                    'orderId': open_order_spot_res[i]['orderId']},
            require_signature=True
        ).json()

        result_spot.append(res_spot)

    result.extend(result_spot)

    return result


def place_order_upbit_spot(
        base_asset: str,
        quote_asset: str,
        side: str,
        qty: Decimal | int | str,
        order_type: str,
        price: str | int | None = None

):
    if side == 'buy' and order_type == 'market':
        raise ValueError(f"""

    Upbit Spot Market Buy/SELL ????????? {quote_asset}??? ?????? ??????????????? ?????? ????????? ?????????????????????. 
    ????????? ???????????? ??????????????????.
    order_type = "limit" ??? ?????? ??????!
                         """)

    if order_type == 'limit' and not price:
        raise ValueError('????????? ????????? ????????? ???????????? ?????????. Should !!')
    elif order_type == 'market' and price is not None:
        print('????????? ????????? ????????? ???????????? ????????? ?????????...(????????? ???????????????)')

    params = {
        'market': f'{quote_asset.upper()}-{base_asset.upper()}',
        'side': 'bid' if side == 'buy' else 'ask',
        'volume': str(qty),
        'price': str(price),
    }

    if order_type == 'limit':
        params['ord_type'] = 'limit'
    elif order_type == 'market' and side == 'buy':
        params['ord_type'] = 'price'
    elif order_type == 'market' and side == 'sell':
        params['ord_type'] = 'market'

    result = upt.request(
        method='post',
        endpoint='/v1/orders',
        params=params,
    ).json()

    return result


def open_order_upbit():
    result = upt.request(
        method='get',
        endpoint='/v1/orders',
        params={'state': 'wait'},
    ).json()

    return result


def cancel_order_upbit():
    open_order_res = upt.request(
        method='get',
        endpoint='/v1/orders',
        params={'state': 'wait'},
    ).json()

    result = []
    for i in range(len(open_order_res)):
        open_order_uuid = open_order_res[i]['uuid']

        cancel_order_res = upt.request(
            method='delete',
            endpoint='/v1/order',
            params={'uuid': open_order_uuid},
        ).json()

        result.append(cancel_order_res)

    return result