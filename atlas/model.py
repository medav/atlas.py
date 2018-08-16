from dataclasses import dataclass, field, MISSING

class SignalTypes(object):
    # Types
    BITS = 0
    LIST = 1
    BUNDLE = 2

    # Direction
    INOUT = 0
    INPUT = 1
    OUTPUT = 2

flip_map = {
    SignalTypes.INPUT: SignalTypes.OUTPUT,
    SignalTypes.OUTPUT: SignalTypes.INPUT,
    SignalTypes.INOUT: SignalTypes.INOUT,
}

@dataclass
class SignalBase(object):
    name : str = field(default=MISSING)
    parent : any = field(default=MISSING, repr=False)
    sigtype : int = field(default=MISSING, repr=False)
    sigdir : int = field(default=SignalTypes.INOUT, repr=False)

@dataclass
class ConnectionBlock(object):
    predicate : SignalBase = None
    true_block : list = field(default_factory=lambda: [], compare=False, repr=False)
    false_block : list = field(default_factory=lambda: [], compare=False, repr=False)

@dataclass
class BitsSignal(SignalBase):
    sigtype : int = SignalTypes.BITS
    width : int = field(default=1)
    signed : bool = field(default=False, repr=False)
    flipped : bool = field(default=False, repr=False)
    connections : list = field(default_factory=lambda: [], repr=False)
    clock : any = field(default=None, repr=None)
    reset : any = field(default=None, repr=None)
    reset_value : any = field(default=None, repr=None)

@dataclass
class ListSignal(SignalBase):
    sigtype : int = SignalTypes.LIST
    fields : list = field(default_factory=lambda: [], compare=False, repr=False)

@dataclass
class BundleSignal(SignalBase):
    sigtype : int = SignalTypes.BUNDLE
    fields : dict = field(default_factory=lambda: {}, compare=False, repr=False)

@dataclass
class IoBundle(object):
    io_dict : dict
    name : str = 'io'

@dataclass
class Module(object):
    name : str
    io : dict = field(default=None, compare=False)
    instances : dict = field(default_factory=lambda: {}, compare=False, repr=False)
    signals : list = field(default_factory=lambda: [], compare=False, repr=False)
    ops : list = field(default_factory=lambda: [], compare=False, repr=False)

@dataclass
class CircuitConfig(object):
    default_clock : bool = False
    default_reset : bool = False

@dataclass
class Circuit(object):
    name : str
    config : CircuitConfig = field(default_factory=lambda: CircuitConfig(), repr=False, compare=False)
    top : Module = field(default=None, compare=False, repr=False)
    modules : list = field(default_factory=lambda: [], compare=False, repr=False)
