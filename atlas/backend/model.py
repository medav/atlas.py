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

    def Regex():
        raise NotImplementedError()

    def __str__(self):
        return self.name

class Expr(object):
    def __init__(self):
        pass

class Node(object):
    def __init__(self, _name, _expr, _info):
        self.name = _name
        self.expr = _expr
        self.info = _info

    def FromString(line):
        regex = re.compile('node ([a-zA-Z_0-9]+)\\W*=\\W*(.*)(@\\[.*\\])?')
        m = regex.match(line.strip())
        name = m.groups('')[0].strip()
        expr = m.groups('')[1].strip()
        info = m.groups('')[2].strip()
        return Node(name, expr, info)

class Condition(Expr):
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

class PrimOp(Expr):
    def __init__(self, _opname, _args):
        self.opname = _opname
        self.args = _args

class Assignment(Expr):
    def __init__(self, _lhs, _rhs):
        self.lhs = _lhs
        self.rhs = _rhs