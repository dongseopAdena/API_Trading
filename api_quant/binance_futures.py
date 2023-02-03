import hashlib
import hmac
import time
from typing import Any
from urllib.parse import urlencode

import aiohttp
import requests

try:
    from util import logger
except ModuleNotFoundError:
    import logging
    logger = logging.getLogger(__name__)


class ApiClient:
    def __init__(
        self,
        key_pair: tuple[str, str],
        base_url: str = 'https://fapi.binance.com',
    ):
        self._api_key = key_pair[0]
        self._secret_key = key_pair[1]
        self._base_url = base_url
    
    def get(
        self,
        endpoint: str,
        params: dict[str, Any] | None = None,
        require_api_key: bool = False,
        require_signature: bool = False,
    ) -> requests.Response:
        return self.request(method='get', endpoint=endpoint, params=params, require_api_key=require_api_key, require_signature=require_signature)
    
    def post(
        self,
        endpoint: str,
        params: dict[str, Any] | None = None,
        require_api_key: bool = False,
        require_signature: bool = False,
    ) -> requests.Response:
        return self.request(method='post', endpoint=endpoint, params=params, require_api_key=require_api_key, require_signature=require_signature)
    
    def put(
        self,
        endpoint: str,
        params: dict[str, Any] | None = None,
        require_api_key: bool = False,
        require_signature: bool = False,
    ) -> requests.Response:
        return self.request(method='put', endpoint=endpoint, params=params, require_api_key=require_api_key, require_signature=require_signature)
    
    def delete(
        self,
        endpoint: str,
        params: dict[str, Any] | None = None,
        require_api_key: bool = False,
        require_signature: bool = False,
    ) -> requests.Response:
        return self.request(method='delete', endpoint=endpoint, params=params, require_api_key=require_api_key, require_signature=require_signature)
    
    def request(
        self,
        method: str,
        endpoint: str,
        params: dict[str, Any] | None = None,
        require_api_key: bool = False,
        require_signature: bool = False,
    ) -> requests.Response:
        if require_signature:
            require_api_key = True
        
        if params is None:
            params = {}
        
        headers = {}
        if method.upper() in ('POST', 'PUT', 'DELETE'):
            headers['Content-Type'] = 'application/json'
        if require_api_key:
            headers['X-MBX-APIKEY'] = self._api_key
        
        if require_signature:
            params['timestamp'] = int(time.time() * 1000)
            query_string = urlencode(params)
            params['signature'] = hmac.new(
                self._secret_key.encode(),
                msg=query_string.encode(),
                digestmod=hashlib.sha256
            ).hexdigest()
        
        return requests.request(
            method=method,
            url=self._base_url + endpoint,
            headers=headers,
            params=params,
        )
    
    async def request_async(
        self,
        method: str,
        endpoint: str,
        params: dict[str, Any] | None = None,
        require_api_key: bool = False,
        require_signature: bool = False,
    ):
        if require_signature:
            require_api_key = True

        headers = {}
        if method.upper() in ('POST', 'PUT', 'DELETE'):
            headers['Content-Type'] = 'application/json'
        if require_api_key:
            headers['X-MBX-APIKEY'] = self._api_key

        if require_signature:
            if params is None:
                params = {}
            
            params['timestamp'] = int(time.time() * 1000)
            query_string = urlencode(params)
            params['signature'] = hmac.new(
                self._secret_key.encode(),
                msg=query_string.encode(),
                digestmod=hashlib.sha256
            ).hexdigest()
        
        async with aiohttp.request(
            method=method,
            url=self._base_url + endpoint,
            headers=headers,
            params={k: str(params[k]) for k in params},
        ) as res:
            # TODO : Error handling
            # TODO : Is it ok to return JSON directly?
            return await res.json()


class TestnetApiClient(ApiClient):
    def __init__(
        self,
        key_pair: tuple[str, str],
    ):
        super().__init__(key_pair, 'https://testnet.binancefuture.com')
