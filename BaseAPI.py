import asyncio
import aiohttp
import json

class BaseAPI:
    _headers={}
    _baseURL=""
    
    def __init__(self,apiKey, host="localhost",port=8384):
        self._headers = {'X-API-Key': apiKey}
        self._baseURL = "http://{host}:{port}/{endpoint}".format(host=host,port=port,endpoint="{endpoint}")

    async def post(self,endpoint,params=[]):
        async with aiohttp.ClientSession() as session:
            async with session.post(self._baseURL.format(endpoint=endpoint),headers=self._headers,params=params) as resp:
                print(resp.status)
                return await resp.json()

    async def get(self,endpoint,params=[]):
        async with aiohttp.ClientSession() as session:
            async with session.get(self._baseURL.format(endpoint=endpoint),headers=self._headers,params=params) as resp:
                print(resp.status)
                return await resp.json()