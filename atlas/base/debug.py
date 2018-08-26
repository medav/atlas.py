
_debug = True

def SetDebug(val=True):
    global _debug
    _debug = val

class AtlasException(Exception):
    def __init__(self, message):
        super().__init__(message)

def AtlasAssert(cond, message):
    if _debug and (not cond):
        raise AtlasException(message)