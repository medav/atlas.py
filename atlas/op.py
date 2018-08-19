from . import model
from .context import RegisterOp, CurrentModule

from .debug import *
from .utilities import *

__all__ = [
    'AtlasOperator'
]

class AtlasOperator(object):
    name_uid_map = {}

    @staticmethod
    def GetUniqueName(opname):
        if opname not in AtlasOperator.name_uid_map:
            uid = 0
            AtlasOperator.name_uid_map[opname] = uid
        else:
            AtlasOperator.name_uid_map[opname] += 1
            uid = AtlasOperator.name_uid_map[opname]

        return f'{opname}_{uid}'

    def __init__(self, opname):
        self.name = AtlasOperator.GetUniqueName(opname)
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

