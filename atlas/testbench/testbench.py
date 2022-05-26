import math
from ctypes import *
from contextlib import contextmanager
import shutil

from ..frontend import *
from ..base import *

from .verilator import *

class SignalTestbench(object):
    def __init__(self, signal):
        self.signal = signal

    def __ilshift__(self, other):
        """Primary assignment operator."""

        raise NotImplementedError()

    def __getattr__(self, key):
        return self.signal.__getattribute__(key)

    def __setitem__(self, key, value):
        pass


class BitsTestbench(SignalTestbench):
    """Wrapper class for a M.BitsSignal that adds testbench functionality."""

    def __init__(self, signal, tb):
        assert type(signal) is M.BitsSignal
        super().__init__(signal)
        self.tb = tb
        self.num_bytes = (self.width + 7) // 8
        self.buf = create_string_buffer(self.num_bytes)
        self.sig_ptr = tb.LookupIo(VName(self.signal))

    def __ilshift__(self, val):
        self.SetValue(val)
        return self

    def SetValue(self, val):
        assert type(val) is int
        self.tb.WriteIo(self.sig_ptr, val, self.num_bytes)

    def GetValue(self):
        return self.tb.ReadIo(self.sig_ptr, self.num_bytes)


class ListTestbench(SignalTestbench):
    """Wrapper class for a M.ListSignal that adds testbench functionality."""

    def __init__(self, signal, tb):
        assert type(signal) is M.ListSignal
        super().__init__(signal)
        self.wrap_fields = [
            WrapTbSignal(signal, tb) for signal in self.signal.fields
        ]

    def __ilshift__(self, other):
        assert type(other) is list
        assert len(self) == len(other)

        for i in range(len(self)):
            self.wrap_fields[i] <<= other[i]

        return self

    def __getitem__(self, key):
        assert type(key) is int
        return self.wrap_fields[key]

    def __len__(self):
        return len(self.wrap_fields)

class BundleTestbench(SignalTestbench):
    def __init__(self, signal, tb):
        assert type(signal) is M.BundleSignal
        super().__init__(signal)
        self.wrap_fields = {
            key:WrapTbSignal(self.signal.fields[key], tb)
            for key in self.signal.fields
        }

    def __ilshift__(self, other):
        assert type(other) is dict
        assert self.signal.fields.keys() >= other.keys()

        for key in other:
            self.wrap_fields[key] <<= other[key]

        return self

    def __getattr__(self, key):
        return self.wrap_fields[key]

class IoTestbench():
    def __init__(self, io_dict, tb):
        self.io_dict = {
            key:WrapTbSignal(io_dict[key], tb)
            for key in io_dict
        }

    def __getattr__(self, key):
        return self.io_dict[key]

def WrapTbSignal(signal, tb):
    """Wrap a model signal with a corresponding testbench wrapper."""

    if type(signal) is M.BitsSignal:
        return BitsTestbench(signal, tb)
    elif type(signal) is M.ListSignal:
        return ListTestbench(signal, tb)
    elif type(signal) is M.BundleSignal:
        return BundleTestbench(signal, tb)
    else:
        assert False, f'Cannot wrap signal of type {type(signal)}'


class Testbench(object):
    def __init__(self, circuit, so_name):
        self.so = None
        self.so_name = so_name
        self.so = cdll.LoadLibrary(so_name)
        self.so.lookup_io.restype = c_void_p
        self.so.setup()
        self.io = IoTestbench(circuit.top.io_dict, self)

    def SetupVcd(self, filename):
        self.so.setup_vcd(c_char_p(filename.encode('ascii')))

    def LookupIo(self, io_name):
        cstr = c_char_p(io_name.encode('ascii'))
        return self.so.lookup_io(cstr)

    def WriteIo(self, sig_ptr, val, num_bytes):
        arr = val.to_bytes(num_bytes, 'little')
        self.so.write_io(c_void_p(sig_ptr), arr, num_bytes)

    def ReadIo(self, sig_ptr, num_bytes):
        buf = bytearray(num_bytes)
        char_array = c_char * len(buf)
        self.so.read_io(c_void_p(sig_ptr), char_array.from_buffer(buf), num_bytes)
        return int.from_bytes(buf, 'little')

    def Reset(self, num_cycles):
        self.so.reset(num_cycles)

    def Step(self, num_cycles):
        self.so.step(num_cycles)

    def __del__(self):
        if self.so is not None:
            self.so.teardown()


@contextmanager
def TestModule(mod_func):
    circuit = Circuit('circuit', True, True)

    with Context(circuit):
        top = mod_func()

    circuit.top = top
    circuit.name = top.name

    build_folder = f'test_{circuit.top.name}'
    so_name = VeriCompile(circuit, build_folder)
    tb = Testbench(circuit, so_name)

    yield tb

    del tb
    shutil.rmtree(build_folder, ignore_errors=True)
