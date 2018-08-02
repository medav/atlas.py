from dataclasses import dataclass, field, MISSING

class SignalTypes(object):
    # Types
    BITS = 0
    LIST = 1
    BUNDLE = 2

    # State
    WIRE =  0
    REG = 1

    # Direction
    INOUT = 0
    INPUT = 1
    OUTPUT = 2

@dataclass
class SignalBase(object):
    name : str = field(default=MISSING)
    typespec : any = field(default=MISSING, repr=False)
    parent : any = field(default=MISSING, repr=False)
    sigtype : int = field(default=MISSING, repr=False)
    sigstate : int = field(default=SignalTypes.WIRE, repr=False)
    sigdir : int = field(default=SignalTypes.INOUT, repr=False)

@dataclass
class BitsSignal(SignalBase):
    sigtype : int = SignalTypes.BITS
    width : int = field(default=1)
    signed : bool = field(default=False, repr=False)
    flipped : bool = field(default=False, repr=False)
    connections : list = field(default_factory=lambda: [], repr=False)

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
class Connection(object):
    predicate : list
    rhs : SignalBase

@dataclass
class Module(object):
    name : str
    io : dict = field(default=None, compare=False)
    instances : dict = field(default_factory=lambda: {}, compare=False, repr=False)
    signals : list = field(default_factory=lambda: [], compare=False, repr=False)
    ops : list = field(default_factory=lambda: [], compare=False, repr=False)

@dataclass
class Circuit(object):
    name : str
    top : Module = field(default=None, compare=False, repr=False)
    modules : list = field(default_factory=lambda: [], compare=False, repr=False)
