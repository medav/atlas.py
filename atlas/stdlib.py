import math
from contextlib import contextmanager

from .debug import *
from .utilities import *

from . import model
from . import op

from .context import *
from .signal import *
from .verilog import *
from .typespec import *

__all__ = [
    'Log2Floor',
    'Log2Ceil',
    'Cat',
    'Fill',
    'Enum',
    'Instance'
]

def Log2Floor(n):
    return int(math.floor(math.log2(n)))

def Log2Ceil(n):
    return int(math.ceil(math.log2(n)))

class CatOperator(op.AtlasOperator):
    def __init__(self, signal_list):
        self.width = 0

        for signal in signal_list:
            assert signal.sigtype == model.SignalTypes.BITS
            self.width += signal.width

        super().__init__('cat')
        self.signal_list = signal_list
        self.RegisterSignal(Signal(Bits(self.width, False)))

    def Declare(self):
        VDeclWire(self.result)

    def Synthesize(self):
        catstr = \
            '{' + ', '.join([VName(signal) for signal in self.signal_list]) + '}'

        VAssignRaw(VName(self.result), catstr)

def Cat(signals):
    return CatOperator(signals).result

def Fill(val, width):
    return Cat([val for _ in range(width)])

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

class InstanceOperator(op.AtlasOperator):
    def __init__(self, module : model.Module):
        self.module = module

        super().__init__(module.name)

        for io_name in self.module.io:
            typespec = self.module.io.TypeSpecOf(io_name)
            signal = Signal(typespec)
            signal.sigdir = model.flip_map[self.module.io.DirectionOf(io_name)]
            self.RegisterSignal(signal, io_name)
            CurrentModule().signals.append(signal)

    def Declare(self):
        pass

    def Synthesize(self):
        with VModuleInstance(self.module.name, self.name):
            lines = []
            for bits, _ in ForEachIoBits(self.module.io.io_dict):
                io_name = VName(bits)
                # TODO: The .replace() here is an ugly hack that should be
                # fixed eventually.
                local_name = self.name + '_' + io_name.replace('io_', '')
                lines.append(f'.{io_name}({local_name})')

            for i in range(len(lines)):
                VEmitRaw(lines[i] + (',' if (i == len(lines) - 1) else ''))

def Instance(module):
    return InstanceOperator(module)