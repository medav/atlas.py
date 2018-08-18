from contextlib import contextmanager

from .model import *
from .utilities import *

__all__ = [
    'VFile',
    'VEmitRaw',
    'VPosedge',
    'VName',
    'VModule',
    'VModuleInstance',
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

def VNameInt(item : int):
    return str(item)

def VNameStr(item : str):
    return item

def VNameEdge(item : VPosedge):
    return f'posedge(clock)'

def VNameSignal(signal : SignalBase):
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

name_func_map = {
    int: VNameInt,
    str: VNameStr,
    VPosedge: VNameEdge,
    SignalBase: VNameSignal
}

def VName(item):
    for key in name_func_map:
        if isinstance(item, key):
            return name_func_map[key](item)

    assert False

@contextmanager
def VModule(name : str, io_dict : dict):
    VEmitRaw(f'module {name} (')
    Indent()

    io_lines = []

    for bits, sigdir in ForEachIoBits(io_dict):
        dirstr = dirstr_map[sigdir]
        if bits.width == 1:
            io_lines.append(f'{dirstr} {VName(bits)}')
        else:
            assert bits.width > 1
            io_lines.append(f'{dirstr} [{bits.width - 1} : 0] {VName(bits)}')

    for i in range(len(io_lines)):
        if i == len(io_lines) - 1:
            VEmitRaw(io_lines[i])
        else:
            VEmitRaw(io_lines[i] + ',')

    Dedent()
    VEmitRaw(');')

    Indent()
    yield
    Dedent()

    VEmitRaw('endmodule')

@contextmanager
def VModuleInstance(module_name, instance_name):
    VEmitRaw(f'{module_name} {instance_name} (')
    Indent()
    yield
    Dedent()
    VEmitRaw(');')

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

def VConnectRaw(lhs, rhs, nonblock=True):
    symbol = '<=' if nonblock else '='
    VEmitRaw(f'{lhs} {symbol} {rhs};')

def VConnect(lbits : SignalBase, rhs, nonblock=True):
    assert lbits.sigdir != SignalTypes.INPUT
    assert lbits.sigtype == SignalTypes.BITS
    VConnectRaw(VName(lbits), VName(rhs), nonblock)

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