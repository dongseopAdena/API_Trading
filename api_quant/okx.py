import base64
import datetime
import hashlib
import hmac
import json
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
        passphrase: str,
        base_url: str = 'https://www.okx.com',
        is_demo: bool = False
    ):
        self._api_key = key_pair[0]
        self._passphrase = passphrase
        self._secret_key = key_pair[1]
        self._base_url = base_url
        self._is_demo = is_demo
    
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
    ) -> requests.Response:
        if params is None:
            params = {}
        
        headers = {}
        
        if require_signature:
            now = time.time()
            timestamp = datetime.datetime.utcfromtimestamp(now).isoformat(timespec='milliseconds') + 'Z'
            
            if method.upper() == 'GET':
                query_string = '&'.join(
                    [str(k) + '=' + str(v) for k, v in sorted(params.items()) if v is not None]
                )
                if params:
                    prehash = f'{timestamp}{method.upper()}{endpoint}?{query_string}'
                else:
                    prehash = f'{timestamp}{method.upper()}{endpoint}'
            else:
                prehash = f'{timestamp}{method.upper()}{endpoint}{json.dumps(params)}'
            
            sign = base64.b64encode(
                hmac.new(
                    self._secret_key.encode(),
                    msg=prehash.encode(),
                    digestmod=hashlib.sha256
                ).digest()
            ).decode()
            
            headers |= {
                'OK-ACCESS-KEY': self._api_key,
                'OK-ACCESS-SIGN': sign,
                'OK-ACCESS-TIMESTAMP': timestamp,
                'OK-ACCESS-PASSPHRASE': self._passphrase,
            }
        
        if self._is_demo:
            headers |= {'x-simulated-trading': '1'}
        
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
    ):
        if params is None:
            params = {}
        
        headers = {}
        
        if require_signature:
            now = time.time()
            timestamp = datetime.datetime.utcfromtimestamp(now).isoformat(timespec='milliseconds') + 'Z'
    
            if method.upper() == 'GET':
                query_string = '&'.join(
                    [str(k) + '=' + str(v) for k, v in sorted(params.items()) if v is not None]
                )
                prehash = f'{timestamp}{method.upper()}{endpoint}?{query_string}'
            else:
                prehash = f'{timestamp}{method.upper()}{endpoint}{json.dumps(params)}'
    
            sign = base64.b64encode(
                hmac.new(
                    self._secret_key.encode(),
                    msg=prehash.encode(),
                    digestmod=hashlib.sha256
                ).digest()
            ).decode()
    
            headers |= {
                'OK-ACCESS-KEY': self._api_key,
                'OK-ACCESS-SIGN': sign,
                'OK-ACCESS-TIMESTAMP': timestamp,
                'OK-ACCESS-PASSPHRASE': self._passphrase,
            }
        
        if self._is_demo:
            headers |= {'x-simulated-trading': '1'}
        
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
