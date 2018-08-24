from .debug import *
from .utilities import *

from . import model
from . import op

from .context import *
from .typespec import *
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

class BinaryOperator(op.AtlasOperator):
    def __init__(self, op0, op1, opname, verilog_op, r_width=0):
        assert op0.sigtype == model.SignalTypes.BITS
        assert (type(op1) is int) or (op1.sigtype == model.SignalTypes.BITS)

        r_width = op0.width if r_width == 0 else r_width

        super().__init__(opname)

        self.op0 = op0
        self.op1 = op1
        self.verilog_op = verilog_op

        self.RegisterSignal(Signal(Bits(r_width, False)))

    def Declare(self):
        VDeclWire(self.result)

    def Synthesize(self):
        VAssignRaw(
            VName(self.result),
            f'{VName(self.op0)} {self.verilog_op} {VName(self.op1)}')

class NotOperator(op.AtlasOperator):
    """Produces a new signal that is the bitwise NOT of its input."""

    def __init__(self, op0):
        assert issubclass(type(op0), model.BitsSignal)

        super().__init__('not')

        self.op0 = op0
        self.RegisterSignal(Signal(Bits(op0.width, False)))

    def Declare(self):
        VDeclWire(self.result)

    def Synthesize(self):
        VAssignRaw(VName(self.result), f'~{VName(self.op0)}')

class SliceOperator(op.AtlasOperator):
    """Produces a new signal that is a bit slice of its input.

    N.B. This operator can only apply to BitsSignals.
    """

    def __init__(self, op0, high, low):
        assert high >= low
        assert issubclass(type(op0), model.BitsSignal)

        super().__init__('slice')

        self.op0 = op0
        self.high = high
        self.low = low
        self.RegisterSignal(Signal(Bits(high - low + 1, False)))

    def Declare(self):
        VDeclWire(self.result)

    def Synthesize(self):
        VAssignRaw(VName(self.result), f'{VName(self.op0)}[{self.high}:{self.low}]')

def Mux(list_signal, index_signal):
    """Select a particular index out of a list signal.

    N.B. The result of this function can only be used on the right-hand side
    of an assignment.
    """

    result = Wire(Bits(list_signal[0].width))

    #
    # This is a bit of a hack, but here the GetUniqueName function is reused
    # as if this were an operator. In the future, this function should be
    # converted into an AtlasOperator.
    #

    result.name = op.AtlasOperator.GetUniqueName('mux')

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

    list_signal : ListSignal
    index_signal : BitsSignal
    rhs : model.SignalBase = field(init=False)

    def __post_init__(self):
        self.rhs = Mux(self.list_signal, self.index_signal)

    def __ilshift__(self, value):
        for i in range(len(self.list_signal)):
            with self.index_signal == i:
                self.list_signal[i] <<= value

class BitsSignal(model.BitsSignal):
    """Wrapper class for a BitsSignal that adds frontend functionality."""

    def __init__(self, typespec, name=None, parent=None):
        if not IsBits(typespec):
            raise TypeError('Typespec is not Bits')

        super().__init__(
            name=name,
            parent=parent,
            width=typespec['width'],
            signed=typespec['signed'],
            flipped=typespec['flipped'])

    def __ilshift__(self, other):
        """Primary assignment operator.

        N.B. The ilshift operator in python expects a return value to update the
        calling code's variable reference. Since this routine simply adds an
        assignment in this signal's connection tree and doesn't produce a new
        value for the variable, it just returns itself.
        """

        #
        # A ListIndex is a wrapper class for indexing into a list signal. The
        # rhs field is the muxed value that can be used on the right-hand of
        # an assignment.
        #

        if isinstance(other, ListIndex):
            other = other.rhs

        #
        # If assigning to another signal, that signal must be another BitsSignal
        # or the assignment is invalid.
        #

        elif isinstance(other, model.SignalBase):
            assert other.sigtype == model.SignalTypes.BITS

        #
        # This signal cannot be assigned to if it's marked as input.
        #

        assert self.sigdir != model.SignalTypes.INPUT

        #
        # At this point, the rhs of this assignment is ready to be inserted
        # into the connection ast. This is done by walking through the current
        # predicate and producing connection blocks in this signal's ast until
        # a point is reached where this connection can be inserted.
        #

        predicate = CurrentPredicate()
        block = self.connections

        for (signal, path) in predicate:
            if (len(block) > 0) and (type(block[-1]) is model.ConnectionBlock) and (block[-1].predicate is signal):
                block = block[-1].true_block if path else block[-1].false_block
            else:
                cb = model.ConnectionBlock(signal)
                block.append(cb)
                block = cb.true_block if path else cb.false_block

        block.append(other)
        return self

    def ResetWith(self, reset, reset_value):
        """Set the reset signal and value for this signal."""
        self.reset = reset
        self.reset_value = reset_value

    def ClockWith(self, clock):
        """Set the clock signal for this signal."""
        self.clock = clock

    def __enter__(self):
        assert self.width == 1, 'Conditions must have bitwidth == 1'
        StartCondition(self)

    def __call__(self, high, low):
        return SliceOperator(self, high, low).result

    def __exit__(self, *kwargs):
        EndCondition()

    #
    # These magic functions are what enable frontend code to use Python's
    # operators to produce verilog operations. They essentially just produce
    # AtlasOperators that implement their corresponding operations in Verilog
    # code.
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

    #
    # The ability to hash a signal is used internally in Atlas for various
    # tasks and optimizations. It is, at the very least, required for the
    # emitter to function properly.
    #

    def __hash__(self):
        return hash((self.name, self.parent))

