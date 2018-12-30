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

        signal_list = list(map(FilterFrontend, signal_list))

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

@OpGen(cacheable=False, default='result')
def Cat(signals):
    return CatOperator(signals)

def Fill(val, width):
    return Cat([val for _ in range(width)])

class MemOperator(Operator):
    def __init__(self, width : int, depth : int, clock=None):
        super().__init__('mem')
        self.width = width
        self.depth = depth
        self.addrwidth = Log2Ceil(self.depth)

        if clock is None:
            self.clock = DefaultClock()
        else:
            self.clock = clock

        self.read_ports = []
        self.read_comb_ports = []
        self.write_ports = []

    def Read(self, addr_signal, enable_signal=None):
        read_signal = CreateSignal(
            Bits(self.width),
            name=f'read_{len(self.read_ports)}',
            parent=self,
            frontend=False)

        if enable_signal is not None:
            enable_signal = FilterFrontend(enable_signal)

        self.read_ports.append((
            FilterFrontend(addr_signal),
            read_signal,
            enable_signal))

        return WrapSignal(read_signal)

    def ReadComb(self, addr_signal):
        read_signal = CreateSignal(
            Bits(self.width),
            name=f'comb_read_{len(self.read_comb_ports)}',
            parent=self,
            frontend=False)

        self.read_comb_ports.append((FilterFrontend(addr_signal), read_signal))
        return WrapSignal(read_signal)

    def Write(self, addr_signal, data_signal, enable_signal):
        assert enable_signal.width == 1
        assert data_signal.width == self.width
        self.write_ports.append((
            FilterFrontend(addr_signal),
            FilterFrontend(data_signal),
            FilterFrontend(enable_signal)))

    def Declare(self):
        for (addr, data, enable) in self.read_ports:
            VDeclReg(data)

    def Synthesize(self):
        mem_name = self.name

        VEmitRaw(
            f'reg [{self.width - 1} : 0] {mem_name} [{self.depth - 1} : 0];')

        for (addr, data) in self.read_comb_ports:
            VAssignRaw(
                VName(data),
                f'{mem_name}[{VName(addr)}]')

        with VAlways([VPosedge(self.clock)]):
            for (addr, data, enable) in self.read_ports:
                if enable is None:
                    VConnectRaw(
                        VName(data),
                        f'{mem_name}[{VName(addr)}]')
                else:
                    with VIf(enable):
                        VConnectRaw(
                            VName(data),
                            f'{mem_name}[{VName(addr)}]')

            for (addr, data, enable) in self.write_ports:
                with VIf(enable):
                    VConnectRaw(
                        f'{mem_name}[{VName(addr)}]',
                        VName(data))

@OpGen(cacheable=False)
def Mem(width, depth, clock=None):
    return MemOperator(width, depth, clock)

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

        for io_name in self.module.io_typespec:
            typespec = self.module.io_typespec[io_name]
            signal = CreateSignal(typespec, io_name, self)
            signal.signal.meta.sigdir = M.flip_map[typespec.meta.sigdir]
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
                    FilterFrontend(self.module.io_dict[io_name]),
                    FilterFrontend(self.io_bundle[io_name]))

                for (iobits, intbits) in zip_bits:
                    lines.append(f'.{VName(iobits)}({VName(intbits)})')

            for i in range(len(lines)):
                VEmitRaw(lines[i] + (',' if (i < len(lines) - 1) else ''))

@OpGen(cacheable=False)
def Instance(module):
    return InstanceOperator(module)

def FillBits(signal, const_value):
    signal = FilterFrontend(signal)

    if type(signal) is M.BitsSignal:
        return const_value

    elif type(signal) is M.ListSignal:
        return [
            FillBits(signal.fields[0], const_value)
            for _ in range(len(signal.fields))
        ]

    elif type(signal) is M.BundleSignal:
        return {
            key: FillBits(signal.fields[key], const_value)
            for key in signal.fields
        }

    assert False, f'Cannot fill signal {signal}'

def ZerosLike(signal):
    return FillBits(signal, 0)

def RegNext(signal):
    typespec = FilterFrontend(signal).meta.typespec
    r = Reg(typespec, reset_value=ZerosLike(signal))
    r <<= signal
    return r

def NameSignals(locals):
    """Search locals and name any signal by its key.

    N.B. This intended to be called by client code to name signals in the local
    scope of a function during module elaboration.
    """

    for name in locals:
        if issubclass(type(locals[name]), SignalFrontend):
            locals[name].signal.meta.name = name

        if type(locals[name]) is InstanceOperator:
            locals[name].name = name