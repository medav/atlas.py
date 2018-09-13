from dataclasses import *

from ..base import *
from ..emitter import *

from .context import *

#
# The magic of the frontend comes from wrapping model signals with a class that
# provides Python magic functions to manipulate them easily. For example, the
# __ilshift__ magic function, which handles the "<<=" operator in Python, is
# overridden to be the universal "assignment" operator for signals.
#
# This module provides a basic set of "Operators" (as defined in base.op) that
# carry-out common tasks needed by these magic functions. This includes:
#
# * All two-operand (binary - not bitwise) operations
# * Bitwise Not (~)
# * Muxing a ListSignal
# * Left-hand / assignable indexing for ListSignals
#

class SignalFrontend(object):
    def __init__(self, signal):
        self.signal = signal

    def __ilshift__(self, other):
        """Primary assignment operator.

        N.B. The ilshift operator in python expects a return value to update the
        calling code's variable reference. Since this routine simply adds an
        assignment in this signal's connection list, this routine will return
        itself in all subclasses.
        """

        raise NotImplementedError()

    def __getattr__(self, key):
        return self.signal.__getattribute__(key)

    def ResetWith(self, reset, reset_value):
        raise NotImplementedError()

    def ClockWith(self, clock):
        raise NotImplementedError()

    def __setitem__(self, key, value):
        pass

    def __hash__(self):
        return hash(self.signal)

def FilterFrontend(value):
    """Takes an object and converts it to something that can be used in the
    base circuit model according to the following rules:

    * Base signals are extracted from frontend wrappers
    * rvalue is extracted from ListIndex's
    * Base signals are passed through
    * ints, lists, and dicts are passed through

    N.B. This should be called at any point where data is passed to base.* or
    emitter.* routines.
    """

    passthrough_types = {
        int, bool, list, dict,
        M.BitsSignal, M.ListSignal, M.BundleSignal
    }

    if issubclass(type(value), SignalFrontend):
        return value.signal

    if type(value) is ListIndex:
        return FilterFrontend(value.rvalue)

    if type(value) in passthrough_types:
        return value

    assert False, f'Object of type {type(value)} cannot be used in the model'

#
# Basic Operators used by frontend wrappers for signals.
#

class BinaryOperator(Operator):
    """A generic binary (two-operand) Operator.

    This class can be used to construct any two-operand operation in Verilog.
    It is used by the frontend wrapper code (below) to enable Python binary
    operations to produce Verilog operations.
    """

    def __init__(self, op0, op1, opname, verilog_op, r_width=0):
        op0 = FilterFrontend(op0)
        op1 = FilterFrontend(op1)
        assert type(op0) is M.BitsSignal
        assert (type(op1) is int) or (type(op1) is M.BitsSignal)
        super().__init__(opname)

        r_width = op0.width if r_width == 0 else r_width

        self.opname = opname
        self.op0 = op0
        self.op1 = op1
        self.verilog_op = verilog_op

        self.result = CreateSignal(Bits(r_width, False))
        self.result.signal.meta.parent = self
        self.result.signal.meta.name = 'result'

    def Declare(self):
        VDeclWire(FilterFrontend(self.result))

    def Synthesize(self):
        VAssignRaw(
            VName(FilterFrontend(self.result.signal)),
            f'{VName(self.op0)} {self.verilog_op} {VName(self.op1)}')

    def __eq__(self, other):
        return (type(self) is type(other)) and \
            (self.op0 is other.op0) and \
            (self.op1 is other.op1)

    def __hash__(self):
        return hash((self.opname, self.op0, self.op1))

@OpGen(cacheable=True, default='result')
def BinaryOp(op0, op1, opname, verilog_op, r_width=0):
    return BinaryOperator(op0, op1, opname, verilog_op, r_width)

class NotOperator(Operator):
    """Produces a new signal that is the bitwise NOT of its input."""

    def __init__(self, op0):
        op0 = FilterFrontend(op0)
        assert type(op0) is M.BitsSignal
        super().__init__('not')

        self.op0 = op0
        self.result = CreateSignal(Bits(op0.width, False))
        self.result.signal.meta.parent = self
        self.result.signal.meta.name = 'result'

    def Declare(self):
        VDeclWire(FilterFrontend(self.result))

    def Synthesize(self):
        VAssignRaw(VName(FilterFrontend(self.result)), f'~{VName(self.op0)}')

    def __eq__(self, other):
        return (type(self) is type(other)) and \
            (self.op0 is other.op0)

    def __hash__(self):
        return hash(('not', self.op0))

