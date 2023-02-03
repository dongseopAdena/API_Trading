import hashlib
import random
import uuid
from typing import Any
from urllib.parse import urlencode, unquote

import aiohttp
import jwt  # PyJWT
import requests

try:
    from util import logger
except ModuleNotFoundError:
    import logging

    logger = logging.getLogger(__name__)


class ApiClient:
    EXCHANGE_API_ENDPOINTS = [
        '/v1/accounts',  # 전체 계좌 조회
        '/v1/orders/chance',  # 주문 가능 정보
        '/v1/order',  # 개별 주문 조회
        '/v1/orders',  # 주문 리스트 조회
        '/v1/withdraws',  # 출금 리스트 조회
        '/v1/withdraw',  # 개별 출금 조회
        '/v1/withdraws/chance',  # 출금 가능 정보
        '/v1/withdraws/coin',  # 코인 출금하기
        '/v1/withdraws/krw',  # 원화 출금하기
        '/v1/deposits',  # 입금 리스트 조회
        '/v1/deposit',  # 개별 입금 조회
        '/v1/deposits/generate_coin_address',  # 입금 주소 생성 요청
        '/v1/deposits/coin_addresses',  # 전체 입금 주소 조회
        '/v1/deposits/coin_address',  # 개별 입금 주소 조회
        '/v1/deposits/krw',  # 원화 입금하기
        '/v1/status/wallet',  # 입출금 현황
        '/v1/api_keys',  # API 키 리스트 조회
    ]
    QUOTATION_API_ENDPOINTS = [
        '/v1/market/all',  # 마켓 코드 조회
        '/v1/candles/minutes/',  # 분 캔들
        '/v1/candles/days',  # 일 캔들
        '/v1/candles/weeks',  # 주 캔들
        '/v1/candles/months',  # 월 캔들
        '/v1/trades/ticks',  # 최근 체결 내역
        '/v1/ticker',  # 현재가 정보
        '/v1/orderbook',  # 호가 정보 조회
    ]

    def __init__(
            self,
            key_pair: tuple[str, str],
            base_url: str = 'https://api.upbit.com',
    ):
        self._api_key = key_pair[0]
        self._secret_key = key_pair[1]
        self._base_url = base_url

    def get(self, endpoint: str, params: dict[str, Any] | None = None) -> requests.Response:
        return self.request(method='get', endpoint=endpoint, params=params)

    def post(self, endpoint: str, params: dict[str, Any] | None = None) -> requests.Response:
        return self.request(method='post', endpoint=endpoint, params=params)

    def delete(self, endpoint: str, params: dict[str, Any] | None = None) -> requests.Response:
        return self.request(method='delete', endpoint=endpoint, params=params)

    def request(
            self,
            method: str,
            endpoint: str,
            params: dict[str, Any] | None = None,
    ) -> requests.Response:
        if not endpoint.startswith('/'):
            endpoint = '/' + endpoint

        # 인증이 필요하지 않은 Quotation API의 경우, IP를 기반으로 limit을 확인하므로 key rotating이 필요하지 않음
        if endpoint in RevolverApiClient.QUOTATION_API_ENDPOINTS or endpoint.startswith('candles/minutes/'):
            # 2022년 8월 4일 기준, Quotation API에서 request parameter를 받는 endpoint는 없음
            return requests.request(method=method, url=self._base_url + endpoint)

        # Upbit에서는 array 형태로 입력되는 인자를 PHP 스타일로 받음 (ex. "a=1&b[]=2&b[]=3&c=4")
        # `urllib.parse.urlencode` 함수를 바로 사용하기 위해, sequence 형태 인자의 key 값에 "[]"를 붙여줌
        params_with_seq_identified: dict[str, Any] | None = None
        if params is not None:
            params_with_seq_identified = {}
            for k, v in params.items():
                if isinstance(v, list | tuple | set):
                    params_with_seq_identified[k + '[]'] = v
                else:
                    params_with_seq_identified[k] = v

        payload = {
            'access_key': self._api_key,
            'nonce': str(uuid.uuid4()),
        }
        if params_with_seq_identified is not None:
            # Upbit 형식에 맞춰 payload에 내용 추가
            m = hashlib.sha512()
            m.update(unquote(urlencode(params_with_seq_identified, doseq=True)).encode())
            payload['query_hash'] = m.hexdigest()
            payload['query_hash_alg'] = 'SHA512'

        jwt_token = jwt.encode(payload, self._secret_key)

        if method.lower == 'post':
            res = requests.request(
                method=method,
                url=self._base_url + endpoint,
                headers={
                    'Authorization': f'Bearer {jwt_token}',
                },
                json=payload,
            )
        else:
            res = requests.request(
                method=method,
                url=self._base_url + endpoint,
                headers={
                    'Authorization': f'Bearer {jwt_token}',
                },
                params=params_with_seq_identified,
            )

        return res

    async def request_async(
            self,
            method: str,
            endpoint: str,
            params: dict[str, Any] | None = None,
    ) -> requests.Response:
        if not endpoint.startswith('/'):
            endpoint = '/' + endpoint

        # 인증이 필요하지 않은 Quotation API의 경우, IP를 기반으로 limit을 확인하므로 key rotating이 필요하지 않음
        if endpoint in RevolverApiClient.QUOTATION_API_ENDPOINTS or endpoint.startswith('candles/minutes/'):
            # 2022년 8월 4일 기준, Quotation API에서 request parameter를 받는 endpoint는 없음
            async with aiohttp.request(
                    method=method,
                    url=self._base_url + endpoint,
            ) as res:
                # TODO : Error handling
                # TODO : Is it ok to return JSON directly?
                return await res.json()

        # Upbit에서는 array 형태로 입력되는 인자를 PHP 스타일로 받음 (ex. "a=1&b[]=2&b[]=3&c=4")
        # `urllib.parse.urlencode` 함수를 바로 사용하기 위해, sequence 형태 인자의 key 값에 "[]"를 붙여줌
        params_with_seq_identified: dict[str, Any] | None = None
        if params is not None:
            params_with_seq_identified = {}
            for k, v in params.items():
                if isinstance(v, list | tuple | set):
                    params_with_seq_identified[k + '[]'] = v
                else:
                    params_with_seq_identified[k] = str(v)

        payload = {
            'access_key': self._api_key,
            'nonce': str(uuid.uuid4()),
        }
        if params_with_seq_identified is not None:
            # Upbit 형식에 맞춰 payload에 내용 추가
            m = hashlib.sha512()
            m.update(unquote(urlencode(params_with_seq_identified, doseq=True)).encode())
            payload['query_hash'] = m.hexdigest()
            payload['query_hash_alg'] = 'SHA512'

        jwt_token = jwt.encode(payload, self._secret_key)

        if method.lower == 'post':
            async with aiohttp.request(
                    method=method,
                    url=self._base_url + endpoint,
                    headers={
                        'Authorization': f'Bearer {jwt_token}',
                    },
                    json={k: str(payload[k]) for k in payload},
            ) as res:
                # TODO : Error handling
                # TODO : Is it ok to return JSON directly?
                return await res.json()
        else:
            async with aiohttp.request(
                    method=method,
                    url=self._base_url + endpoint,
                    headers={
                        'Authorization': f'Bearer {jwt_token}',
                    },
                    params=params_with_seq_identified,
            ) as res:
                # TODO : Error handling
                # TODO : Is it ok to return JSON directly?
                return await res.json()


