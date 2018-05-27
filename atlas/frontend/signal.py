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
    'Io',
    'Wire',
    'Reg',
    'NameSignals',
    'Cat'
]

class Node(model.Node):
    uid = 0

    def __init__(self, _primop, _args):
        model.Node.__init__(self, f'node_{Node.uid}', _primop, _args)
        Node.uid += 1

    def __enter__(self):
        self.condition = StartCondition(self)

    def __exit__(self, *kwargs):
        EndCondition(self.condition)

    def __or__(self, other):
        n = Node('or', [self, other])
        CurrentContext().AddNode(n)
        return n

    def __xor__(self, other):
        n = Node('xor', [self, other])
        CurrentContext().AddNode(n)
        return n

    def __and__(self, other):
        n = Node('and', [self, other])
        CurrentContext().AddNode(n)
        return n

class Bits(model.Bits):
    def __init__(self, _elemwidth, _shape=(1,), _name='bits', _signed=False):
        model.Bits.__init__(self, _elemwidth, _shape, _name, _signed)

    def Assign(self, other):
        CurrentContext().AddStmt(model.Assignment(self, other))

    def __le__(self, other):
        self.Assign(other)

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

class BitsElement(model.BitsElement):
    def __init__(self, _parent, _key):
        model.BitsElement.__init__(self, _parent, _key)

    def Assign(self, other):
        CurrentContext().AddStmt(model.Assignment(self, other))

    def __le__(self, other):
        self.Assign(other)

    def __or__(self, other):
        n = Node('or', [self, other])
        CurrentContext().AddNode(n)
        return n

    def __xor__(self, other):
        n = Node('xor', [self, other])
        CurrentContext().AddNode(n)
        return n

    def __and__(self, other):
        n = Node('and', [self, other])
        CurrentContext().AddNode(n)
        return n

class Bundle(model.Bundle):
    def __init__(self, _dict, _name='bundle'):
        model.Bundle.__init__(self, _dict, _name=_name)

    def Assign(self, other):
        CurrentContext().AddStmt(model.Assignment(self, other))

    def __le__(self, other):
        self.Assign(other)

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

def Reg(signal):
    signal.sigtype = model.Signal.REG
    CurrentContext().AddSignal(signal)
    return signal

def Cat(signals):
    if len(signals) == 1:
        return signals[0]

    elif len(signals) == 2:
        n = Node('cat', signals)
        CurrentContext().AddNode(n)
        return n

    else:
        half = int(len(signals) / 2)
        n1 = Cat(signals[:half])
        n2 = Cat(signals[half:])
        return Cat([n1, n2])


def Assign(signal, child):
    CurrentContext().AddStmt(model.Assignment(child, signal))

def NameSignals(locals):
    for local in locals:
        if issubclass(type(locals[local]), model.Signal):
            locals[local].name = local