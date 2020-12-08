from EventHook import EventHook
from BaseAPI import BaseAPI
import asyncio


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
            data = await self.get(self.endpoint, params=params)
            for event in data:
                self._last_seen_id = event["id"]
                print(event)



class _Events(object):
    def __init__(self):
        self.onDevicePaused = EventHook()
        self.onDeviceConnected = EventHook()
        self.onDeviceDisconnected = EventHook()
        self.onDeviceDiscovered = EventHook()
        self.onDevicePaused = EventHook()
        self.onDeviceRejected = EventHook()
        self.onDeviceResumed = EventHook()
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
