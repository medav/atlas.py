import math
from contextlib import contextmanager

from ..base import *

from .context import *
from .frontend import *
from .signals import *

def Log2Floor(n):
    return int(math.floor(math.log2(n)))

def Log2Ceil(n):
    return int(math.ceil(math.log2(n)))

class CatOperator(Operator):
    def __init__(self, signal_list):
        self.width = 0

        signal_list = list(map(FilterRvalue, signal_list))

        for signal in signal_list:
            assert type(signal) is M.BitsSignal
            self.width += signal.width

        super().__init__('cat')
        self.signal_list = signal_list
        self.result = CreateSignal(Bits(self.width, False), 'result', self)

    def Declare(self):
        VDeclWire(self.result.signal)

    def Synthesize(self):
        catstr = \
            '{' + ', '.join([VName(signal) for signal in self.signal_list]) + '}'

        VAssignRaw(VName(self.result.signal), catstr)

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

class InstanceOperator(Operator):
    def __init__(self, module : M.Module):
        super().__init__(module.name)

        self.module = module
        self.io_bundle = {}
        self.io_map = {}

        for io_name in self.module.io_dict:
            typespec = TypespecOf(self.module.io_dict[io_name])
            signal = CreateSignal(typespec, io_name, self)
            signal.signal.meta.sigdir = M.flip_map[signal.signal.meta.sigdir]
            CurrentModule().signals.append(signal.signal)
            self.io_bundle[io_name] = signal

        if CurrentCircuit().config.default_clock:
            self.io_bundle['clock'] <<= DefaultClock()

        if CurrentCircuit().config.default_reset:
            self.io_bundle['reset'] <<= DefaultReset()

    def __getattr__(self, key):
        return self.io_bundle[key]

    def Declare(self):

        #
        # N.B. Because all signals from an instance are added to the module's
        # signal list, they will be declared with the rest of the signals in
        # the module.
        #

        pass

    def Synthesize(self):
        with VModuleInstance(self.module.name, self.name):
            lines = []

            for io_name in self.io_bundle:
                zip_bits = ZipBits(
                    FilterRvalue(self.module.io_dict[io_name]),
                    FilterRvalue(self.io_bundle[io_name]))

                for (iobits, intbits) in zip_bits:
                    lines.append(f'.{VName(iobits)}({VName(intbits)})')

            for i in range(len(lines)):
                VEmitRaw(lines[i] + (',' if (i < len(lines) - 1) else ''))

def Instance(module):
    return InstanceOperator(module)