from contextlib import contextmanager

from .model import *

__all__ = [
    'VEmitRaw',
    'VName',
    'VModule',
    'VAssign'
]

def VEmitRaw(f, line):
    print(line)
    # f.write(f'{line}\n')

def VName(signal : SignalBase):
    if signal.typespec == SignalTypes.BUNDLE:
        raise TypeError('Bundles do not have Verilog names')
    elif signal.typespec == SignalTypes.LIST:
        raise TypeError('Lists do not have Verilog names')

    if signal.name is None:
        raise NameError('Signal must have a name')

    name = signal.name
    while issubclass(type(signal), SignalBase):
        signal = signal.parent

        if signal.name is None:
            raise NameError('Signal must have a name')

        name = f'{signal.name}_{name}'

    return name

dirstr_map = {
    SignalTypes.INPUT: 'input',
    SignalTypes.OUTPUT: 'output',
    SignalTypes.INOUT: 'inout',
}

flip_map = {
    SignalTypes.INPUT: SignalTypes.OUTPUT,
    SignalTypes.OUTPUT: SignalTypes.INPUT,
    SignalTypes.INOUT: SignalTypes.INOUT,
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

@contextmanager
def VModule(f, name : str, io_dict : dict):
    VEmitRaw(f, f'module {name} (')

    for key in io_dict:
        parent_dir = io_dict[key].sigdir
        for signal in ForEachBits(io_dict[key]):
            sigdir = parent_dir

            if signal.flipped:
                sigdir = flip_map[sigdir]

            dirstr = dirstr_map[sigdir]

            if signal.width == 1:
                VEmitRaw(f, f'{dirstr} {VName(signal)},')
            else:
                assert signal.width > 1
                VEmitRaw(f, f'{dirstr} {VName(signal)}[{signal.width}],')

    VEmitRaw(f, ');')
    yield

    VEmitRaw(f, 'endmodule')

def VAssign(lhs, rhs):
    VEmitRaw(f, f'assign {lhs} = {rhs};')