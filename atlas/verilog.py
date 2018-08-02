from contextlib import contextmanager

from .model import *

__all__ = [
    'VEmitRaw',
    'VName',
    'ForEachBits',
    'VModule',
    'VDecl',
    'VAlways',
    'VAssign',
    'VConnect',
    'VIf',
    'VElse'
]

indent = 0

def Indent():
    global indent
    indent += 1

def Dedent():
    global indent
    assert indent > 0
    indent -= 1

def VEmitRaw(line):
    global indent
    print('    ' * indent + line)
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

        if signal is None:
            break

        if signal.name is None:
            raise NameError('Signal must have a name')

        name = f'{signal.name}_{name}'

    return name

dirstr_map = {
    SignalTypes.INPUT: 'input',
    SignalTypes.OUTPUT: 'output',
    SignalTypes.INOUT: 'inout',
}

statestr_map = {
    SignalTypes.WIRE: 'wire',
    SignalTypes.REG: 'reg'
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
def VModule(name : str, io_dict : dict):
    VEmitRaw(f'module {name} (')

    for key in io_dict:
        parent_dir = io_dict[key].sigdir
        for signal in ForEachBits(io_dict[key]):
            sigdir = parent_dir

            if signal.flipped:
                sigdir = flip_map[sigdir]

            dirstr = dirstr_map[sigdir]

            if signal.width == 1:
                VEmitRaw(f'{dirstr} {VName(signal)},')
            else:
                assert signal.width > 1
                VEmitRaw(f'{dirstr} {VName(signal)}[{signal.width}],')

    VEmitRaw(');')

    Indent()
    yield
    Dedent()

    VEmitRaw('endmodule')

def VDecl(signal):
    for bits in ForEachBits(signal):
        sigdir = bits.sigdir

        if bits.flipped:
            sigdir = flip_map[sigdir]

        statestr = statestr_map[bits.sigstate]

        if bits.width == 1:
            VEmitRaw(f'{statestr_map[bits.sigstate]} {VName(bits)};')
        else:
            assert bits.width > 1
            VEmitRaw(f'{statestr_map[bits.sigstate]} {VName(bits)}[{bits.width}];')

def VAssign(lhs, rhs):
    VEmitRaw(f'assign {lhs} = {rhs};')

def VConnect(lhs, rhs):
    VEmitRaw(f'{lhs} <= {rhs};')

@contextmanager
def VAlways(signal_list=None):
    if signal_list is None:
        VEmitRaw('always @* begin')

    else:
        signal_names = [
            VName(bits)
            for signal in signal_list
            for bits in ForEachBits(bits)
        ]

        names_str = ', '.join(signal_names)

        VEmitRaw(f'always @({names_str}) begin')

    Indent()
    yield
    Dedent()

    VEmitRaw(f'end')

@contextmanager
def VIf(bits):
    assert type(bits) is BitsSignal
    assert bits.width == 1

    VEmitRaw(f'if ({VName(bits)}) begin')
    Indent()
    yield
    Dedent()
    VEmitRaw('end')

@contextmanager
def VElse():
    VEmitRaw(f'else begin')
    Indent()
    yield
    Dedent()
    VEmitRaw('end')