import pandas as pd
import datetime
from api_quant import get_api_key_pair, binance, bybit, okx, upbit
from pprint import pprint
from collections import defaultdict
from decimal import Decimal
from typing import Literal
import re

bnc_futures = binance.FuturesTestnetApiClient(get_api_key_pair('binance_testnet'))
# bnc_futures = binance.FuturesApiClient(get_api_key_pair('binance'))
bnc_spot = binance.SpotTestnetApiClient(get_api_key_pair('binance_spot_testnet'))
byb = bybit.TestnetApiClient(get_api_key_pair('bybit_testnet'))
okx = okx.ApiClient(get_api_key_pair('okx_testnet'), 'Shinhan@1',is_demo=True)
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


    return pprint(result)

def cancel_order(exchange)

    if exchange == 'bnc':
        result = cancel_order_binance()

    if exchange == 'byb':
        result = cancel_order_bybit()

    if exchange == 'okx':
        result = cancel_order_okx()

    if exchange == 'upt':
        result = cancel_order_upbit()

    return pprint(result)


#######################
######## OKX ####################
#######################

def place_order_okx_perpetual(
        base_asset: str,
        quote_asset: str,
        side: str,
        qty: Decimal | int | str,
        order_type: str,
        price: str | int | None =None
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
            'ordType': order_type,  # 우리 input 값과 포맷 동일
            'sz': str(int(qty/ok_ctVal)),
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
        price: str | int | None =None
):

    if side == 'buy' and order_type == 'market':
        raise ValueError(f"""
         
    OKX Spot Market Buy 주문은 {quote_asset}이 수량 기준이어서 주문 제출이 거부되었습니다. 
    지정가 주문으로 제출해주세요.
    order_type = "limit" 로 설정 필수!
                         """)


    result = okx.request(
        method='post',
        endpoint='/api/v5/trade/order',
        params={

            'instId': f'{base_asset.upper()}-{quote_asset.upper()}',
            'tdMode': 'cash',    # Account Mode 에 따라서 달라짐.  일반적인 single-currecy 모드는 cash 가능. 나머지는 cross 해야함. 따라서 마진 배수도 조심해야 함.
            'side': side,
            'ordType': order_type,  # 우리 input 값과 포맷 동일
            'sz': str(qty),
            'px': str(price),
            # 'timeInForce' : 'GTC'
        },
        require_signature=True,
    ).json()

    return result

def open_order_okx():

    res = okx.request(
        method='get',
        endpoint='/api/v5/trade/orders-pending',
        params={},
    require_signature = True,
    ).json()

    result = res['data']

    return result

def cancel_order_okx():

    open_order_res_ = okx.request(
        method='get',
        endpoint='/api/v5/trade/orders-pending',
        params={},
    require_signature = True,
    ).json()

    open_order_res = open_order_res_['data']

    result = []
    for i in range(len(open_order_res)):

        res = okx.request(
            method='post',
            endpoint='/api/v5/trade/cancel-order',
            params = {
                'instId': open_order_res[i]['instId'],
                'ordId': open_order_res[i]['ordId']
                     },
        require_signature=True
        ).json()

        result.append(res)


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
        price: str | int | None =None
):

    if order_type == 'limit' and not price :
        raise ValueError('지정가 주문은 가격을 입력해야 합니다. Should !!')
    elif order_type == 'market' and price is not None:
        print('시장가 주문은 가격을 입력하지 않아도 됩니다...(주문은 나갔습니다)')

    params = {
                 'side': 'Buy' if side == 'buy' else 'Sell',
                 'symbol': f'{base_asset.upper()}{quote_asset.upper()}',
                 'order_type': "Limit" if order_type == 'limit' else 'Market',
                 'qty': str(qty),
                 'price': str(price),
                 'close_on_trigger': False,
                 'time_in_force': 'GoodTillCancel',
                 'reduce_only': False,
                 'position_idx': 0
             }

    result = byb.request(
            method='post',
            endpoint='/private/linear/order/create',
            params= params,
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
     
    Bybit Spot Market Buy 주문은 {quote_asset}이 수량 기준이어서 주문 제출이 거부되었습니다. 
    지정가 주문으로 제출해주세요.
    order_type = "limit" 로 설정 필수!
                         """)


    if order_type == 'limit' and not price:
        raise ValueError('지정가 주문은 가격을 입력해야 합니다. Should !!')
    elif order_type == 'market' and price is not None:
        print('시장가 주문은 가격을 입력하지 않아도 됩니다...(주문은 나갔습니다)')

    params = {
        'side': 'Buy' if side == 'buy' else 'Sell',
        'symbol': f'{base_asset.upper()}{quote_asset.upper()}',
        'type': "Limit" if order_type == 'limit' else 'Market',
        'qty': str(qty),
        'price': str(price),
        'close_on_trigger': False,
        'time_in_force': 'GoodTillCancel',
    }

    result = byb.request(
        method='post',
        endpoint='/spot/v1/order',
        params=params,
        require_signature=True
    ).json()

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
        price: str | int | None =None
):

    if order_type == 'limit' and not price :
        raise ValueError('지정가 주문은 가격을 입력해야 합니다. Should !!')
    elif order_type == 'market' and price is not None:
        print('시장가 주문은 가격을 입력하지 않아도 됩니다...(주문은 나갔습니다)')



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
            params= params_bnc,
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

    if order_type == 'limit' and not price :
        raise ValueError('지정가 주문은 가격을 입력해야 합니다. Should !!')
    elif order_type == 'market' and price is not None:
        print('시장가 주문은 가격을 입력하지 않아도 됩니다...(주문은 나갔습니다)')


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
            params= params_bnc,
            require_signature=True
        ).json()

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

    Upbit Spot Market Buy/SELL 주문은 {quote_asset}이 수량 기준이어서 주문 제출이 거부되었습니다. 
    지정가 주문으로 제출해주세요.
    order_type = "limit" 로 설정 필수!
                         """)

    if order_type == 'limit' and not price:
        raise ValueError('지정가 주문은 가격을 입력해야 합니다. Should !!')
    elif order_type == 'market' and price is not None:
        print('시장가 주문은 가격을 입력하지 않아도 됩니다...(주문은 나갔습니다)')

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
        params= {'state': 'wait'},
    ).json()

    return result

def cancel_order_upbit():

    open_order_res = upt.request(
        method='get',
        endpoint='/v1/orders',
        params= {'state': 'wait'},
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
