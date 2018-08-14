
debug = True

class AtlasException(Exception):
    def __init__(self, message):
        super().__init__(message)

def AtlasAssert(cond, message):
    if debug and (not cond):
        raise AtlasException(message)