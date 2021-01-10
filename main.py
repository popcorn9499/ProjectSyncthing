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
        self.events.Events.onStateChanged += self.stateChanged
        self.queue = [] #store a queue of file changes. This should be type list<QueueItem>
        loop = asyncio.get_event_loop()
        self.processingQueueTask = loop.create_task(self._startingCleaning()) #holds the last processing queue task.
        #may wanna listen to onItemStarted to remove items from the queue that are being updated again to prevent issues.

    #add items to queue with the specified date to be processed when the folder is finished syncing
    async def addItemToQueue(self,data):
        noError = data.data.error == None
        if await self.isFolder(data.data.folder) and noError: #check if we are looking at the correct folderID and that no errors have occured
            print(data)
            itemName = data.data.item
            itemType = data.data.type
            folderID = data.data.folder
            action = data.data.action
            item = QueueItem(itemName,itemType,folderID,action)
            self.queue.append(item) #add the new QueueItem Object to the list

    #the purpose of this function is to handle all the cleaning that may be required due to strange shutdowns
    async def _startingCleaning(self):
        #clean any dead links
        await self.rest.revertFolder(self.folderID)
        print("CLEANING")
        await asyncio.sleep(10)
        await self.syncingCheck(self.folderID)
        print("REMOVING DEAD LINKS")
        #potentially also remove links that just dont point to the correct directory
        await self._checkDeadSymlinks(self.outputDir)
        await asyncio.sleep(10)
        #create any links and extracted files that may be required.
        
        print("Relinking and extracting")
        #walk through folder
        maxDepth = self.inputDir.count(os.sep) - 1 + self.directoryDepth
        for root,dirs,files in os.walk(self.inputDir):
            if root.endswith(os.sep):
                root =  root[:len(root)-1]
            curDepth = root.count(os.sep) #determine the current depth we are looking at.
            if curDepth == maxDepth:
                for directory in dirs:
                    src = root + os.sep + directory
                    dst = src.replace(self.inputDir,self.outputDir)
                    await self.attemptExtraction(src)
                    await self._makeSymLink(src,dst)
                for file in files:
                    src = root + os.sep + file
                    dst = src.replace(self.inputDir,self.outputDir)
                    await self._makeSymLink(src,dst)
        print("FINISHED STARTUP")
        print("QUEUE SIZE " + str(len(self.queue)))

    #debugging so we can tell when the syncing state has changed
    async def stateChanged(self,data):
        if await self.isFolder(data.data.folder):
            print("THE STATE HAS CHANGED {0}".format(data))

    async def main(self, data):
        isIdle = data.data.summary["state"] == "idle" or data.data.summary["state"] == "scanning" or data.data.summary["state"] == "scan-waiting"
        noNeededFiles = data.data.summary["needFiles"]==0
        noNeededDirs = data.data.summary["needDirectories"]==0
        noNeededBytes = data.data.summary["needBytes"]==0
        print("Starting QueueSize "+ str(len(self.queue)))
        # debugging to help determine why stuff did not function correctly
        if (await self.isFolder(data.data.folder)):
            print(str(data))
        print(await self.isFolder(data.data.folder))
        print("IDLE {0}".format(isIdle))
        print("noNeededFiles {0}".format(noNeededFiles))
        print("noNeededDirs {0}".format(noNeededDirs))
        print("noNeededBytes {0}".format(noNeededBytes))
        #determines if this foldersummary event was useful and whether to continue
        if await self.isFolder(data.data.folder) and isIdle and noNeededFiles and noNeededFiles and noNeededDirs and noNeededBytes:
            await asyncio.sleep(5)
            #wait for the previous process queue task to be completed before firing another one.
            while not self.processingQueueTask.done():
                await asyncio.sleep(4) #this is not a mission critical task and should be done slowly.
            while len(self.queue) > 0:
                self.processingQueueTask = asyncio.create_task(self._processQueue(data.data.folder))
                await self.processingQueueTask
                print("Queue Size until 0")
                print("Current QueueSize" + str(len(self.queue)))

    #manage the process queue until its empty
    async def _processQueue(self,folderID):
        for item in self.queue:
            try:
                if item.folderID == folderID:
                    #check between each iteration to determine if the process queue should halt due to syncing
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
                        #attempt to extract any files in the input directory before creating the symlink
                        await self.attemptExtraction(itemInputFolder)
                        #create the symbolic link
                        await self._makeSymLinkProcessing(self.inputDir,self.outputDir,item.itemName,self.directoryDepth)
                    elif item.action == QI_Actions.DELETE.value:
                        #Delete any extracted items so the folder can be properly deleted
                        await self.extractDeletion(itemInputFolder)
                        #unlink the dead symlink to declutter the output folder
                        await self._checkDeadSymlink(itemOutputFolder)
                        if not os.path.islink(itemOutputFolder) and os.path.exists(itemOutputFolder): #remove the directory if it is not a link.
                            os.removedirs(itemOutputFolder) 
            except Exception as e:
                print("Error " + str(e))
            print("Next")
            self.queue.remove(item)#remove the item from the list/queue
        print("DONE")

    #check to see if we have idled for a long enough period of time
    async def syncingCheck(self,folderID):
        delta=0
        print("Checking Idle status")
        while delta < 60:
            print("Idled for: {0} seconds".format(delta))
            result = await self.rest.getStatus(folderID)
            lastSync = await self.createDateTime(result["stateChanged"]) 
            delta = (datetime.now() - lastSync).seconds
            await asyncio.sleep(15)
        print("Idled Long Enough")

    #take the time syncthing gives and return a datetime object
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

    #find the directory of a file/or if its a directory and return the directory path
    async def _findFileDirectory(self,item):
        directory = item
        if (os.path.isfile(item)): #if its a file determine the files parent directory
            print("Find File Directory LOOKING " + item)
            lastSlash = item.rfind(os.sep)
            directory = item[:lastSlash]
        return directory

    #extract any items in the parent directory
    async def attemptExtraction(self,extractItem):
        extractionDir = await self._findFileDirectory(extractItem)
        for item in os.listdir(extractionDir):
            alreadyDone = os.path.exists(extractionDir+os.sep+"filesExtracted.json")
            extractable = await archiveHandler.archiveHandler.isSupportedArchive(item)
            try:
                if extractable and not alreadyDone:#if its a supported archive attempt to unrar
                    archiveContents = await archiveHandler.archiveHandler.listArchive(extractionDir+os.sep+item)
                    await archiveHandler.archiveHandler.extractArchive(item,extractionDir)
                    if len(archiveContents) > 0: #prevents us from saying we extracted a empty archive.
                        print("Extracted " + item)
                        await self.fileSave(extractionDir+os.sep+"filesExtracted.json", archiveContents)
                        break #leave loop once we found the good archive to extract
            except:
                pass
    
    #delete files that were extracted cleaning up the extraction
    async def extractDeletion(self,extractItem):
        extractionDir = await self._findFileDirectory(extractItem)
        if os.path.exists(extractionDir): #if this folder still exists try to delete any items inside and the folder itself.
            archiveContents = await self.fileLoad(extractionDir+os.sep+"filesExtracted.json") #load the file containing the items extracted
            for item in archiveContents:
                print("DELETING " + item)
                os.remove(extractionDir+os.sep+item)
            os.remove(extractionDir+os.sep+"filesExtracted.json")
            os.removedirs(extractionDir)#remove the trailing directory that syncthing didnt delete due to files in that directory

    async def fileLoad(self,fileName):#loads files
        with open(fileName, 'r') as handle:#loads the json file
            config = json.load(handle) 
        return config


    async def fileSave(self,fileName,config):#saves files in jason formate
        print("Saving")
        f = open(fileName, 'w') #opens the file your saving to with write permissions
        f.write(json.dumps(config,sort_keys=True, indent=4 ) + "\n") #writes the string to a file
        f.close() #closes the file io

    #create a symlink to the output directory from the input directory
    async def _makeSymLinkProcessing(self,src,dst,item,depth):
        items = item.split(os.sep)
        items = items[0:depth+1]
        newItem = (os.sep).join(items)
        print("items {0}".format(items))
        newSrc = src + newItem
        newDst = dst + newItem
        await self._makeSymLink(newSrc,newDst)

    async def _makeSymLink(self,src,dst):
        #attempts to make any missing directories if  at all possible. failure should only occur if the directory already exists
        try:
            items = dst.split(os.sep)
            items = items[:len(items)-1]
            item = os.sep.join(items)
            print(item)
            os.makedirs(item) #make the directories leading up to our symbolic link
        except:
            pass
        try: #create the sym link
            print("dst: {0}, src: {1}".format(src,dst))
            '''
            # should add a check to determine if its a file or a directory. directories
            # should be symlinked files should be hard linked
            '''
            if os.path.isdir(src):
                os.symlink(src,dst)
            elif os.path.isfile(src):
                os.link(src,dst)
        except FileExistsError as e:
            print("FILE ALREADY EXIST {0}".format(src))

    #check if it is the folderID we are supposed to look at
    async def isFolder(self,folderID):
        return folderID == self.folderID

    async def _checkDeadSymlinks(self,path):
        for subdir,dirs,files in os.walk(path):
            print(files)
            print(subdir)
            for file in files:
                await self._checkDeadSymlink(subdir+ "/" +file)
                if len(os.listdir(subdir)) == 0: #remove the directory if its empty.
                    os.removedirs(subdir)

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
