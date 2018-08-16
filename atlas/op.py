from . import model
from .frontend import RegisterOp, CurrentModule

from .debug import *
from .utilities import *

name_uid_map = {}

def GetUniqueName(opname):
    global name_uid_map

    if opname not in name_uid_map:
        uid = 0
        name_uid_map[opname] = uid
    else:
        name_uid_map[opname] += 1
        uid = name_uid_map[opname]

    return f'{opname}_{uid}'

class AtlasOperator(object):
    def __init__(self, opname):
        self.name = GetUniqueName(opname)
        self.signals = {}
        RegisterOp(self)

    def RegisterSignal(self, signal, name='result'):
        signal.parent = self
        signal.name = name
        self.signals[name] = signal

    def __getattr__(self, key):
        return self.signals[key]

    def Declare(self):
        raise NotImplementedError()

    def Synthesize(self):
        raise NotImplementedError()

