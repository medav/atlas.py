from .model import *
from .typespec import *

dirstr_map = {
    SignalTypes.INPUT: 'input',
    SignalTypes.OUTPUT: 'output',
    SignalTypes.INOUT: 'inout',
}

typestr_map = {
    SignalTypes.BITS: 'bits',
    SignalTypes.LIST: 'list',
    SignalTypes.BUNDLE: 'bundle'
}

def ForEachBits(signal):
    if signal.sigtype == SignalTypes.BITS:
        yield signal

    elif signal.sigtype == SignalTypes.LIST:
        for subsig in signal.fields:
            for bits in ForEachBits(subsig):
                yield bits

    elif signal.sigtype == SignalTypes.BUNDLE:
        for subsig in signal.fields:
            for bits in ForEachBits(signal.fields[subsig]):
                yield bits

    else:
        assert False

def ForEachIoBits(io_dict):
    for key in io_dict:
        signal = io_dict[key][1]
        parent_dir = signal.sigdir
        for bits in ForEachBits(signal):
            sigdir = signal.sigdir

            if signal.flipped:
                sigdir = flip_map[sigdir]

            yield bits, sigdir