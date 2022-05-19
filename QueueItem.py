from enum import Enum
from Object import Object

class QueueItem(Object):
    #itemType can be file,dir
    #action can be update,delete,metadata
    def __init__(self,itemName,itemType,folderID,action):
        payload = {"itemName": itemName, "itemType": itemType, "folderID": folderID, "action": action}
        super().__init__(payload)

class QI_Actions(Enum):
    UPDATE = "update"
    DELETE = "delete"
    METADATA = "metadata"


class QI_ItemType(Enum):
    FILE = "file"
    DIR = "dir"