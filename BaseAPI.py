import asyncio
import aiohttp
import json

class BaseAPI:
    _headers={}
    _baseURL=""
    
    def __init__(self,apiKey, host="localhost",port=8384):
        self._headers = {'X-API-key': apiKey}
        self._baseURL = "http://{host}:{port}{endpoint}".format(host=host,port=port,endpoint="{endpoint}")
        self._retryTime = 60
        self._retryMessage = "Retrying Connection Error"

    async def post(self,endpoint,params=[]):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self._baseURL.format(endpoint=endpoint),headers=self._headers,params=params) as resp:
                    return await resp.json()
        except (aiohttp.client_exceptions.ClientConnectorError,aiohttp.client_exceptions.ClientPayloadError):
            print(self._retryMessage)
            await asyncio.sleep(self._retryTime)
            await self.post(endpoint,params=params)

    async def get(self,endpoint,params=[]):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self._baseURL.format(endpoint=endpoint),headers=self._headers,params=params) as resp:
                    return await resp.json()
        except (aiohttp.client_exceptions.ClientConnectorError,aiohttp.client_exceptions.ClientPayloadError):
            print(self._retryMessage)
            await asyncio.sleep(self._retryTime)
            await self.get(endpoint,params=params)