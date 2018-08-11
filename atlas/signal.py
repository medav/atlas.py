from . import model
from .base import *
from .typespec import *
from . import op
from .verilog import *

__all__ = [
    'BitsSignal',
    'ListSignal',
    'BundleSignal',
    'Input',
    'Output',
    'Flip',
    'Io',
    'Signal',
    'Wire',
    'Reg',
    'NameSignals'
]

def AssignBits(lbits, rbits):
    predicate = CurrentPredicate()
    block = lbits.connections

    for (signal, path) in predicate:
        if (len(block) > 0) and (type(block[-1]) is model.ConnectionBlock) and (block[-1].predicate is signal):
            block = block[-1].true_block if path else block[-1].false_block
        else:
            cb = model.ConnectionBlock(signal)
            block.append(cb)
            block = cb.true_block if path else cb.false_block

    block.append(rbits)

class BinaryOperator(op.AtlasOperator):
    def __init__(self, sig_a, sig_b, opname, verilog_op, r_width=0):
        assert sig_a.sigtype == model.SignalTypes.BITS
        assert sig_b.sigtype == model.SignalTypes.BITS
        assert sig_a.width == sig_b.width

        r_width = sig_a.width if r_width == 0 else r_width

        super().__init__(Signal(Bits(r_width, False)), opname)

        self.sig_a = sig_a
        self.sig_b = sig_b
        self.verilog_op = verilog_op

    def Declare(self):
        VDeclWire(self.result)

    def Synthesize(self):
        VAssignRaw(
            VName(self.result),
            f'{VName(self.sig_a)} {self.verilog_op} {VName(self.sig_b)}')

class NotOperator(op.AtlasOperator):
    def __init__(self, sig_a):
        assert sig_a.sigtype == model.SignalTypes.BITS
        super().__init__(Signal(Bits(sig_a.width, False)), 'not')
        self.sig_a = sig_a

    def Declare(self):
        VDeclWire(self.result)

    def Synthesize(self):
        VAssignRaw(VName(self.result), f'~{VName(self.sig_a)}')

class SliceOperator(op.AtlasOperator):
    def __init__(self, sig_a, high, low):
        assert high >= low
        super().__init__(Signal(Bits(high - low + 1, False)), 'slice')
        self.sig_a = sig_a
        self.high = high
        self.low = low

    def Declare(self):
        VDeclWire(self.result)

    def Synthesize(self):
        VAssignRaw(VName(self.result), f'{VName(self.sig_a)}[{self.high}:{self.low}]')

class BitsSignal(model.BitsSignal):
    def __init__(self, typespec, name=None, parent=None):
        if not IsBits(typespec):
            raise TypeError('Typespec is not Bits')

        super().__init__(
            name=name,
            typespec=typespec,
            parent=parent,
            width=typespec['width'],
            signed=typespec['signed'],
            flipped=typespec['flipped'])

    def __ilshift__(self, other):
        AssignBits(self, other)
        return self

    def __enter__(self):
        if self.width != 1:
            raise RuntimeError("Conditions must have bitwidth == 1")
        StartCondition(self)

    def __call__(self, high, low):
        return SliceOperator(self, high, low).result

    def __exit__(self, *kwargs):
        EndCondition()

    def __add__(self, other): return BinaryOperator(self, other, 'add', '+').result
    def __sub__(self, other): return BinaryOperator(self, other, 'sub', '-').result
    def __mul__(self, other): return BinaryOperator(self, other, 'mul', '*').result
    def __div__(self, other): return BinaryOperator(self, other, 'div', '/').result
    def __or__(self, other): return BinaryOperator(self, other, 'or', '|').result
    def __xor__(self, other): return BinaryOperator(self, other, 'xor', '^').result
    def __and__(self, other): return BinaryOperator(self, other, 'and', '&').result
    def __gt__(self, other): return BinaryOperator(self, other, 'gt', '>', 1).result
    def __lt__(self, other): return BinaryOperator(self, other, 'lt', '<', 1).result
    def __ge__(self, other): return BinaryOperator(self, other, 'ge', '>=', 1).result
    def __le__(self, other): return BinaryOperator(self, other, 'le', '<=', 1).result
    def __eq__(self, other): return BinaryOperator(self, other, 'eq', '==', 1).result
    def __neq__(self, other): return BinaryOperator(self, other, 'neq', '!=', 1).result
    def __invert__(self): return NotOperator(self).result

class ListSignal(model.ListSignal):
    def __init__(self, typespec, name=None, parent=None):
        if type(typespec) is not list:
            raise TypeError('Typespec is not List')

        fields = list([Signal(typespec[i], f'i{i}', self) for i in range(len(typespec))])

        super().__init__(
            name=name,
            typespec=typespec,
            parent=parent,
            fields=fields)

    def __ilshift__(self, other):
        assert isinstance(other, model.SignalBase)
        assert other.sigtype == model.SignalTypes.LIST
        assert len(other.fields) == len(self.fields)

        for i in range(len(self.fields)):
            self.fields[i] <<= other.fields[i]

    def __getitem__(self, key):
        return self.fields[key]

    def __setitem__(self, key, value):
        pass

class BundleSignal(model.BundleSignal):
    def __init__(self, typespec, name=None, parent=None):
        if type(typespec) is not dict:
            raise TypeError('Typespec is not Bundle')

        fields = { field:Signal(typespec[field], field, self) for field in typespec }

        super().__init__(
            name=name,
            typespec=typespec,
            parent=parent,
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
    signal.sigdir = model.SignalTypes.INPUT
    return signal

def Output(typespec):
    signal = Signal(typespec)
    signal.sigdir = model.SignalTypes.OUTPUT
    return signal

def Inout(typespec):
    signal = Signal(typespec)
    signal.sigdir = model.SignalTypes.INOUT
    return signal

def Flip(typespec):
    typespec['flipped'] = True
    return typespec

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
    if CurrentCircuit().config.default_clock:
        io_dict['clock'] = Input(Bits(1))

    if CurrentCircuit().config.default_reset:
        io_dict['reset'] = Input(Bits(1))

    io = IoBundle(io_dict)
    io.parent = CurrentModule()
    CurrentModule().io = io
    return io

def Wire(typespec):
    signal = Signal(typespec)
    CurrentModule().signals.append(signal)
    return signal

def Reg(typespec, clock=None, reset=None, reset_value=None):
    signal = Signal(typespec)

    if clock is not None:
        signal.clock = clock
    else:
        signal.clock = CurrentModule().io.clock

    if reset is not None:
        signal.reset = reset
    else:
        signal.reset = CurrentModule().io.reset

    signal.reset_value = reset_value
    CurrentModule().signals.append(signal)
    signal <<= signal
    return signal

def NameSignals(locals):
    for local in locals:
        if issubclass(type(locals[local]), model.SignalBase):
            locals[local].name = local