class ListSignal(model.ListSignal):
    """Wrapper class for a ListSignal that adds frontend functionality."""

    def __init__(self, typespec, name=None, parent=None):
        if type(typespec) is not list:
            raise TypeError('Typespec is not List')

        fields = list([Signal(typespec[i], f'i{i}', self) for i in range(len(typespec))])

        super().__init__(
            name=name,
            parent=parent,
            fields=fields)

    def __ilshift__(self, other):
        """Primary assignment operator.

        N.B. The ilshift operator in python expects a return value to update the
        calling code's variable reference. Since this routine simply adds an
        assignment in this signal's connection tree and doesn't produce a new
        value for the variable, it just returns itself.
        """

        #
        # A ListIndex is a wrapper class for indexing into a list signal. The
        # rhs field is the muxed value that can be used on the right-hand of
        # an assignment.
        #

        if isinstance(other, ListIndex):
            other = other.rhs

        #
        # If assigning to another signal, that signal must be another ListSignal
        # or the assignment is invalid.
        #

        if isinstance(other, model.SignalBase):
            assert other.sigtype == model.SignalTypes.LIST
            assert len(other.fields) == len(self.fields)

            for i in range(len(self.fields)):
                self.fields[i] <<= other.fields[i]

        #
        # Assigning to a literal / constant value can be achieved by supplying
        # a Python list to this assignment operator.
        #

        elif type(other) is list:
            for i in range(len(self.fields)):
                self.fields[i] <<= other[i]

        else:
            assert False, f'Cannot assign type {type(other)} to ListSignal'

        return self

    def ResetWith(self, reset, reset_value):
        """Set the reset signal and value for this signal's children."""

        assert type(reset_value) is list
        assert len(self.fields) == len(reset_value)

        for i in range(len(self.fields)):
            self.fields[i].ResetWith(reset, reset_value[i])

    def ClockWith(self, clock):
        """Set the clock signal for this signal's children"""

        for i in range(len(self.fields)):
            self.fields[i].ClockWith(clock)

    def __getitem__(self, key):
        if type(key) is int:
            return self.fields[key]
        else:
            return ListIndex(self, key)

    def __len__(self):
        return len(self.fields)

    def __setitem__(self, key, value):
        pass

    def __hash__(self):
        return hash((self.name, self.parent))

class BundleSignal(model.BundleSignal):
    def __init__(self, typespec, name=None, parent=None):
        if type(typespec) is not dict:
            raise TypeError('Typespec is not Bundle')

        fields = { field:Signal(typespec[field], field, self) for field in typespec }

        super().__init__(
            name=name,
            parent=parent,
            fields=fields)

    def __ilshift__(self, other):
        """Primary assignment operator.

        N.B. The ilshift operator in python expects a return value to update the
        calling code's variable reference. Since this routine simply adds an
        assignment in this signal's connection tree and doesn't produce a new
        value for the variable, it just returns itself.
        """

        #
        # If assigning to another signal, that signal must be another ListSignal
        # or the assignment is invalid.
        #

        if isinstance(other, ListIndex):
            other = other.rhs

        #
        # If assigning to another signal, that signal must be another
        # BundleSignal or the assignment is invalid.
        #

        if isinstance(other, model.SignalBase):
            assert other.sigtype == model.SignalTypes.BUNDLE
            assert self.fields.keys() >= other.fields.keys()

            for key in other.fields:
                self.fields[key] <<= other.fields[key]

        #
        # Assigning to a literal / constant value can be achieved by supplying
        # a Python dict to this assignment operator.
        #

        elif type(other) is dict:
            assert self.fields.keys() >= other.keys()
            for key in other:
                self.fields[key] <<= other[key]

        else:
            assert False, f'Cannot assign type {type(other)} to BundleSignal'

        return self

    def ResetWith(self, reset, reset_value):
        """Set the reset signal and value for this signal's children."""

        assert type(reset_value) is dict
        assert set(reset_value.keys()) == set(self.fields.keys())

        for key in self.fields:
            self.fields[key].ResetWith(reset, reset_value[key])

    def ClockWith(self, clock):
        """Set the clock signal for this signal's children"""

        for key in self.fields:
            self.fields[key].ClockWith(clock)

    def __getattr__(self, key):
        return self.fields[key]

    def __hash__(self):
        return hash((self.name, self.parent))

