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
        other = FilterRvalue(other)

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

def FilterRvalue(rvalue):
    """Takes an item used on the right hand side of a connection or as an
    operand to a Operator and converts it to something that can be used on the
    right side of a connection. This means the following:

    * Base signals are extracted from frontend wrappers
    * rvalue is extracted from ListIndex's
    * bools are converted to 1/0
    * Base signals are passed through
    * ints, lists, and dicts are passed through
    """

    passthrough_types = {
        int, list, dict,
        M.BitsSignal, M.ListSignal, M.BundleSignal
    }

    if issubclass(type(rvalue), SignalFrontend):
        return rvalue.signal

    if type(rvalue) is ListIndex:
        return FilterRvalue(rvalue.rvalue)

    if type(rvalue) is bool:
        return 1 if rvalue else 0

    if type(rvalue) in passthrough_types:
        return rvalue

    assert False, f'Object of type {type(rvalue)} cannot be used as an r-value'

#
# Basic Operators used by frontend wrappers for signals.
#

class BinaryOperator(Operator):
    def __init__(self, op0, op1, opname, verilog_op, r_width=0):
        op0 = FilterRvalue(op0)
        op1 = FilterRvalue(op1)

        assert type(op0) is M.BitsSignal
        assert (type(op1) is int) or (type(op1) is M.BitsSignal)

        r_width = op0.width if r_width == 0 else r_width

        super().__init__(opname)

        self.op0 = op0
        self.op1 = op1
        self.verilog_op = verilog_op

        self.result = CreateSignal(Bits(r_width, False))
        self.result.signal.meta.parent = self
        self.result.signal.meta.name = 'result'

    def Declare(self):
        VDeclWire(self.result.signal)

    def Synthesize(self):
        VAssignRaw(
            VName(self.result.signal),
            f'{VName(self.op0)} {self.verilog_op} {VName(self.op1)}')

class NotOperator(Operator):
    """Produces a new signal that is the bitwise NOT of its input."""

    def __init__(self, op0):
        op0 = FilterRvalue(op0)

        assert type(op0) is M.BitsSignal

        super().__init__('not')

        self.op0 = op0
        self.result = CreateSignal(Bits(op0.width, False))
        self.result.signal.meta.parent = self
        self.result.signal.meta.name = 'result'

    def Declare(self):
        VDeclWire(self.result.signal)

    def Synthesize(self):
        VAssignRaw(VName(self.result.signal), f'~{VName(self.op0)}')

class SliceOperator(Operator):
    """Produces a new signal that is a bit slice of its input.

    N.B. This operator can only apply to M.BitsSignals.
    """

    def __init__(self, op0, high : int, low : int):
        op0 = FilterRvalue(op0)

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
        VDeclWire(self.result.signal)

    def Synthesize(self):
        VAssignRaw(
            VName(self.result.signal),
            f'{VName(self.op0)}[{self.high}:{self.low}]')

def Mux(list_signal, index_signal):
    """Select a particular index out of a list signal.

    N.B. The result of this function can only be used on the right-hand side
    of an assignment.
    """

    #
    # This is a bit of a hack, but here the GetUniqueName function is reused
    # as if this were an operator. In the future, this function should be
    # converted into an Operator.
    #

    result = CreateSignal(
        Bits(list_signal[0].signal.width),
        name=Operator.GetUniqueName('mux'))

    CurrentModule().signals.append(result.signal)

    #
    # The ConnectionContext() context manager pushes a new predicate context
    # for use in assignments. This effectively means that any assignments
    # inside the with aren't predicated by anything outside this function.
    #

    with ConnectionContext():

        #
        # result is defaulted to [0] because the emitter requires wires to be
        # driven in all logic cases.
        #

        result <<= list_signal[0]

        for i in range(1, len(list_signal)):
            with index_signal == i:
                result <<= list_signal[i]

    return result

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
        self.rvalue = Mux(self.list_signal, self.index_signal)

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
            lambda item: (FilterRvalue(item[0]), item[1]),
            CurrentPredicate())

        InsertConnection(self.signal, predicate, other)

        return self

    def ResetWith(self, reset, reset_value):
        """Set the reset signal and value for this signal."""
        self.signal.reset = FilterRvalue(reset)
        self.signal.reset_value = FilterRvalue(reset_value)

    def ClockWith(self, clock):
        """Set the clock signal for this signal."""
        self.signal.clock = FilterRvalue(clock)

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