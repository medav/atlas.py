import re
from .signals import *

class Circuit(object):
    def __init__(self, _name):
        self.name = _name
        self.modules = []

    def AddModule(self, module):
        self.modules.append(module)

    def Regex():
        raise NotImplementedError()

    def __str__(self):
        return 'circuit {}'.format(self.name)

class Module(object):
    def __init__(self, _name):
        self.name = _name
        self.io = {}
        self.regs = {}
        self.wires = {}
        self.nodes = {}
        self.insts = {}
        self.exprs = []

    def AddIo(self, signal):
        self.io[signal.name] = signal

    def AddReg(self, reg):
        self.regs[reg.name] = reg

    def AddWire(self, wire):
        self.wires[wire.name] = wire

    def AddSignal(self, signal):
        if signal.sigtype == 'input':
            self.AddIo(Input(signal))
        elif signal.sigtype == 'output':
            self.AddIo(Output(signal))
        elif signal.sigtype == 'wire':
            self.AddWire(signal)
        elif signal.sigtype == 'reg':
            self.AddReg(signal)
        else:
            raise NotImplementedError()

    def AddNode(self, node):
        self.nodes[node.name] = node

    def AddInst(self, inst):
        self.insts[inst.name] = inst

    def AddExpr(self, expr):
        self.exprs.append(expr)

    def AddConnect(self, lhs, rhs):
        pass

    def Regex():
        raise NotImplementedError()

    def __str__(self):
        return self.name

class Assignment():
    def __init__(self, _lhs, _rhs):
        self.lhs = _lhs
        self.rhs = _rhs

class Condition():
    def __init__(self, _condition_str):
        self.condition_str = _condition_str
        self.exprs = []
        self.wires = {}
        self.nodes = {}

    def AddExpr(self, expr):
        self.exprs.append(expr)

    def AddWire(self, wire):
        self.wires[wire.name] = wire

    def AddSignal(self, signal):
        if signal.sigtype == 'wire':
            self.AddWire(signal)
        else:
            raise NotImplementedError()

    def AddNode(self, node):
        self.nodes[node.name] = node

    def __str__(self):
        return 'when'


class Node(object):
    def __init__(self, _name, _expr, _info):
        self.name = _name
        self.expr = _expr
        self.info = _info

    def __enter__(self):
        pass

    def __exit__(self, *kwargs):
        pass

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
