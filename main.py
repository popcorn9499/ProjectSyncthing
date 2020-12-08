import aiohttp
import asyncio
import json
from BaseAPI import BaseAPI
from Events import Events
import os
import fileIO

config = {"host": "localhost", "port": 8384, "api_key": "InsertKeyHere" }
if (os.path.isfile(os.path.join(".", "config.json")) == False):
    fileIO.fileSave("config.json",config)
else:
    config = fileIO.fileLoad("config.json")


base = BaseAPI(config["api_key"],host=config["host"],port=config["port"])
events = Events(config["api_key"],host=config["host"],port=config["port"])
loop = asyncio.get_event_loop()
#loop.run_until_complete(base.get("/rest/system/version"))
loop.run_forever()
# loop.run_until_complete(base.post("/rest/system/ping"))
