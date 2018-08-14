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

def ForEachBitsPair(signal_a, signal_b):
    assert CompareTypespec(signal_a.typespec, signal_b.typespec)

    if signal_a.sigtype == SignalTypes.BITS:
        yield (signal_a, signal_b)

    elif signal_a.sigtype == SignalTypes.LIST:
        for i in range(len(signal_a.fields)):
            subsig_a = signal_a[i]
            subsig_b = signal_b[i]
            for pair in ForEachBitsPair(subsig_a, subsig_b):
                yield pair

    elif signal_a.sigtype == SignalTypes.BUNDLE:
        for key in signal_a.fields:
            subsig_a = signal_a.fields[key]
            subsig_b = signal_b.fields[key]
            for pair in ForEachBitsPair(subsig_a, subsig_b):
                yield pair

    else:
        assert False

def ForEachIoBits(io_dict):
    for key in io_dict:
        signal = io_dict[key]
        parent_dir = signal.sigdir
        for bits in ForEachBits(signal):
            sigdir = signal.sigdir

            if signal.flipped:
                sigdir = flip_map[sigdir]

            yield bits, sigdir