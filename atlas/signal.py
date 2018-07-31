from . import model
from .base import *
from .typespec import *

__all__ = [
    'BitsSignal',
    'ListSignal',
    'BundleSignal',
    'Input',
    'Output',
    'Io',
    'Wire',
    'Reg'
]

class BitsSignal(model.BitsSignal):
    def __init__(self, typespec, name=None, parent=None, sigstate=model.SignalTypes.WIRE):
        if not IsBits(typespec):
            raise TypeError('Typespec is not Bits')

        super().__init__(
            name=name,
            typespec=typespec,
            parent=parent,
            sigstate=sigstate,
            width=typespec['width'],
            signed=typespec['signed'],
            flipped=typespec['flipped'])

    def Assign(self, other):
        self.connections.append(model.Connection(CurrentPredicate(), other))

    def __ilshift__(self, other):
        self.Assign(other)
        return self

    def __enter__(self):
        if self.width != 1:
            raise RuntimeError("Conditions must have bitwidth == 1")
        StartCondition(self)

    def __exit__(self, *kwargs):
        EndCondition(self)

    def __add__(self, other): return Add(self, other)
    def __sub__(self, other): return Sub(self, other)
    def __mul__(self, other): return Mul(self, other)
    def __div__(self, other): return Div(self, other)
    def __or__(self, other): return Or(self, other)
    def __xor__(self, other): return Xor(self, other)
    def __and__(self, other): return And(self, other)
    def __gt__(self, other): return Gt(self, other)
    def __lt__(self, other): return Lt(self, other)
    def __ge__(self, other): return Ge(self, other)
    def __le__(self, other): return Le(self, other)
    def __eq__(self, other): return Eq(self, other)
    def __neq__(self, other): return Neq(self, other)
    def __invert__(self): return Not(self)

class ListSignal(model.ListSignal):
    def __init__(self, typespec, name=None, parent=None, sigstate=model.SignalTypes.WIRE):
        if type(typespec) is not list:
            raise TypeError('Typespec is not List')

        fields = list([Signal(typespec[i], f'i{i}', self) for i in range(len(typespec))])

        super().__init__(
            name=name,
            typespec=typespec,
            parent=parent,
            sigstate=sigstate,
            fields=fields)

    def __getitem__(self, key):
        return self.fields[key]

class BundleSignal(model.BundleSignal):
    def __init__(self, typespec, name=None, parent=None, sigstate=model.SignalTypes.WIRE):
        if type(typespec) is not dict:
            raise TypeError('Typespec is not Bundle')

        fields = { field:Signal(typespec[field], field, self) for field in typespec }

        super().__init__(
            name=name,
            typespec=typespec,
            parent=parent,
            sigstate=sigstate,
            fields=fields)

    def Assign(self, other):
        assert False

    def __getattr__(self, key):
        return self.fields[key]

    def __ilshift__(self, other):
        self.Assign(other)
        return self

def Signal(typespec, name=None, parent=None):
    if IsBits(typespec):
        return BitsSignal(typespec, name, parent)
    elif type(typespec) is list:
        return ListSignal(typespec, name, parent)
    elif type(typespec) is dict:
        return BundleSignal(typespec, name, parent)
    else:
        assert False

def Input(typespec):
    signal = Signal(typespec)
    signal.sigdir = model.SignalTypes.OUTPUT
    return signal

def Output(typespec):
    signal = Signal(typespec)
    signal.sigdir = model.SignalTypes.INPUT
    return signal

def Inout(typespec):
    signal = Signal(typespec)
    signal.sigdir = model.SignalTypes.INOUT
    return signal

class IoBundle(model.IoBundle):
    def __init__(self, io_dict):
        super().__init__(io_dict=io_dict)

        for key in self.io_dict:
            signal = io_dict[key]
            signal.parent = self
            signal.name = key

    def __getattr__(self, key):
        return self.io_dict[key]

def Io(io_dict):
    io = IoBundle(io_dict)
    io.parent = CurrentModule()
    CurrentModule().io = io
    return io

def Wire(typespec):
    signal = Signal(typespec)
    signal.sigstate = SignalTypes.WIRE
    return signal

def Reg(typespec):
    signal = Signal(typespec)
    signal.sigstate = SignalTypes.REG
    return signal


# def NameSignals(locals):
#     for local in locals:
#         if issubclass(type(locals[local]), model.Signal):
#             locals[local].name = local