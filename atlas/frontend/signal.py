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
    'Io'
]

class Node(model.Node):
    def __init__(self, _name, _primop, _args):
        model.Node.__init__(self, _name, _primop, _args)

    def __enter__(self):
        self.condition = StartCondition(self)

    def __exit__(self, *kwargs):
        EndCondition(self.condition)

class Bits(model.Bits):
    def __init__(self, _width, _name='bits', _length=1, _signed=False):
        model.Bits.__init__(self, _width, _name, _length, _signed)

    def Assign(self, other):
        CurrentContext().AddStmt(model.Assignment(self, other))

    def __enter__(self):
        self.condition = StartCondition(self)

    def __exit__(self, *kwargs):
        EndCondition(self.condition)

class Bundle(model.Bundle):
    def __init__(self, _dict, _name='bundle'):
        model.Bundle.__init__(self, _dict, _name=_name)

    def Assign(self, other):
        CurrentContext().AddStmt(model.Assignment(self, other))

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

def Reg(signal):
    signal.sigtype = model.Signal.REG
    CurrentContext().AddSignal(signal)

def Assign(signal, child):
    CurrentContext().AddStmt(model.Assignment(child, signal))