class Object():
    def __init__(self, attributes:dict):
        self.__dict__ = attributes

    def __repr__(self):
        return str(self.__dict__)
