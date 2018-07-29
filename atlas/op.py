from .model import *

uid = 0

def GetUniqueName(opname):
    global uid
    uname = f'{opname}_{uid}'
    uid += 1
    return uname

class AtlasOperator:
    def __init__(self, result, opname):
        self.result = result
        self.result.name = GetUniqueName(opname)

    def Synthesize(self):
        raise NotImplementedError()

