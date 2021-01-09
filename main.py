import aiohttp
import asyncio
import json
from BaseAPI import BaseAPI
from Events import Events
import os
import fileIO
from QueueItem import QueueItem,QI_Actions,QI_ItemType


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
        self.events.Events.onFolderSummary += self.main
        self.events.Events.onItemFinished += self.addItemToQueue
        self.queue = [] #store a queue of file changes. This should be type list<QueueItem>
        loop = asyncio.get_event_loop()
        self.processingQueueTask = loop.create_task(self._processQueue("NOT MEEE")) #holds the last processing queue task.
        #may wanna listen to onItemStarted to remove items from the queue that are being updated again to prevent issues.

    async def addItemToQueue(self,data):
        noError = data.data.error == None
        print(data)
        if await self.isFolder(data.data.folder) and noError:
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
        if await self.isFolder(data.data.folder) and isIdle and noNeededFiles and noNeededFiles and noNeededDirs and noNeededBytes:
            print(str(data))
            self.counter += 1
            print("Counter: " + str(self.counter))
            while not self.processingQueueTask.done():
                await asyncio.sleep(10) #this is not a mission critical task and should be done slowly.
            self.processingQueueTask = asyncio.create_task(self._processQueue(data.data.folder))
            # self._symLinkFolder(self.inputDir,self.outputDir)
            # self._checkDeadSymlink(self.outputDir)

    async def _processQueue(self,folderID):

        for item in self.queue:
            if item.folderID == folderID:
                #determine if its a folder or path.
                    # if folder then create a symlink to it and unrar any files in that directory.
                        #problem. how to handle deleting unrared items..
                    # if file attempt to determine if its in the base directory or a subdirection
                        #if its a file in the base directory then symlink the file.
                itemOutputFolder = self.outputDir + os.sep + item.itemName
                itemInputFolder = self.inputDir + os.sep + item.itemName
                if item.action == QI_Actions.UPDATE.value:
                    if item.itemType == QI_ItemType.FILE.value:
                        pass
                    elif item.itemType == QI_ItemType.DIR.value:
                        pass
                    await self._makeSymLink(self.inputDir,self.outputDir,item.itemName,self.directoryDepth)
                elif item.action == QI_Actions.DELETE.value:
                    #empty all symbolic links.
                    #if I add a extract archive function handle deleting the archive files.
                    await self._checkDeadSymlink(itemOutputFolder)
                
                self.queue.remove(item)#remove the item from the list/queue

    async def _makeSymLink(self,src,dst,item,depth):
        items = item.split(os.sep)
        items = items[0:depth]
        newItem = (os.sep).join(items)
        newSrc = src + newItem
        newDst = dst + newItem
        try:
            print("dst: {0}, src: {1}".format(newDst,newSrc))
            #os.symlink(newSrc,newDst)
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
           #os.unlink(path)


main1 = main()

loop = asyncio.get_event_loop()
#loop.run_until_complete(base.get("/rest/system/version"))
loop.run_forever()
# loop.run_until_complete(base.post("/rest/system/ping"))
