from EventHook import EventHook
from BaseAPI import BaseAPI
import asyncio
from Object import Object

class Events(BaseAPI):
    def __init__(self,apiKey,last_seen_id=None,filters=None,limit=None, *args, **kwargs):
        super().__init__(apiKey, *args, **kwargs)
        self._last_seen_id = last_seen_id or 0
        self._filters = filters
        self._limit = limit
        self._count = 0
        self.endpoint = "/rest/events"
        self.loop = asyncio.get_running_loop()
        self.loop.create_task(self._gatherEvents())

        self.Events = _Events()

    @property
    async def count(self):
        """ The number of events that have been processed by this event stream.
            Returns:
                int
        """
        return self._count

    @property
    async def last_seen_id(self):
        """ The id of the last seen event.
            Returns:
                int
        """
        return self._last_seen_id

    async def _gatherEvents(self):
        while True:
            params = {"timeout":60, "since": self._last_seen_id}
            eventData = await self.get(self.endpoint, params=params)
            #protect against returning a null object
            print(type(eventData))
            print(eventData)
            if (eventData != None and type(eventData) == list):
                for event in eventData:
                    self._last_seen_id = event["id"] #keep track of the last ID we have seen
                    print(event["data"])
                    if (type(event["data"]) == dict): #ensure this isnt a string
                        eventType = event["type"] #store the event type for easier typing
                        #store the event data into a object to make it easier to send as events
                        data = Object(event["data"])
                        data = Object({"time": event["time"], "data": data})
                        #fire any events that occured
                        if eventType == "ConfigSaved":
                            self.Events.onConfigSaved(data)
                        elif eventType == "DeviceConnected":
                            self.Events.onDeviceConnected(data)
                        elif eventType == "DeviceDisconnected":
                            self.Events.onDeviceDisconnected(data)
                        elif eventType == "DeviceDiscovered":
                            self.Events.onDeviceDiscovered(data)
                        elif eventType == "DevicePaused":
                            self.Events.onDevicePaused(data)
                        elif eventType == "DeviceResumed":
                            self.Events.onDeviceResumed(data)
                        elif eventType == "DeviceRejected":
                            self.Events.onDeviceRejected(data)
                        elif eventType == "DownloadProgress":
                            self.Events.onDownloadProgress(data)
                        elif eventType == "FolderCompletion":
                            self.Events.onFolderCompletion(data)
                        elif eventType == "FolderErrors":
                            self.Events.onFolderErrors(data)
                        elif eventType == "FolderRejected":
                            self.Events.onFolderRejected(data)
                        elif eventType == "FolderScanProgress":
                            self.Events.onFolderScanProgress(data)
                        elif eventType == "FolderSummary":
                            self.Events.onFolderSummary(data)
                        elif eventType == "ItemFinished":
                            self.Events.onItemFinished(data)
                        elif eventType == "itemStarted":
                            self.Events.onItemStarted(data)
                        elif eventType == "ListenAddressesChanged":
                            self.Events.onListenAddressesChanged(data)
                        elif eventType == "LocalChangeDetected":
                            self.Events.onLocalChangeDetected(data)
                        elif eventType == "LocalIndexUpdated":
                            self.Events.onLocalIndexUpdated(data)
                        elif eventType == "LoginAttempt":
                            self.Events.onLoginAttempt(data)
                        elif eventType == "RemoteChangeDetected":
                            self.Events.onRemoteChangeDetected(data)
                        elif eventType == "RemoteDownloadProgress":
                            self.Events.onRemoteDownloadProgress(data)
                        elif eventType == "RemoteIndexUpdated":
                            self.Events.onRemoteIndexUpdated(data)
                        elif eventType == "Starting":
                            self.Events.onStarting(data)
                        elif eventType == "StartupComplete":
                            self.Events.onStartupComplete(data)
                        elif eventType == "StateChanged":
                            self.Events.onStateChanged(data)
                            continue
            else:
                print("Some form of NoneType Error has occured")

class _Events(object):
    def __init__(self):
        self.onConfigSaved = EventHook()
        self.onDevicePaused = EventHook()
        self.onDeviceConnected = EventHook()
        self.onDeviceDisconnected = EventHook()
        self.onDeviceDiscovered = EventHook()
        self.onDevicePaused = EventHook()
        self.onDeviceRejected = EventHook()
        self.onDeviceResumed = EventHook()
        self.onDownloadProgress = EventHook()
        self.onFolderCompletion = EventHook()
        self.onFolderErrors = EventHook()
        self.onFolderRejected = EventHook()
        self.onFolderScanProgress = EventHook()
        self.onFolderSummary = EventHook()
        self.onItemFinished = EventHook()
        self.onItemStarted = EventHook()
        self.onListenAddressesChanged = EventHook()
        self.onLocalChangeDetected = EventHook()
        self.onLocalIndexUpdated = EventHook()
        self.onLoginAttempt = EventHook()
        self.onRemoteChangeDetected = EventHook()
        self.onRemoteDownloadProgress = EventHook()
        self.onRemoteIndexUpdated = EventHook()
        self.onStarting = EventHook()
        self.onStartupComplete = EventHook()
        self.onStateChanged = EventHook()
