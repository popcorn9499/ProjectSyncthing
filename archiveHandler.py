import asyncio
import subprocess




class archiveHandler:

    SUPPORTED_LIST = {".rar": rarHandler}

    async def determineArchiveType(archive):
        returntype = None #If we cannot handle this archive please take now
        for key,val in archiveHandler.SUPPORTED_LIST:    
            if archive.endswith(key):
                returntype = val
                break

        return returntype

    #checks if its a supported archive
    #returns true or false
    async def isSupportedArchive(file):
        result = False
        for key,val in archiveHandler.SUPPORTED_LIST:
            if file.endswith(key):
                result = True
        return result

    #return a list of the contents of the archive
    async def listArchive(archive):
        handler = archiveHandler.determineArchiveType(archive)
        return await handler.listArchive(archive)

    #extract the contents of the archive.
    async def extractArchive(archive,extractLocation):
        handler = archiveHandler.determineArchiveType(archive)
        await handler.extractArchive(archive,extractLocation)

#exceptions

#handlers
class rarHandler:
    async def listArchive(archive):
        output = []
        try:
            cmdOutput = subprocess.check_output('unrar lb {0}'.format(archive), shell=True) #extract the file
            cmdOutput = cmdOutput.decode()
            output = cmdOutput.strip("/n")
            output = output[:len(output)-1] #remove the '' last element in the list
        except subprocess.CalledProcessError:
            print("ERROR!!")
        return output

    async def extractArchive(archive,extractLocation):
        try:
            print(subprocess.check_output('cd {1} && unrar x -kb -y {0}'.format(archive,extractLocation), shell=True)) #extract the file
        except subprocess.CalledProcessError:
            print("ERROR!!")