@OpGen(cacheable=True, default='result')
def Not(op0):
    return NotOperator(op0)

class SliceOperator(Operator):
    """Produces a new signal that is a bit slice of its input.

    N.B. This operator can only be applied to M.BitsSignals.
    """

    def __init__(self, op0, high : int, low : int):
        op0 = FilterFrontend(op0)
        assert high >= low
        assert type(op0) is M.BitsSignal
        super().__init__('slice')

        self.op0 = op0
        self.high = high
        self.low = low
        self.result = CreateSignal(Bits(high - low + 1, False))
        self.result.signal.meta.parent = self
        self.result.signal.meta.name = 'result'

    def Declare(self):
        VDeclWire(FilterFrontend(self.result))

    def Synthesize(self):
        VAssignRaw(
            VName(FilterFrontend(self.result)),
            f'{VName(self.op0)}[{self.high}:{self.low}]')

    def __eq__(self, other):
        return (type(self) is type(other)) and \
            (self.op0 is other.op0) and \
            (self.high == other.high) and \
            (self.low == other.low)

    def __hash__(self):
        return hash(('slice', self.op0, self.high, self.low))

@OpGen(cacheable=True, default='result')
def Slice(op0, high, low):
    return SliceOperator(op0, high, low)

class MuxOperator(Operator):
    """Multiplexor Operator.

    This Operator takes a list signal (of bits only) and an index signal and
    extracts the indicated signal from the list.
    """

    def __init__(self, list_signal, index_signal):
        self.list_signal = FilterFrontend(list_signal)
        self.index_signal = FilterFrontend(index_signal)

        assert type(self.list_signal) is M.ListSignal
        assert type(self.index_signal) is M.BitsSignal

        super().__init__('mux')

        self.r_width = list_signal[0].width
        self.l_length = len(list_signal)

        self.result = CreateSignal(Bits(self.r_width))
        self.result.signal.meta.parent = self
        self.result.signal.meta.name = 'result'

    def Declare(self):
        VDeclWire(FilterFrontend(self.result))

    def Synthesize(self):
        node_name = NewNodeName()
        VEmitRaw(
            f'wire [{self.r_width - 1} : 0] {node_name} [{self.l_length - 1} : 0];')

        for i in range(self.l_length):
            VAssignRaw(f'{node_name}[{i}]', VName(self.list_signal.fields[i]))

        VAssignRaw(
            VName(FilterFrontend(self.result)),
            f'{node_name}[{VName(self.index_signal)}]')

    def __eq__(self, other):
        return (type(self) is type(other)) and \
            (self.list_signal is other.list_signal) and \
            (self.index_signal is other.index_signal)

    def __hash__(self):
        return hash(('mux', self.list_signal, self.index_signal))

@OpGen(cacheable=True, default='result')
def Mux(list_signal, index_signal):
    return MuxOperator(list_signal, index_signal)

@dataclass
class ListIndex(object):
    """Class that enables both left-hand and right-hand indexing into a list.

    This is primarily a data-class that stores the list, and index that
    produces the resulting signal. This class also defines __ilshift__ to enable
    assignments to the signal.
    """

    list_signal : M.ListSignal
    index_signal : M.BitsSignal
    rvalue : any = field(init=False)

    def __post_init__(self):
        self.rvalue = MuxOperator(self.list_signal, self.index_signal).result

    def __ilshift__(self, value):
        for i in range(len(self.list_signal)):
            with self.index_signal == i:
                self.list_signal[i] <<= value

#
# The following classes wrap model signals with additional functionalities that
# enable DSL like features for adding connections, indexing, etc...
#