class RevolverApiClient:
    EXCHANGE_API_ENDPOINTS = [
        '/v1/accounts',  # 전체 계좌 조회
        '/v1/orders/chance',  # 주문 가능 정보
        '/v1/order',  # 개별 주문 조회
        '/v1/orders',  # 주문 리스트 조회
        '/v1/withdraws',  # 출금 리스트 조회
        '/v1/withdraw',  # 개별 출금 조회
        '/v1/withdraws/chance',  # 출금 가능 정보
        '/v1/withdraws/coin',  # 코인 출금하기
        '/v1/withdraws/krw',  # 원화 출금하기
        '/v1/deposits',  # 입금 리스트 조회
        '/v1/deposit',  # 개별 입금 조회
        '/v1/deposits/generate_coin_address',  # 입금 주소 생성 요청
        '/v1/deposits/coin_addresses',  # 전체 입금 주소 조회
        '/v1/deposits/coin_address',  # 개별 입금 주소 조회
        '/v1/deposits/krw',  # 원화 입금하기
        '/v1/status/wallet',  # 입출금 현황
        '/v1/api_keys',  # API 키 리스트 조회
    ]
    QUOTATION_API_ENDPOINTS = [
        '/v1/market/all',  # 마켓 코드 조회
        '/v1/candles/minutes/',  # 분 캔들
        '/v1/candles/days',  # 일 캔들
        '/v1/candles/weeks',  # 주 캔들
        '/v1/candles/months',  # 월 캔들
        '/v1/trades/ticks',  # 최근 체결 내역
        '/v1/ticker',  # 현재가 정보
        '/v1/orderbook',  # 호가 정보 조회
    ]

    def __init__(
            self,
            key_pairs: list[tuple[str, str]],
            base_url: str = 'https://api.upbit.com',
    ):
        self._key_pairs: list[tuple[str, str]] = []
        for access_key, secret_key in key_pairs:
            self.add_key_pair(access_key, secret_key)
        random.shuffle(self._key_pairs)

        self._index = 0
        self._base_url = base_url

    def add_key_pair(self, access_key: str, secret_key: str) -> None:
        # TODO : 주어진 key pair가 유효한지 확인 (정상적으로 입력이 되었는지?, 만료가 되지는 않았는지?)
        self._key_pairs.append((access_key, secret_key))

    def get_next_key_pair(self) -> tuple[str, str]:
        _a, _s = self._key_pairs[self._index]
        self._index = (self._index + 1) % len(self._key_pairs)
        return _a, _s

    def get(self, endpoint: str, params: dict[str, Any] | None = None) -> requests.Response:
        return self.request(method='get', endpoint=endpoint, params=params)

    def post(self, endpoint: str, params: dict[str, Any] | None = None) -> requests.Response:
        return self.request(method='post', endpoint=endpoint, params=params)

    def delete(self, endpoint: str, params: dict[str, Any] | None = None) -> requests.Response:
        return self.request(method='delete', endpoint=endpoint, params=params)

    def request(
            self,
            method: str,
            endpoint: str,
            params: dict[str, Any] | None = None,
    ) -> requests.Response:
        if not endpoint.startswith('/'):
            endpoint = '/' + endpoint

        # 인증이 필요하지 않은 Quotation API의 경우, IP를 기반으로 limit을 확인하므로 key rotating이 필요하지 않음
        if endpoint in RevolverApiClient.QUOTATION_API_ENDPOINTS or endpoint.startswith('candles/minutes/'):
            # 2022년 8월 4일 기준, Quotation API에서 request parameter를 받는 endpoint는 없음
            return requests.request(method=method, url=self._base_url + endpoint)
        elif endpoint not in RevolverApiClient.EXCHANGE_API_ENDPOINTS:
            raise ValueError(f'알 수 없는 endpoint입니다. ({endpoint})')

        # Upbit에서는 array 형태로 입력되는 인자를 PHP 스타일로 받음 (ex. "a=1&b[]=2&b[]=3&c=4")
        # `urllib.parse.urlencode` 함수를 바로 사용하기 위해, sequence 형태 인자의 key 값에 "[]"를 붙여줌
        params_with_seq_identified: dict[str, Any] | None = None
        if params is not None:
            params_with_seq_identified = {}
            for k, v in params.items():
                if isinstance(v, list | tuple | set):
                    params_with_seq_identified[k + '[]'] = v
                else:
                    params_with_seq_identified[k] = v

        # API limit이 걸려있지 않는 key를 만날 때까지 반복하여 요청
        res: requests.Response | None = None
        for _tries in range(len(self._key_pairs)):
            # 인증에 필요한 JWT token을 계산하는 과정
            access_key, secret_key = self.get_next_key_pair()
            payload = {
                'access_key': access_key,
                'nonce': str(uuid.uuid4()),
            }
            if params_with_seq_identified is not None:
                # Upbit 형식에 맞춰 payload에 내용 추가
                m = hashlib.sha512()
                m.update(unquote(urlencode(params_with_seq_identified, doseq=True)).encode())
                payload['query_hash'] = m.hexdigest()
                payload['query_hash_alg'] = 'SHA512'

            jwt_token = jwt.encode(payload, secret_key)

            if method.lower == 'post':
                res = requests.request(
                    method=method,
                    url=self._base_url + endpoint,
                    headers={
                        'Authorization': f'Bearer {jwt_token}',
                    },
                    json=payload,
                )
            else:
                res = requests.request(
                    method=method,
                    url=self._base_url + endpoint,
                    headers={
                        'Authorization': f'Bearer {jwt_token}',
                    },
                    params=params_with_seq_identified,
                )

            # `429 Too Many Requests` 오류가 아닌 경우, 반환
            if res.status_code != 429:
                return res

            logger.warning(f'API key limit에 도달하였습니다. 다른 key로 시도합니다. ({access_key=}, {method=}, {endpoint=}, {params=})')

        logger.error(f'총 {len(self._key_pairs)}개의 API키의 {endpoint} endpoint의 limit이 다다랐습니다.')
        return res