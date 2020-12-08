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
        self.loop = asyncio.get_event_loop()
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
            for event in eventData:
                self._last_seen_id = event["id"]
                print(event)
                eventType = event["type"]
                data = Object(event["data"])
                data = Object({"time": event["time"], "data": data})
                
                #fire any events that occured
                if eventType == "ConfigSaved":
                    await self.events.onConfigSaved(data)
                elif eventType == "DeviceConnected":
                    await self.events.onDeviceConnected(data)
                elif eventType == "DeviceDisconnected":
                    await self.events.onDeviceDisconnected(data)
                elif eventType == "DeviceDiscovered":
                    await self.events.onDeviceDiscovered(data)
                elif eventType == "DevicePaused":
                    await self.events.onDevicePaused(data)
                elif eventType == "DeviceResumed":
                    await self.events.onDeviceResumed(data)
                elif eventType == "DeviceRejected":
                    await self.events.onDeviceRejected(data)
                elif eventType == "DownloadProgress":
                    await self.events.onDownloadProgress(data)
                elif eventType == "FolderCompletion":
                    await self.events.onFolderCompletetion(data)
                elif eventType == "FolderErrors":
                    await self.events.onFolderErrors(data)
                elif eventType == "FolderRejected":
                    await self.events.onFolderRejected(data)
                elif eventType == "FolderScanProgress":
                    await self.events.onFolderScanProgress(data)
                elif eventType == "FolderSummary":
                    await self.events.onFolderSummary(data)
                elif eventType == "ItemFinished":
                    await self.events.onItemFinished(data)
                elif eventType == "itemStarted":
                    await self.events.onItemStarted(data)
                elif eventType == "ListenAddressesChanged":
                    await self.events.onListenAddressesChanged(data)
                elif eventType == "LocalChangeDetected":
                    await self.events.onLocalChangeDetected(data)
                elif eventType == "LocalIndexUpdated":
                    await self.events.onLocalIndexUpdated(data)
                elif eventType == "LoginAttempt":
                    await self.events.onLoginAttempt(data)
                elif eventType == "RemoteChangeDetected":
                    await self.events.onRemoteChangeDetected(data)
                elif eventType == "RemoteDownloadProgress":
                    await self.events.onRemoteDownloadProgress(data)
                elif eventType == "RemoteIndexUpdated":
                    await self.events.onRemoteIndexUpdated(data)
                elif eventType == "Starting":
                    await self.events.onStarting(data)
                elif eventType == "StartupComplete":
                    await self.events.onStartupComplete(data)
                elif eventType == "StateChanged":
                    await self.events.onStateChanged(data)
                


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
        self.onStarting = EventHook()
        self.onStartupComplete = EventHook()
        self.onStateChanged = EventHook()
