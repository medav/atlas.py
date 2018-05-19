import re

class Node(object):
    def __init__(self, _name, _primop, _args):
        self.name = _name
        self.primop = primop
        self.args = _args

class Signal():

    # Signal directions
    INPUT = 0
    OUTPUT = 1
    FLIPPED = 2

    # Signal types
    WIRE = 0
    REG = 1

    def __init__(self, _name):
        self.sigdir = Signal.INPUT
        self.sigtype = Signal.WIRE
        self.name = _name
        self.parent = None

class Bits(Signal):
    def __init__(self, _name, _width, _signed=False):
        Signal.__init__(self, _name)
        self.width = _width
        self.signed = _signed
        self.parent = None

class Bundle(Signal):
    def __init__(self, _name, _dict):
        Signal.__init__(self, _name)
        self.signal_names = []

        for name in _dict:
            self.signal_names.append(name)
            _dict[name].name = name
            _dict[name].parent = self

        self.__dict__.update(_dict)

    def __iter__(self):
        self.index = 0
        return self

    def __next__(self):
        if self.index >= len(self.signal_names):
            raise StopIteration

        signal = self.__dict__[self.signal_names[self.index]]
        self.index += 1

        return signal

    def __getitem__(self, key):
        return self.__dict__[key]

class Assignment():
    def __init__(self, _lhs, _rhs):
        self.lhs = _lhs
        self.rhs = _rhs

class StatementGroup():
    def __init__(self):
        self.stmts = []
        self.signals = {}
        self.nodes = {}

    def AddSignal(self, signal):
        self.signals[signal.name] = signal
        self.AddStmt(signal)

    def AddNode(self, node):
        self.nodes[node.name] = node
        self.AddStmt(node)

    def AddStmt(self, stmt):
        self.stmts.append(stmt)

class Condition(StatementGroup):
    def __init__(self, _condition_signal):
        StatementGroup.__init__(self)
        self.condition_signal = _condition_signal

class Module(StatementGroup):
    def __init__(self, _name):
        StatementGroup.__init__(self)
        self.name = _name
        self.io = {}
        self.signals = {}
        self.nodes = {}
        self.insts = {}
        self.stmts = []

    def AddIo(self, signal):
        self.io[signal.name] = signal

    def AddInst(self, inst):
        self.insts[inst.name] = inst

class Circuit(object):
    def __init__(self, _name):
        self.name = _name
        self.modules = []

    def AddModule(self, module):
        self.modules.append(module)