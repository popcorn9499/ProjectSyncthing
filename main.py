import aiohttp
import asyncio
import json
from BaseAPI import BaseAPI
from Events import Events
import os
import fileIO


class main:
    def __init__(self):
        config = {"host": "localhost", "port": 8384, "api_key": "InsertKeyHere", "inputDir": "/path/to/Torrents", "outputDir": "/path/to/TorrentsLinks", "syncthingMonitorFolderID": "someID" }
        if (os.path.isfile(os.path.join(".", "config.json")) == False):
            fileIO.fileSave("config.json",config)
        else:
            config = fileIO.fileLoad("config.json")
        
        self.inputDir = config["inputDir"]
        self.outputDir = config["outputDir"]
        self.folderID = config["syncthingMonitorFolderID"]
        self.base = BaseAPI(config["api_key"],host=config["host"],port=config["port"])
        self.events = Events(config["api_key"],host=config["host"],port=config["port"])
        self.events.Events.onFolderSummary += self.main

    async def main(self, data):
        print()
        isFolder = data.data.folder == self.folderID
        isIdle = data.data.summary["state"] == "idle"
        noNeededFiles = data.data.summary["needFiles"]==0
        noNeededDirs = data.data.summary["needDirectories"]==0
        noNeededBytes = data.data.summary["needBytes"]==0
        if isFolder and isIdle and noNeededFiles and noNeededFiles and noNeededDirs and noNeededBytes:
            print(str(data))
            print(" ")
            # self._symLinkFolder(self.inputDir,self.outputDir)
            # self._checkDeadSymlink(self.outputDir)

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

    async def _checkDeadSymlink(self,path):
        #os.path.islink(filename) and not os.path.exists(filename)
        for subdir,dirs,files in os.walk(path):
            for file in files:
                if os.path.islink(subdir+ "/" +file) and not os.path.exists(subdir + "/" + file):
                    os.unlink(subdir+ "/" +file)





main1 = main()

loop = asyncio.get_event_loop()
#loop.run_until_complete(base.get("/rest/system/version"))
loop.run_forever()
# loop.run_until_complete(base.post("/rest/system/ping"))
