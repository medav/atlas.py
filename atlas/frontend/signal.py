from .. import model
from .module import *

def LookupParentModule(signal):
    while signal.parent is not None and not issubclass(type(signal.parent), Module):
        signal = signal.parent

    return signal.parent

class Node(model.Node):
    def __init__(self, _name, _primop, _args):
        model.Node.__init__(self, _name, _primop, _args)

    def __enter__(self):
        assert self.parent is not None
        assert issubclass(type(self.parent), Module)
        self.parent.StartCondition(self)

    def __exit__(self, *kwargs):
        assert self.parent is not None
        assert issubclass(type(self.parent), Module)
        self.parent.EndCondition

class Bits(model.Bits):
    def __init__(self, _width, _name='bits', _length=1, _signed=False):
        model.Bits.__init__(self, _width, _name, _length, _signed)

    def Assign(self, other, child=None):
        assert self.parent is not None
        self.parent.Assign(other, self if child is None else child)

    def __enter__(self):
        self.module = LookupParentModule(self)
        assert self.module is not None
        self.module.StartCondition(self)

    def __exit__(self, *kwargs):
        assert self.module is not None
        self.module.EndCondition

class Bundle(model.Bundle):
    def __init__(self, _dict, _name='bundle'):
        model.Bundle.__init__(self, _dict, _name=_name)

    def Assign(self, other, child=None):
        assert self.parent is not None
        self.parent.Assign(other, self if child is None else child)

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

    return io