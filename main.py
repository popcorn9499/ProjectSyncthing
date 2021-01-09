import aiohttp
import asyncio
import json
from BaseAPI import BaseAPI
from Events import Events
from Rest import Rest
import os
import fileIO
from QueueItem import QueueItem,QI_Actions,QI_ItemType
import archiveHandler
from datetime import datetime

class main:
    def __init__(self):
        config = {"host": "localhost", "port": 8384, "api_key": "InsertKeyHere", "inputDir": "/path/to/Torrents/", "outputDir": "/path/to/TorrentsLinks/","directoryDepth": 2, "syncthingMonitorFolderID": "someID" }
        if (os.path.isfile(os.path.join(".", "config.json")) == False):
            fileIO.fileSave("config.json",config)
        else:
            config = fileIO.fileLoad("config.json")
        self.counter = 0
        self.inputDir = config["inputDir"]
        self.outputDir = config["outputDir"]
        self.folderID = config["syncthingMonitorFolderID"]
        self.directoryDepth = config["directoryDepth"] #the depth in a directory structure to create a symbolic link in.
        self.base = BaseAPI(config["api_key"],host=config["host"],port=config["port"])
        self.events = Events(config["api_key"],host=config["host"],port=config["port"])
        self.rest = Rest(config["api_key"],host=config["host"],port=config["port"])
        self.events.Events.onFolderSummary += self.main
        self.events.Events.onItemFinished += self.addItemToQueue
        self.queue = [] #store a queue of file changes. This should be type list<QueueItem>
        loop = asyncio.get_event_loop()
        self.processingQueueTask = loop.create_task(self._processQueue("NOT MEEE")) #holds the last processing queue task.
        #may wanna listen to onItemStarted to remove items from the queue that are being updated again to prevent issues.

    async def addItemToQueue(self,data):
        noError = data.data.error == None
        
        if await self.isFolder(data.data.folder) and noError:
            print(data)
            itemName = data.data.item
            itemType = data.data.type
            folderID = data.data.folder
            action = data.data.action
            item = QueueItem(itemName,itemType,folderID,action)
            self.queue.append(item)


    async def main(self, data):
        isIdle = data.data.summary["state"] == "idle"
        noNeededFiles = data.data.summary["needFiles"]==0
        noNeededDirs = data.data.summary["needDirectories"]==0
        noNeededBytes = data.data.summary["needBytes"]==0
        print("FIRING QueueSize "+ str(len(self.queue)))
        if (await self.isFolder(data.data.folder)):
            print(str(data))
        print(await self.isFolder(data.data.folder))
        print("IDLE {0}".format(isIdle))
        print("noNeededFiles {0}".format(noNeededFiles))
        print("noNeededDirs {0}".format(noNeededDirs))
        print("noNeededBytes {0}".format(noNeededBytes))
        
        if await self.isFolder(data.data.folder) and isIdle and noNeededFiles and noNeededFiles and noNeededDirs and noNeededBytes:
            #print(str(data))
            
            print("Counter: " + str(self.counter))
            await asyncio.sleep(5)
            while not self.processingQueueTask.done():
                await asyncio.sleep(4) #this is not a mission critical task and should be done slowly.
                print("LOOPPPPINGGG")
            self.counter += 1
            print("Counter: " + str(self.counter))
            while len(self.queue) > 0:
                self.processingQueueTask = asyncio.create_task(self._processQueue(data.data.folder))
                await self.processingQueueTask
                print("Queue Size to 0")
                print("Current QueueSize" + str(len(self.queue)))
            self.counter -= 1
            print("Counter: " + str(self.counter))
            # self._symLinkFolder(self.inputDir,self.outputDir)
            # self._checkDeadSymlink(self.outputDir)
        print("QueueSize "+ str(len(self.queue)))

    async def _processQueue(self,folderID):
        for item in self.queue:
            
            try:
                if item.folderID == folderID:
                    await self.syncingCheck(item.folderID)
                    #determine if its a folder or path.
                        # if folder then create a symlink to it and unrar any files in that directory.
                            #problem. how to handle deleting unrared items..
                        # if file attempt to determine if its in the base directory or a subdirection
                            #if its a file in the base directory then symlink the file.                    
                    itemOutputFolder = self.outputDir + os.sep + item.itemName
                    itemInputFolder = self.inputDir + os.sep + item.itemName
                    print("Processing " + item.itemName)
                    
                    if item.action == QI_Actions.UPDATE.value:
                        if not os.path.exists(itemInputFolder): #exit iteration if the file does not exist
                            self.queue.remove(item)#remove the item from the list/queue
                            continue
                        if item.itemType == QI_ItemType.FILE.value:
                            pass
                        elif item.itemType == QI_ItemType.DIR.value:
                            pass
                        await self.attemptExtraction(itemInputFolder)
                        print("COMPLETED EXTRACTION")
                        await self._makeSymLink(self.inputDir,self.outputDir,item.itemName,self.directoryDepth)
                    elif item.action == QI_Actions.DELETE.value:
                        #empty all symbolic links.
                        #if I add a extract archive function handle deleting the archive files.
                        await self.extractDeletion(itemInputFolder)
                        await self._checkDeadSymlink(itemOutputFolder)
                        if not os.path.islink(itemOutputFolder) and os.path.exists(itemOutputFolder): #remove the directory if it is not a link.
                            os.removedirs(itemOutputFolder)
                    
            except Exception as e:
                print("ERRPROMG " + str(e))
                pass
            print("Next")
            self.queue.remove(item)#remove the item from the list/queue
        print("DONE")

    async def syncingCheck(self,folderID):
        result = await self.rest.getStatus(folderID)
        lastSync = await self.createDateTime(result["stateChanged"]) 
        currentTime = datetime.now()
        delta = (currentTime - lastSync).seconds
        if delta < 60 and result["state"] == "idle": 
            print("LOOPY")
            attempts = 0
            print("RESETTING")
            while attempts < 3:
                await asyncio.sleep(15)
                result = await self.rest.getStatus(folderID)
                print(result["state"])
                print(attempts)
                if result["state"] == "idle":
                    attempts += 1
                    print("IDLE")
                else:
                    print("FAIL")
                    attempts = 0
        print("DONE")

    async def createDateTime(self,time):
        date = time.split("T")[0].split("-") #represented by Year Month Day
        time = time.split("T")[1].split(".")[0].split(":") #represented by H M S
        year = int(date[0])
        month = int(date[1])
        day = int(date[2])
        hour = int(time[0])
        minute = int(time[1])
        second = int(time[2])
        date= datetime(year,month,day,hour=hour,minute=minute,second=second)
        return date

    async def _findFileDirectory(self,item):
        directory = item
        if (os.path.isfile(item)):
            lastSlash = item.rfind(os.sep)
            directory = item[:lastSlash]
        return directory

    async def attemptExtraction(self,extractItem):
        extractionDir = await self._findFileDirectory(extractItem)
        for item in os.listdir(extractionDir):
            alreadyDone = os.path.exists(extractionDir+os.sep+"filesExtracted.json")
            extractable = await archiveHandler.archiveHandler.isSupportedArchive(item)
            try:
                if extractable and not alreadyDone:#if its a supported archive attempt to unrar
                    print("LISTING ARCHIVE")
                    print(item)
                    archiveContents = await archiveHandler.archiveHandler.listArchive(extractionDir+os.sep+item)
                    print("EXTRACTING")
                    await archiveHandler.archiveHandler.extractArchive(item,extractionDir)
                    await self.fileSave(extractionDir+os.sep+"filesExtracted.json", archiveContents)
                    break #leave loop once we found the good archive to extract
            except:
                pass

    async def extractDeletion(self,extractItem):
        extractionDir = await self._findFileDirectory(extractItem)
        if os.path.exists(extractionDir):
            print("EXTRACTABLE")
            archiveContents = await self.fileLoad(extractionDir+os.sep+"filesExtracted.json")
            for item in archiveContents:
                os.remove(extractionDir+os.sep+item)
            os.remove(extractionDir+os.sep+"filesExtracted.json")
            os.removedirs(extractionDir)#remove the trailing directory that syncthing didnt delete due to files e

    async def fileLoad(self,fileName):#loads files
        with open(fileName, 'r') as handle:#loads the json file
            config = json.load(handle) 
        return config


    async def fileSave(self,fileName,config):
        print("Saving")
        f = open(fileName, 'w') #opens the file your saving to with write permissions
        f.write(json.dumps(config,sort_keys=True, indent=4 ) + "\n") #writes the string to a file
        f.close() #closes the file io

    async def _makeSymLink(self,src,dst,item,depth):
        items = item.split(os.sep)
        items = items[0:depth]
        try:
            os.makedirs(dst+os.sep+(os.sep).join(items[:depth-1])) #make the directories leading up to our symbolic link
        except:
            pass
        newItem = (os.sep).join(items)
        newSrc = src + newItem
        newDst = dst + newItem
        try: #create the sym link
            print("dst: {0}, src: {1}".format(newDst,newSrc))
            os.symlink(newSrc,newDst)
        except FileExistsError as e:
            print("FILE ALREADY EXIST {0}".format(newDst))


    async def isFolder(self,folderID):
        return folderID == self.folderID


    #I should rewrite this cleaner.
    async def _symLinkFolder(self,pathToWalk, destinationPath):
        levelDepth = len(pathToWalk.split("/")) #this splits the top dir / as ""
        levelDepth+=1 #for the directory after this level
        for subdir, dirs,files in os.walk(pathToWalk):
            try:
                #print(subdir)
                if (len(subdir.split("/")) == levelDepth):
                    #print(subdir + ": good")
                    baseDir = os.path.basename(subdir)
                    if (baseDir == ""):
                        #print("wrong")
                        splitArgs = subdir.split("/")
                        baseDir = splitArgs[len(splitArgs)-2]
                    os.symlink(subdir,self.outputDir+"/"+baseDir)
                if (subdir == self.inputDir):
                    print(files)
                    for file in files:
                        try:
                            print(file + ": good")
                            os.link(subdir+"/"+file,self.outputDir+"/"+file)
                        except:
                            pass

            except FileExistsError as e:
                print(e)
                print("FILE ALREADY EXIST {0}".format(subdir))
                pass

    async def _checkDeadSymlinks(self,path):
        #os.path.islink(filename) and not os.path.exists(filename)
        for subdir,dirs,files in os.walk(path):
            for file in files:
                self._checkDeadSymLink(subdir+ "/" +file)

    #Remove a dead symbolic link.
    async def _checkDeadSymlink(self,path):
        if os.path.islink(path) and not os.path.exists(path):
           print("Dead Link: " + path)
           os.unlink(path)


main1 = main()

loop = asyncio.get_event_loop()
#loop.run_until_complete(base.get("/rest/system/version"))
loop.run_forever()
# loop.run_until_complete(base.post("/rest/system/ping"))
