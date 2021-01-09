from BaseAPI import BaseAPI
import asyncio
from Object import Object

class Rest(BaseAPI):
    
    def __init__(self,apiKey,last_seen_id=None,filters=None,limit=None, *args, **kwargs):
        super().__init__(apiKey, *args, **kwargs)

            
    
    async def getStatus(self,folderID):
        endpoint="/rest/db/status"
        params = {"folder": folderID}
        data = await self.get(endpoint, params=params)
        return data

    async def revertFolder(self,folderID):
        endpoint="/rest/db/revert"
        params = {"folder": folderID}
        data = await self.post(endpoint, params=params)
        print(data)