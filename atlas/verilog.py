from contextlib import contextmanager

from .model import *

__all__ = [
    'VFile',
    'VEmitRaw',
    'VPosedge',
    'VName',
    'ForEachBits',
    'ForEachIoBits',
    'VModule',
    'VDeclReg',
    'VDeclWire',
    'VAlways',
    'VAssignRaw',
    'VAssign',
    'VConnectRaw',
    'VConnect',
    'VIf',
    'VElse'
]

current_file = None
indent = 0

@contextmanager
def VFile(filename):
    global current_file
    with open(filename, 'w') as f:
        current_file = f
        yield
        current_file = None

def Indent():
    global indent
    indent += 1

def Dedent():
    global indent
    assert indent > 0
    indent -= 1

def VEmitRaw(line):
    global indent
    global current_file
    assert current_file is not None
    current_file.write('    ' * indent + line + '\n')
    # f.write(f'{line}\n')

@dataclass
class VPosedge(object):
    signal : SignalBase

def VName(item):
    if type(item) is VPosedge:
        return f'posedge(clock)'

    # This is a signal, name it accordingly.
    signal = item

    if signal.sigtype == SignalTypes.BUNDLE:
        raise TypeError('Bundles do not have Verilog names')
    elif signal.sigtype == SignalTypes.LIST:
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
        signal = io_dict[key]
        parent_dir = signal.sigdir
        for bits in ForEachBits(signal):
            sigdir = signal.sigdir

            if signal.flipped:
                sigdir = flip_map[sigdir]

            yield bits, sigdir

@contextmanager
def VModule(name : str, io_dict : dict):
    VEmitRaw(f'module {name} (')
    Indent()

    for bits, sigdir in ForEachIoBits(io_dict):
        dirstr = dirstr_map[sigdir]
        if bits.width == 1:
            VEmitRaw(f'{dirstr} {VName(bits)},')
        else:
            assert bits.width > 1
            VEmitRaw(f'{dirstr} [{bits.width - 1} : 0] {VName(bits)},')

    Dedent()
    VEmitRaw(');')

    Indent()
    yield
    Dedent()

    VEmitRaw('endmodule')

def VDecl(signal, decltype='wire'):
    for bits in ForEachBits(signal):
        if bits.width == 1:
            VEmitRaw(f'{decltype} {VName(bits)};')
        else:
            assert bits.width > 1
            VEmitRaw(f'{decltype} [{bits.width - 1} : 0] {VName(bits)};')

def VDeclWire(signal):
    VDecl(signal)

def VDeclReg(signal):
    VDecl(signal, 'reg')

def VAssignRaw(lhs, rhs):
    VEmitRaw(f'assign {lhs} = {rhs};')

def VAssign(lbits, rbits):
    VAssignRaw(VName(lbits), VName(rbits))

def VConnectRaw(lhs, rhs):
    VEmitRaw(f'{lhs} <= {rhs};')

def VConnect(lbits : SignalBase, rbits : SignalBase):
    assert lbits.sigdir != SignalTypes.INPUT
    assert lbits.sigtype == SignalTypes.BITS
    # assert lbits.sigstate == SignalTypes.REG
    assert rbits.sigtype == SignalTypes.BITS
    VConnectRaw(VName(lbits), VName(rbits))

@contextmanager
def VAlways(condition_list=None):
    if condition_list is None:
        VEmitRaw('always @* begin')

    else:
        signal_names = []

        for item in condition_list:
            if type(item) is VPosedge:
                assert item.signal.sigtype == SignalTypes.BITS
                signal_names.append(f'posedge({VName(item.signal)})')
            else:
                signal_names += [
                    VName(bits)
                    for bits in ForEachBits(item)
                ]

        names_str = ', '.join(signal_names)

        VEmitRaw(f'always @({names_str}) begin')

    Indent()
    yield
    Dedent()

    VEmitRaw(f'end')

@contextmanager
def VIf(bits, invert=False):
    assert bits.sigtype == SignalTypes.BITS
    assert bits.width == 1

    invert_str = '!' if invert else ''

    VEmitRaw(f'if ({invert_str}{VName(bits)}) begin')
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