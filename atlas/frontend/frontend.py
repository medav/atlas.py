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

    @staticmethod
    def GetConnection(other, this_type, const_type):
        other = FilterFrontend(other)

        #
        # Now check assignment compatibility
        #

        assert (type(other) is this_type) or (type(other) is const_type), \
            f'Cannot assign object of type {type(other)} to signal of type {this_type}'

        return other

    def ResetWith(self, reset, reset_value):
        raise NotImplementedError()

    def ClockWith(self, clock):
        raise NotImplementedError()

    def __setitem__(self, key, value):
        pass

    def __hash__(self):
        return hash(self.signal.meta)

def FilterFrontend(value):
    """Takes an object and converts it to something that can be used in the
    base circuit model according to the following rules:

    * Base signals are extracted from frontend wrappers
    * rvalue is extracted from ListIndex's
    * bools are converted to 1/0
    * Base signals are passed through
    * ints, lists, and dicts are passed through

    N.B. This should be called at any point where data is passed to base.* or
    emitter.* routines.
    """

    passthrough_types = {
        int, list, dict,
        M.BitsSignal, M.ListSignal, M.BundleSignal
    }

    if issubclass(type(value), SignalFrontend):
        return value.signal

    if type(value) is ListIndex:
        return FilterFrontend(value.rvalue)

    if type(value) is bool:
        return 1 if value else 0

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
# enable DSL list features for adding connections, indexing, etc...
#

class BitsFrontend(SignalFrontend):
    """Wrapper class for a M.BitsSignal that adds frontend functionality."""

    def __init__(self, signal):
        assert type(signal) is M.BitsSignal
        super().__init__(signal)

    def __ilshift__(self, other):
        other = SignalFrontend.GetConnection(other, M.BitsSignal, int)

        assert self.signal.meta.sigdir != M.SignalTypes.INPUT, \
            'Cannot assign to an input signals'

        predicate = map(
            lambda item: (FilterFrontend(item[0]), item[1]),
            CurrentPredicate())

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
        return SliceOperator(self, high, low).result

    def __exit__(self, *kwargs):
        EndCondition()

    #
    # These magic functions are what enable frontend code to use Python's
    # operators to produce verilog operations. They essentially just produce
    # Operators that implement their corresponding operations in Verilog code.
    #

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
    def __ne__(self, other): return BinaryOperator(self, other, 'neq', '!=', 1).result
    def __lshift__(self, other): return BinaryOperator(self, other, 'sll', '<<').result
    def __rshift__(self, other): return BinaryOperator(self, other, 'srl', '>>').result
    def __invert__(self): return NotOperator(self).result

class ListFrontend(SignalFrontend):
    """Wrapper class for a M.ListSignal that adds frontend functionality."""

    def __init__(self, signal):
        assert type(signal) is M.ListSignal
        super().__init__(signal)
        self.wrap_fields = [
            WrapSignal(signal) for signal in self.signal.fields
        ]

    def __ilshift__(self, other):
        other = SignalFrontend.GetConnection(other, M.ListSignal, list)

        if type(other) is M.ListSignal:
            assert len(self) == len(other.fields)
            for i in range(len(self)):
                self.wrap_fields[i] <<= other.fields[i]

        elif type(other) is list:
            assert len(self) == len(other)
            for i in range(len(self)):
                self.wrap_fields[i] <<= other[i]

        else:
            assert False

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
        other = SignalFrontend.GetConnection(other, M.BundleSignal, dict)

        if type(other) is M.BundleSignal:
            assert self.signal.fields.keys() >= other.fields.keys()
            for key in other.fields:
                self.wrap_fields[key] <<= other.fields[key]

        elif type(other) is dict:
            assert self.signal.fields.keys() >= other.keys()
            for key in other:
                self.wrap_fields[key] <<= other[key]

        else:
            assert False

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

def CreateSignal(typespec, name=None, parent=None, frontend=True):
    """Produce a signal given a typespec.

    This is an entrypoint that is called by the signal init functions to
    recursively produce sub-signals.
    """

    if IsBits(typespec):
        signal = M.BitsSignal(
            meta=M.SignalMeta(
                name=name,
                parent=parent
            ),
            width=typespec['width'],
            signed=typespec['signed'],
            flipped=typespec['flipped']
        )

    elif type(typespec) is list:
        signal = M.ListSignal(
            M.SignalMeta(
                name=name,
                parent=parent
            ),
            fields = list([
                CreateSignal(typespec[i], f'i{i}', None, False)
                for i in range(len(typespec))
            ])
        )

        for item in signal.fields:
            item.meta.parent = signal

    elif type(typespec) is dict:
        signal = M.BundleSignal(
            M.SignalMeta(
                name=name,
                parent=parent
            ),
            fields = {
                field:CreateSignal(typespec[field], field, None, False)
                for field in typespec
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