from dataclasses import *

from ..base import *
from ..emitter import *

from .context import *
from .frontend import *

def Input(typespec):
    """Produce a signal marked as Input."""
    signal = CreateSignal(typespec, frontend=False)
    signal.meta.sigdir = M.SignalTypes.INPUT
    return signal

def Output(typespec):
    """Produce a signal marked as Output."""
    signal = CreateSignal(typespec, frontend=False)
    signal.meta.sigdir = M.SignalTypes.OUTPUT
    return signal

def Inout(typespec):
    """Produce a signal marked as Inout."""
    signal = CreateSignal(typespec, frontend=False)
    signal.sigdir = M.SignalTypes.INOUT
    return signal

def Flip(typespec):
    """Mark a typespec as flipped.

    N.B. This can only be applied to bits signals.
    """

    assert IsBits(typespec)
    typespec['flipped'] = True
    return typespec

def Io(io_dict):
    """Produce an Io Bundle based on the input io_dict."""

    #
    # If the current circuit config specifies default clock and reset. Add them
    # silently here.
    #

    if CurrentCircuit().config.default_clock:
        io_dict['clock'] = Input(Bits(1))

    if CurrentCircuit().config.default_reset:
        io_dict['reset'] = Input(Bits(1))

    for io_name in io_dict:
        io_dict[io_name].meta.name = io_name
        io_dict[io_name].meta.parent = 'io'

    CurrentModule().io_dict = io_dict
    return IoFrontend(io_dict)

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

    CurrentModule().signals.append(FilterFrontend(signal))

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