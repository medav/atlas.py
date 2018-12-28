from . import model as M
from .debug import *
from .utilities import *

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

    def __init__(self, opname=None, override_name=None):
        global _RegisterOp
        if override_name is not None:
            self.name = override_name
        else:
            self.name = Operator.GetUniqueName(opname)
        self.signals = {}

    def Declare(self):
        raise NotImplementedError()

    def Synthesize(self):
        raise NotImplementedError()

    def __eq__(self, other):
        raise NotImplementedError()

    def __hash__(self):
        return hash(self.name)