class BitsFrontend(SignalFrontend):
    """Wrapper class for a M.BitsSignal that adds frontend functionality."""

    def __init__(self, signal):
        assert type(signal) is M.BitsSignal
        super().__init__(signal)

    def __ilshift__(self, other):
        other = FilterFrontend(other)

        assert (type(other) is M.BitsSignal) or \
            (type(other) is int) or \
            (type(other) is bool)

        assert self.signal.meta.sigdir != M.SignalDir.INPUT, \
            'Cannot assign to an input signal'

        predicate = map(
            lambda item: (FilterFrontend(item[0]), item[1]),
            CurrentPredicate())

        assert GetDirection(self.signal) != M.SignalDir.INPUT

        InsertConnection(self.signal, predicate, other)
        return self

    def ResetWith(self, reset, reset_value):
        """Set the reset signal and value for this signal."""
        self.signal.reset = FilterFrontend(reset)
        self.signal.reset_value = FilterFrontend(reset_value)

    def ClockWith(self, clock):
        """Set the clock signal for this signal."""
        self.signal.clock = FilterFrontend(clock)

    def __enter__(self):
        assert self.signal.width == 1, 'Conditions must have bitwidth == 1'
        StartCondition(self)

    def __call__(self, high, low):
        return Slice(self, high, low)

    def __exit__(self, *kwargs):
        EndCondition()

    #
    # These magic functions are what enable frontend code to use Python's
    # operators to produce verilog operations. They essentially just produce
    # Operators that implement their corresponding operations in Verilog code.
    #

    def __add__(self, other): return BinaryOp(self, other, 'add', '+')
    def __sub__(self, other): return BinaryOp(self, other, 'sub', '-')
    def __mul__(self, other): return BinaryOp(self, other, 'mul', '*')
    def __div__(self, other): return BinaryOp(self, other, 'div', '/')
    def __or__(self, other): return BinaryOp(self, other, 'or', '|')
    def __xor__(self, other): return BinaryOp(self, other, 'xor', '^')
    def __and__(self, other): return BinaryOp(self, other, 'and', '&')
    def __radd__(self, other): return BinaryOp(self, other, 'add', '+')
    def __rsub__(self, other): return BinaryOp(self, other, 'sub', '-')
    def __rmul__(self, other): return BinaryOp(self, other, 'mul', '*')
    def __rdiv__(self, other): return BinaryOp(self, other, 'div', '/')
    def __ror__(self, other): return BinaryOp(self, other, 'or', '|')
    def __rxor__(self, other): return BinaryOp(self, other, 'xor', '^')
    def __rand__(self, other): return BinaryOp(self, other, 'and', '&')
    def __gt__(self, other): return BinaryOp(self, other, 'gt', '>', 1)
    def __lt__(self, other): return BinaryOp(self, other, 'lt', '<', 1)
    def __ge__(self, other): return BinaryOp(self, other, 'ge', '>=', 1)
    def __le__(self, other): return BinaryOp(self, other, 'le', '<=', 1)
    def __eq__(self, other): return BinaryOp(self, other, 'eq', '==', 1)
    def __ne__(self, other): return BinaryOp(self, other, 'neq', '!=', 1)
    def __lshift__(self, other): return BinaryOp(self, other, 'sll', '<<')
    def __rshift__(self, other): return BinaryOp(self, other, 'srl', '>>')
    def __invert__(self): return Not(self)

class ListFrontend(SignalFrontend):
    """Wrapper class for a M.ListSignal that adds frontend functionality."""

    def __init__(self, signal):
        assert type(signal) is M.ListSignal
        super().__init__(signal)
        self.wrap_fields = [
            WrapSignal(signal) for signal in self.signal.fields
        ]

    def __ilshift__(self, other):
        other = FilterFrontend(other)

        assert (type(other) is M.ListSignal) or (type(other) is list)

        if type(other) is M.ListSignal:
            assert len(self) == len(other.fields)
            for i in range(len(self)):
                if self.wrap_fields[i].meta.sigdir == M.SignalDir.FLIPPED:
                    other.fields[i] <<= self.wrap_fields[i]
                else:
                    self.wrap_fields[i] <<= other.fields[i]

        elif type(other) is list:
            assert len(self) == len(other)
            for i in range(len(self)):
                self.wrap_fields[i] <<= other[i]

        return self

    def ResetWith(self, reset, reset_value):
        """Set the reset signal and value for this signal's children."""
        assert type(reset_value) is list
        assert len(self.wrap_fields) == len(reset_value)
        for i in range(len(self.wrap_fields)):
            self.wrap_fields[i].ResetWith(reset, reset_value[i])

    def ClockWith(self, clock):
        """Set the clock signal for this signal's children"""
        for i in range(len(self.wrap_fields)):
            self.wrap_fields[i].ClockWith(clock)

    def __getitem__(self, key):
        if type(key) is int:
            return self.wrap_fields[key]
        else:
            return ListIndex(self, key)

    def __len__(self):
        return len(self.wrap_fields)

