from .. import model
from .base import *

__all__ = [
    'Node',
    'Bits',
    'Bundle',
    'Signed',
    'Unsigned',
    'Flip',
    'Input',
    'Output',
    'Const',
    'Io',
    'Wire',
    'WireInit',
    'Reg',
    'RegInit',
    'NameSignals'
]

def UnaryOp(op, a):
    n = Node(op, [a])
    CurrentContext().AddNode(n)
    return n

def BinaryOp(op, a, b):
    n = Node(op, [a, b])
    CurrentContext().AddNode(n)
    return n

def ConvertLiterals(args):
    return args
    # for i in range(len(args)):
    #     if type(args[i]) is int:
            

class Node(model.Node):
    uid = 0

    def __init__(self, _primop, _args):
        model.Node.__init__(self, f'node_{Node.uid}', _primop, ConvertLiterals(_args))
        Node.uid += 1

    def __enter__(self):
        self.condition = StartCondition(self)

    def __exit__(self, *kwargs):
        EndCondition(self.condition)

    def __add__(self, other): return BinaryOp('add', self, other)
    def __sub__(self, other): return BinaryOp('sub', self, other)
    def __mul__(self, other): return BinaryOp('mul', self, other)
    def __div__(self, other): return BinaryOp('div', self, other)
    def __or__(self, other): return BinaryOp('or', self, other)
    def __xor__(self, other): return BinaryOp('xor', self, other)
    def __and__(self, other): return BinaryOp('and', self, other)
    def __gt__(self, other): return BinaryOp('gt', self, other)
    def __lt__(self, other): return BinaryOp('lt', self, other)
    def __ge__(self, other): return BinaryOp('ge', self, other)
    def __le__(self, other): return BinaryOp('le', self, other)
    def __eq__(self, other): return BinaryOp('eq', self, other)
    def __neq__(self, other): return BinaryOp('neq', self, other)
    def __invert__(self): return UnaryOp('not', self)

class Bits(model.Bits):
    def __init__(self, _elemwidth, _shape=(1,), _name='bits', _signed=False):
        model.Bits.__init__(self, _elemwidth, _shape, _name, _signed)

    def Assign(self, other):
        CurrentContext().AddStmt(model.Assignment(self, other))

    def __ilshift__(self, other):
        self.Assign(other)
        return self

    def __enter__(self):
        self.condition = StartCondition(self)

    def __exit__(self, *kwargs):
        EndCondition(self.condition)

    def __call__(self, high, low):
        n = Node('bits', [self, high, low])
        CurrentContext().AddNode(n)
        return n

    def __getitem__(self, key):
        return BitsElement(self, key)

    def __setitem__(self, key, value):
        pass

    def __add__(self, other): return BinaryOp('add', self, other)
    def __sub__(self, other): return BinaryOp('sub', self, other)
    def __mul__(self, other): return BinaryOp('mul', self, other)
    def __div__(self, other): return BinaryOp('div', self, other)
    def __or__(self, other): return BinaryOp('or', self, other)
    def __xor__(self, other): return BinaryOp('xor', self, other)
    def __and__(self, other): return BinaryOp('and', self, other)
    def __gt__(self, other): return BinaryOp('gt', self, other)
    def __lt__(self, other): return BinaryOp('lt', self, other)
    def __ge__(self, other): return BinaryOp('ge', self, other)
    def __le__(self, other): return BinaryOp('le', self, other)
    def __eq__(self, other): return BinaryOp('eq', self, other)
    def __neq__(self, other): return BinaryOp('neq', self, other)
    def __invert__(self): return UnaryOp('not', self)

class BitsElement(model.BitsElement):
    def __init__(self, _parent, _key):
        model.BitsElement.__init__(self, _parent, _key)

    def Assign(self, other):
        CurrentContext().AddStmt(model.Assignment(self, other))

    def __ilshift__(self, other):
        self.Assign(other)
        return self

    def __add__(self, other): return BinaryOp('add', self, other)
    def __sub__(self, other): return BinaryOp('sub', self, other)
    def __mul__(self, other): return BinaryOp('mul', self, other)
    def __div__(self, other): return BinaryOp('div', self, other)
    def __or__(self, other): return BinaryOp('or', self, other)
    def __xor__(self, other): return BinaryOp('xor', self, other)
    def __and__(self, other): return BinaryOp('and', self, other)
    def __gt__(self, other): return BinaryOp('gt', self, other)
    def __lt__(self, other): return BinaryOp('lt', self, other)
    def __ge__(self, other): return BinaryOp('ge', self, other)
    def __le__(self, other): return BinaryOp('le', self, other)
    def __eq__(self, other): return BinaryOp('eq', self, other)
    def __neq__(self, other): return BinaryOp('neq', self, other)
    def __invert__(self): return UnaryOp('not', self)

class Bundle(model.Bundle):
    def __init__(self, _dict, _name='bundle'):
        model.Bundle.__init__(self, _dict, _name=_name)

    def Assign(self, other):
        CurrentContext().AddStmt(model.Assignment(self, other))

    def __ilshift__(self, other):
        self.Assign(other)
        return self

def Const(value, bitwidth=0, signed=False):
    return model.Constant(value, bitwidth, signed)

def Signed(signal):
    signal.signed = True
    return signal

def Unsigned(signal):
    signal.signed = False
    return signal

def Flip(signal):
    signal.sigdir = model.Signal.FLIP
    return signal

def Input(signal):
    signal.sigdir = model.Signal.INPUT
    return signal

def Output(signal):
    signal.sigdir = model.Signal.OUTPUT
    return signal

def Io(_dict):
    io = Bundle(_dict, _name='io')

    for s in io:
        if s.sigdir == model.Signal.INPUT:
            Flip(s)

    CurrentModule().io = io
    io.parent = CurrentModule()
    return io

def Wire(signal):
    signal.sigtype = model.Signal.WIRE
    CurrentContext().AddSignal(signal)
    return signal

def WireInit(signal, default):
    wire = Wire(signal)
    wire <<= default
    return wire

def Reg(signal):
    signal.sigtype = model.Signal.REG
    CurrentModule().has_state = True
    CurrentContext().AddSignal(signal)
    return signal

def RegInit(signal, reset):
    reg = Reg(signal)
    reg.reset = reset
    return reg

def Assign(signal, child):
    CurrentContext().AddStmt(model.Assignment(child, signal))

def NameSignals(locals):
    for local in locals:
        if issubclass(type(locals[local]), model.Signal):
            locals[local].name = local