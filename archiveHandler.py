import asyncio
import subprocess
from archiveHandlers.rarHandler import rarHandler


SUPPORTED_LIST = {".rar": rarHandler}
class archiveHandler:
    async def determineArchiveType(archive):
        returntype = None #If we cannot handle this archive please take now
        for key,val in SUPPORTED_LIST.items():    
            if archive.endswith(key):
                returntype = val
                break

        return returntype

    #checks if its a supported archive
    #returns true or false
    async def isSupportedArchive(file):
        result = False
        for key,val in SUPPORTED_LIST.items():
            if file.endswith(key):
                result = True
        return result

    #return a list of the contents of the archive
    async def listArchive(archive):
        handler = await archiveHandler.determineArchiveType(archive)
        return await handler.listArchive(archive)

    #extract the contents of the archive.
    async def extractArchive(archive,extractLocation):
        handler = await archiveHandler.determineArchiveType(archive)
        await handler.extractArchive(archive,extractLocation)

#exceptions

#handlers
