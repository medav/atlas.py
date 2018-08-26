from . import model as M
from .debug import *
from .utilities import *

_RegisterOp = lambda op: None

def HookRegisterOp(func):
    global _RegisterOp
    _RegisterOp = func

class Operator(object):
    name_uid_map = {}

    @staticmethod
    def GetUniqueName(opname):
        if opname not in Operator.name_uid_map:
            uid = 0
            Operator.name_uid_map[opname] = uid
        else:
            Operator.name_uid_map[opname] += 1
            uid = Operator.name_uid_map[opname]

        return f'{opname}_{uid}'

    def __init__(self, opname):
        global _RegisterOp
        self.name = Operator.GetUniqueName(opname)
        self.signals = {}
        _RegisterOp(self)

    def Declare(self):
        raise NotImplementedError()

    def Synthesize(self):
        raise NotImplementedError()

