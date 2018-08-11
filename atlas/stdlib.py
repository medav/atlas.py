import math
from contextlib import contextmanager

from . import model
from .base import *
from .signal import *
from .verilog import *
from . import op
from .typespec import *

__all__ = [
    'Log2Floor',
    'Log2Ceil',
    'Cat',
    'Enum',
    'Const'
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

        super().__init__(Signal(Bits(self.width, False)), 'cat')
        self.signals = signals

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
        self.bitwidth = Log2Ceil(self.count)
        self.values = {}

        i = 0
        for name in names:
            self.values[name] = Const(i, self.bitwidth)
            i += 1

    def __getattr__(self, name):
        return self.values[name]

class ConstOperator(op.AtlasOperator):
    def __init__(self, value, width):
        super().__init__(Signal(Bits(width, False)), 'const')
        self.value = value
        self.width = width

    def Declare(self):
        VDeclWire(self.result)

    def Synthesize(self):
        VAssignRaw(VName(self.result), f'{self.value}')

def Const(value, width=0):
    if width == 0:
        if value == 0:
            width = 1
        else:
            width = max(1, Log2Ceil(value))

    return ConstOperator(value, width).result