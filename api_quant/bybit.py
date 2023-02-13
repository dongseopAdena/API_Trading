import hashlib
import hmac
import json
import time
from typing import Any
from urllib.parse import urlencode

import aiohttp
import requests

try:
    from project_logger import logger
except ModuleNotFoundError:
    import logging

    logger = logging.getLogger(__name__)


class ApiClient:
    def __init__(
            self,
            key_pair: tuple[str, str],
            base_url: str = 'https://api.bybit.com',
    ):
        self._api_key = key_pair[0]
        self._secret_key = key_pair[1]
        self._base_url = base_url

    def get(
            self,
            endpoint: str,
            params: dict[str, Any] | None = None,
            require_signature: bool = False,
    ) -> requests.Response:
        return self.request(method='get', endpoint=endpoint, params=params, require_signature=require_signature)

    def post(
            self,
            endpoint: str,
            params: dict[str, Any] | None = None,
            require_signature: bool = False,
    ) -> requests.Response:
        return self.request(method='post', endpoint=endpoint, params=params, require_signature=require_signature)

    def request(
            self,
            method: str,
            endpoint: str,
            params: dict[str, Any] | None = None,
            require_signature: bool = False,
            recv_window: int = 5000,
    ) -> requests.Response:
        if params is None:
            params = {}

        headers = {}

        if require_signature:
            timestamp = int(time.time() * 1000)

            if len(params) == 0:
                prehash = f'{timestamp}{self._api_key}{recv_window}'
            elif method.upper() == 'GET':
                query_string = urlencode(params)
                prehash = f'{timestamp}{self._api_key}{recv_window}{query_string}'
            else:
                prehash = f'{timestamp}{self._api_key}{recv_window}{json.dumps(params)}'

            sign = hmac.new(
                self._secret_key.encode(),
                msg=prehash.encode(),
                digestmod=hashlib.sha256,
            ).hexdigest()

            headers |= {
                # 'X-BAPI-SIGN-TYPE': '2',
                'X-BAPI-SIGN': sign,
                'X-BAPI-API-KEY': self._api_key,
                'X-BAPI-TIMESTAMP': str(timestamp),
                'X-BAPI-RECV-WINDOW': str(recv_window),
            }

        if method.upper() == 'GET':
            return requests.request(
                method=method,
                url=self._base_url + endpoint,
                headers=headers,
                params={k: str(params[k]) for k in params},
            )
        else:
            return requests.request(
                method=method,
                url=self._base_url + endpoint,
                headers=headers,
                json={k: str(params[k]) for k in params},
            )

    async def request_async(
            self,
            method: str,
            endpoint: str,
            params: dict[str, Any] | None = None,
            require_signature: bool = False,
            recv_window: int = 5000,
    ):
        if params is None:
            params = {}

        headers = {}

        if require_signature:
            timestamp = int(time.time() * 1000)

            if method.upper() == 'GET':
                query_string = urlencode(params)
                prehash = f'{timestamp}{self._api_key}{recv_window}{query_string}'
            else:
                prehash = f'{timestamp}{self._api_key}{recv_window}{json.dumps(params)}'

            sign = hmac.new(
                self._secret_key.encode(),
                msg=prehash.encode(),
                digestmod=hashlib.sha256,
            ).hexdigest()

            headers |= {
                'X-BAPI-SIGN-TYPE': '2',
                'X-BAPI-SIGN': sign,
                'X-BAPI-API-KEY': self._api_key,
                'X-BAPI-TIMESTAMP': str(timestamp),
                'X-BAPI-RECV-WINDOW': str(recv_window),
            }

        if method.upper() == 'GET':
            async with aiohttp.request(
                    method=method,
                    url=self._base_url + endpoint,
                    headers=headers,
                    params={k: str(params[k]) for k in params},
            ) as res:
                # TODO : Error handling
                # TODO : Is it ok to return JSON directly?
                return await res.json()
        else:
            async with aiohttp.request(
                    method=method,
                    url=self._base_url + endpoint,
                    headers=headers,
                    json={k: str(params[k]) for k in params},
            ) as res:
                # TODO : Error handling
                # TODO : Is it ok to return JSON directly?
                return await res.json()


class TestnetApiClient(ApiClient):
    def __init__(
            self,
            key_pair: tuple[str, str],
    ):
        super().__init__(key_pair, 'https://api-testnet.bybit.com')