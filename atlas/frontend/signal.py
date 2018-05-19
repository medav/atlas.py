from .. import model
from .module import *

def LookupParentModule(signal):
    while signal.parent is not None and type(signal.parent) != Module:
        signal = signal.parent

    assert signal.parent is not None

    return signal.parent

class Bits(model.Bits):
    def __init__(self, _width, _name='bits', _signed=False):
        model.Bits.__init__(self, _name, _width, _signed)

    def Assign(self, other, child=None):
        assert self.parent is not None
        self.parent.Assign(other, self if child is None else child)

    def __enter__(self):
        pass

    def __exit__(self, *kwargs):
        pass

class Bundle(model.Bundle):
    def __init__(self, _name, _dict):
        model.Bundle.__init__(self, _name, _dict)

    def Assign(self, other, child=None):
        assert self.parent is not None
        self.parent.Assign(other, self if child is None else child)

def Signed(signal):
    signal.signed = True
    return

def Unsigned(signal):
    signal.signed = False
    return

def Flip(signal):
    signal.sigdir = model.Signal.FLIPPED
    return signal

def Input(signal):
    signal.sigdir = model.Signal.INPUT
    return signal

def Output(signal):
    signal.sigdir = model.Signal.OUTPUT
    return signal

def Io(_dict):
    return Bundle('io', _dict)