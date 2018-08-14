import math
from contextlib import contextmanager

from .debug import *
from .utilities import *

from . import model
from . import op

from .frontend import *
from .signal import *
from .verilog import *
from .typespec import *

__all__ = [
    'Log2Floor',
    'Log2Ceil',
    'Cat',
    'Enum'
]

def Log2Floor(n):
    return int(math.floor(math.log2(n)))

def Log2Ceil(n):
    return int(math.ceil(math.log2(n)))

class CatOperator(op.AtlasOperator):
    def __init__(self, signals):
        self.width = 0

        for signal in signals:
            assert signal.sigtype == model.SignalTypes.BITS
            self.width += signal.width

        super().__init__('cat')
        self.signals = signals
        self.RegisterOutput(Signal(Bits(self.width, False)))

    def Declare(self):
        VDeclWire(self.result)

    def Synthesize(self):
        catstr = \
            '{' + ', '.join([VName(signal) for signal in self.signals]) + '}'

        VAssignRaw(VName(self.result), catstr)

def Cat(signals):
    return CatOperator(signals).result

class Enum():
    def __init__(self, names):
        self.count = len(names)
        self.bitwidth = 1 if self.count == 1 else Log2Ceil(self.count)
        self.values = {}

        i = 0
        for name in names:
            self.values[name] = i
            i += 1

    def __getattr__(self, name):
        return self.values[name]