class BundleFrontend(SignalFrontend):
    def __init__(self, signal):
        assert type(signal) is M.BundleSignal
        super().__init__(signal)
        self.wrap_fields = {
            key:WrapSignal(self.signal.fields[key]) for key in self.signal.fields
        }

    def __ilshift__(self, other):
        other = FilterFrontend(other)

        assert (type(other) is M.BundleSignal) or (type(other) is dict)

        if type(other) is M.BundleSignal:
            assert self.signal.fields.keys() >= other.fields.keys()
            for key in other.fields:
                if self.wrap_fields[key].meta.sigdir == M.SignalDir.FLIPPED:
                    other.fields[key] <<= self.wrap_fields[key]
                else:
                    self.wrap_fields[key] <<= other.fields[key]

        elif type(other) is dict:
            assert self.signal.fields.keys() >= other.keys()
            for key in other:
                self.wrap_fields[key] <<= other[key]

        return self

    def ResetWith(self, reset, reset_value):
        """Set the reset signal and value for this signal's children."""

        assert type(reset_value) is dict
        assert set(reset_value.keys()) == set(self.wrap_fields.keys())

        for key in self.wrap_fields:
            self.wrap_fields[key].ResetWith(reset, reset_value[key])

    def ClockWith(self, clock):
        """Set the clock signal for this signal's children"""

        for key in self.wrap_fields:
            self.wrap_fields[key].ClockWith(clock)

    def __getattr__(self, key):
        return self.wrap_fields[key]

class IoFrontend():
    def __init__(self, io_dict):
        self.io_dict = {
            key:WrapSignal(io_dict[key])
            for key in io_dict
        }

    def __getattr__(self, key):
        return self.io_dict[key]

#
# Common routines to produce signals and wrap them with frontend classes.
#

def WrapSignal(signal):
    """Wrap a model signal with a corresponding frontend wrapper."""

    if type(signal) is M.BitsSignal:
        return BitsFrontend(signal)
    elif type(signal) is M.ListSignal:
        return ListFrontend(signal)
    elif type(signal) is M.BundleSignal:
        return BundleFrontend(signal)
    else:
        assert False, f'Cannot wrap signal of type {type(signal)}'

def CreateSignal(primitive_spec, name=None, parent=None, frontend=True):
    """Produce a signal given a primitive_spec.

    This is an entrypoint that is called by the signal init functions to
    recursively produce sub-signals.
    """

    typespec = BuildTypespec(primitive_spec)

    if type(typespec) is Bits:
        signal = M.BitsSignal(
            meta=M.SignalMeta(
                name=name,
                parent=parent,
                sigdir=typespec.meta.sigdir
            ),
            width=typespec.width,
            signed=typespec.signed
        )

    elif type(typespec) is List:
        signal = M.ListSignal(
            M.SignalMeta(
                name=name,
                parent=parent,
                sigdir=typespec.meta.sigdir
            ),
            fields = list([
                CreateSignal(typespec.field_type, f'i{i}', None, False)
                for i in range(typespec.length)
            ])
        )

        for item in signal.fields:
            item.meta.parent = signal

    elif type(typespec) is Bundle:
        signal = M.BundleSignal(
            M.SignalMeta(
                name=name,
                parent=parent,
                sigdir=typespec.meta.sigdir
            ),
            fields = {
                field:CreateSignal(typespec.fields[field], field, None, False)
                for field in typespec.fields
            }
        )

        for key in signal.fields:
            signal.fields[key].meta.parent = signal

    else:
        assert False, f'Unknown typespec: {typespec}'

    if frontend:
        return WrapSignal(signal)
    else:
        return signal