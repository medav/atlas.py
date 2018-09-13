from dataclasses import *

class SignalDir(object):
    INHERIT = 0
    INPUT = 1
    OUTPUT = 2
    INOUT = 3
    FLIPPED = 4

flip_map = {
    SignalDir.INPUT: SignalDir.OUTPUT,
    SignalDir.OUTPUT: SignalDir.INPUT,
    SignalDir.INOUT: SignalDir.INOUT,
}

@dataclass
class SignalMeta(object):
    """Signal metadata record

    Fields:
    name -- Name of this signal
    parent -- Reference to the parent of this signal
    sigdir -- Direction of this signal

    This class contains meta-data common to all signal types. This includes its
    name, parent, and direction.
    """

    name : str = field(default=MISSING)
    parent : any = field(default=MISSING, repr=False)
    sigdir : int = field(default=SignalDir.INHERIT, repr=False)

    def __hash__(self):
        return hash((self.name, self.parent, self.sigdir))

@dataclass
class ConnectionTree(object):
    """Connection tree node

    Fields:
    predicate -- Predicate signal for this tree node (must have width == 1)
    true_path -- Assignment if predicate is true
    false_path -- Assignment is predicate is false

    A connection tree is a binary tree with no null leaf nodes. Such a tree is
    produced from a list of raw connections to hook up combinational logic
    properly.

    N.B. Connection trees are created and used internally by the emitter. They
    are not intended to be used by user code.
    """

    predicate : any = None
    true_path : any = None
    false_path : any = None

@dataclass
class ConnectionBlock(object):
    """A predicated connection block.

    Fields:
    predicate -- Predicate signal for this block (must have width == 1)
    true_block -- list of connections to apply if predicate is true
    false_block -- list of connections to apply if predicate is false

    A ConnectionBlock is used to predicate connections on a signal called the
    "predicate". During elaboration (execution of user code), a signal's
    connection list is populated with direct (unpredicated) connections and also
    predicated connections, which produce a ConnectionBlock.

    N.B. Order within connection lists matters. Later connections take
    precedence over earlier ones.
    """

    predicate : SignalMeta = None
    true_block : list = field(default_factory=list, compare=False, repr=False)
    false_block : list = field(default_factory=list, compare=False, repr=False)

@dataclass
class BitsSignal(object):
    """An array of bits

    Fields:
    meta -- Metadata for this signal
    width -- Width of this signal
    signed -- Whether or not to treat this signal as signed
    connections -- Ordered list of connections to apply to this signal
    clock -- Signal to use for clocking this signal
    reset -- Signal to use for applying synchronous resets
    reset_value -- Value to reset to when reset is asserted

    This is the primitive datatype that maps directly to Verilog code. List and
    Bundle types are containers used to provide user code with powerful ways to
    express bulk connections and related signals.
    """

    meta : SignalMeta

    width : int = field(default=1)
    signed : bool = field(default=False, repr=False)

    connections : list = field(default_factory=list, repr=False)

    clock : any = field(default=None, repr=None)
    reset : any = field(default=None, repr=None)
    reset_value : any = field(default=None, repr=None)

    def __hash__(self):
        return hash(self.meta)

@dataclass
class ListSignal(object):
    """A list of signals

    Fields:
    meta -- Metadata for this signal
    fields -- List of subsignals contained by this one

    This signal type is a container for other signals. In generated Verilog, a
    list signal simply becomes duplicated signals numbered 0 through N-1.
    """

    meta : SignalMeta
    fields : list = field(default_factory=list, compare=False, repr=False)

    def __hash__(self):
        return hash(self.meta)

@dataclass
class BundleSignal(object):
    """A bundle of signals

    Fields:
    meta -- Metadata for this signal
    fields -- dict of subsignals contained by this one

    This signal type is a container for other signals (like a ListSignal).
    Unlike a List, though, this allows for named children (essentially this is
    a dictionary of signals).
    """

    meta : SignalMeta
    fields : dict = field(default_factory=dict, compare=False, repr=False)

    def __hash__(self):
        return hash(self.meta)

@dataclass
class Module(object):
    """A Hardware Module

    Each module in atlas contains IO, several signals, submodules, and
    operators - all of which are used to synthsize the module to Verilog in the
    emitter.
    """

    name : str

    io_dict : dict = field(default=None, compare=False)
    io_typespec : dict = field(default=None, compare=False)
    instances : dict = field(default_factory=dict, compare=False, repr=False)
    signals : list = field(default_factory=list, compare=False, repr=False)
    ops : list = field(default_factory=list, compare=False, repr=False)

@dataclass
class CircuitConfig(object):
    """Configuration metadata for a circuit."""

    default_clock : bool = False
    default_reset : bool = False

@dataclass
class Circuit(object):
    """A Circuit"""

    name : str
    config : CircuitConfig = \
        field(default_factory=CircuitConfig, repr=False, compare=False)

    top : Module = field(default=None, compare=False, repr=False)
    modules : list = field(default_factory=list, compare=False, repr=False)
