from dataclasses import *

from ..base import *
from ..emitter import *

from .context import *
from .frontend import *

def Input(typespec):
    """Produce a signal marked as Input."""
    wrapper = CreateSignal(typespec)
    wrapper.signal.meta.sigdir = M.SignalTypes.INPUT
    return wrapper

def Output(typespec):
    """Produce a signal marked as Output."""
    wrapper = CreateSignal(typespec)
    wrapper.signal.meta.sigdir = M.SignalTypes.OUTPUT
    return wrapper

def Inout(typespec):
    """Produce a signal marked as Inout."""
    wrapper = CreateSignal(typespec)
    wrapper.signal.sigdir = M.SignalTypes.INOUT
    return wrapper

def Flip(typespec):
    """Mark a typespec as flipped.

    N.B. This can only be applied to bits signals.
    """

    assert IsBits(typespec)
    typespec['flipped'] = True
    return typespec

class IoBundle(M.IoBundle):
    def __init__(self, io_dict):
        self.wrap_fields = io_dict

        super().__init__(io_dict={
            key:io_dict[key].signal
            for key in io_dict
        })

        for key in self.io_dict:
            signal = self.io_dict[key]
            signal.meta.parent = self
            signal.meta.name = key

    def __getattr__(self, key):
        return self.wrap_fields[key]

    def DirectionOf(self, key):
        return self.wrap_fields[key].signal.meta.sigdir

    def __iter__(self):
        return iter(self.wrap_fields)

    def TypespecOf(self, key):
        return TypespecOf(self.wrap_fields[key].signal)

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
    signal = CreateSignal(typespec)
    CurrentModule().signals.append(signal.signal)
    return signal

def Reg(typespec, clock=None, reset=None, reset_value=None):
    """Produce a register signal based on the given typespec."""

    signal = CreateSignal(typespec)

    #
    # If clock and reset are not supplied, used the current module's default
    # clock and reset signals.
    #

    if clock is None:
        clock = DefaultClock()

    if reset is None:
        reset = DefaultReset()

    #
    # reset_value is optional (though strongly recommended).
    #

    if reset_value is not None:
        signal.ResetWith(reset, reset_value)

    signal.ClockWith(clock)

    CurrentModule().signals.append(signal.signal)

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

    for name in locals:
        if issubclass(type(locals[name]), SignalFrontend) and \
            locals[name].signal.meta.name is None:

            locals[name].signal.meta.name = name