def Signal(typespec, name=None, parent=None):
    """Produce a signal given a typespec.

    This is an entrypoint that is called by the signal init functions to
    recursively produce sub-signals.
    """

    if IsBits(typespec):
        return BitsSignal(typespec, name, parent)
    elif type(typespec) is list:
        return ListSignal(typespec, name, parent)
    elif type(typespec) is dict:
        return BundleSignal(typespec, name, parent)
    else:
        assert False, f'Unknown typespec: {typespec}'

def Input(typespec):
    """Produce a signal marked as Input.

    N.B. This also returns a tuple of the original typespec combined with the
    produced signal. This is because io_dict's encode the typespec of their
    signals so they can be duplicated when they are instanced.
    """

    signal = Signal(typespec)
    signal.sigdir = model.SignalTypes.INPUT
    return (typespec, signal)

def Output(typespec):
    """Produce a signal marked as Output.

    N.B. This also returns a tuple of the original typespec combined with the
    produced signal. This is because io_dict's encode the typespec of their
    signals so they can be duplicated when they are instanced.
    """

    signal = Signal(typespec)
    signal.sigdir = model.SignalTypes.OUTPUT
    return (typespec, signal)

def Inout(typespec):
    """Produce a signal marked as Inout.

    N.B. This also returns a tuple of the original typespec combined with the
    produced signal. This is because io_dict's encode the typespec of their
    signals so they can be duplicated when they are instanced.
    """

    signal = Signal(typespec)
    signal.sigdir = model.SignalTypes.INOUT
    return (typespec, signal)

def Flip(typespec):
    """Mark a typespec as flipped.

    N.B. This can only be applied to bits signals.
    """

    assert IsBits(typespec)
    typespec['flipped'] = True
    return typespec

class IoBundle(model.IoBundle):
    def __init__(self, io_dict):
        super().__init__(io_dict=io_dict)

        for key in self.io_dict:
            signal = io_dict[key][1]
            signal.parent = self
            signal.name = key

    def __getattr__(self, key):
        return self.io_dict[key][1]

    def DirectionOf(self, key):
        return self.io_dict[key][1].sigdir

    def __iter__(self):
        return iter(self.io_dict)

    def TypeSpecOf(self, key):
        return self.io_dict[key][0]

def Io(io_dict):
    """Produce an IoBundle based on the input io_dict."""

    #
    # If the current circuit config specifies default clock and reset. Add them
    # silently here.
    #

    if CurrentCircuit().config.default_clock:
        io_dict['clock'] = Input(Bits(1))

    if CurrentCircuit().config.default_reset:
        io_dict['reset'] = Input(Bits(1))

    io = IoBundle(io_dict)
    io.parent = CurrentModule()
    CurrentModule().io = io
    return io

def Wire(typespec):
    """Produce a wire signal based on the given typespec."""

    signal = Signal(typespec)
    CurrentModule().signals.append(signal)
    return signal

def Reg(typespec, clock=None, reset=None, reset_value=None):
    """Produce a register signal based on the given typespec."""

    signal = Signal(typespec)

    #
    # If clock and reset are not supplied, used the current module's default
    # clock and reset signals.
    #

    if clock is None:
        clock = DefaultClock()

    if reset is None:
        reset = DefaultReset()

    #
    # reset_value is optional (thought strongly recommended).
    #

    if reset_value is not None:
        signal.ResetWith(reset, reset_value)

    signal.ClockWith(clock)

    CurrentModule().signals.append(signal)

    #
    # The default for every register is to retain its current value. This is
    # achieved by making the first assignment to itself.
    #

    signal <<= signal
    return signal

def NameSignals(locals):
    """Search locals and name any signal by its key.

    N.B. This intended to be called by client code to name signals in the local
    scope of a function during module elaboration.
    """

    for local in locals:
        if issubclass(type(locals[local]), model.SignalBase):
            locals[local].name = local