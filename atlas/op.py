from . import model
from .frontend import RegisterOp

from .debug import *
from .utilities import *

uid = 0

def GetUniqueName(opname):
    global uid
    uname = f'{opname}_{uid}'
    uid += 1
    return uname

class AtlasOperator(object):
    def __init__(self, opname):
        self.name = GetUniqueName(opname)
        self.outputs = {}
        RegisterOp(self)

    def RegisterOutput(self, signal, name='result'):
        signal.parent = self
        signal.name = name
        self.outputs[name] = signal

    def __getattr__(self, key):
        return self.outputs[key]

    def Declare(self):
        raise NotImplementedError()

    def Synthesize(self):
        raise NotImplementedError()

