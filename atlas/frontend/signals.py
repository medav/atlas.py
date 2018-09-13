from dataclasses import *

from ..base import *
from ..emitter import *

from .context import *
from .frontend import *

def Input(primitive_spec):
    """Produce a signal marked as Input."""
    signal = CreateSignal(primitive_spec, frontend=False)
    signal.meta.sigdir = M.SignalDir.INPUT
    return signal

def Output(primitive_spec):
    """Produce a signal marked as Output."""
    signal = CreateSignal(primitive_spec, frontend=False)
    signal.meta.sigdir = M.SignalDir.OUTPUT
    return signal

def Inout(primitive_spec):
    """Produce a signal marked as Inout."""
    signal = CreateSignal(primitive_spec, frontend=False)
    signal.sigdir = M.SignalDir.INOUT
    return signal

def Flip(primitive_spec):
    """Mark a typespec as flipped."""

    typespec = BuildTypespec(primitive_spec)
    typespec.meta.sigdir = M.SignalDir.FLIPPED
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

def Wire(primitive_spec):
    """Produce a wire signal based on the given primitive_spec."""
    signal = CreateSignal(primitive_spec)
    CurrentModule().signals.append(signal.signal)
    return signal

def Reg(primitive_spec, clock=None, reset=None, reset_value=None):
    """Produce a register signal based on the given primitive_spec."""

    signal = CreateSignal(primitive_spec)

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