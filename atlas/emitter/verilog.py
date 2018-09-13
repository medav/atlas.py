from contextlib import contextmanager
from ..base import *

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
    signal : any

def VNameBool(item : bool):
    return '1' if item else '0'

def VNameInt(item):

    #
    # N.B. bools in Python are subclasses if int, so naming a bool will redirect
    # here first.
    #

    if type(item) is bool:
        return VNameBool(item)
    else:
        return str(item)

def VNameStr(item : str):
    return item

def VNameEdge(item : VPosedge):
    return f'posedge(clock)'

def VNameSignal(signal):
    if type(signal) is M.BundleSignal:
        raise TypeError('Bundles do not have Verilog names')
    elif type(signal) is M.ListSignal:
        raise TypeError('Lists do not have Verilog names')

    if signal.meta.name is None:
        raise NameError('Signal must have a name')

    sigtypes = { M.BitsSignal, M.ListSignal, M.BundleSignal }

    name_parts = [signal.meta.name]

    while type(signal) in sigtypes:
        if signal.meta.parent is None:
            break

        signal = signal.meta.parent

        if type(signal) in sigtypes:
            if signal.meta.name is None:
                raise NameError('Signal must have a name')

            name_parts.append(signal.meta.name)
        elif type(signal) is str:
            name_parts.append(signal)
        else:
            name_parts.append(signal.name)

    return '_'.join(reversed(name_parts))

name_func_map = {
    int: VNameInt,
    str: VNameStr,
    VPosedge: VNameEdge,
    M.BitsSignal: VNameSignal,
    M.ListSignal: VNameSignal,
    M.BundleSignal: VNameSignal
}

def VName(item):
    for key in name_func_map:
        if isinstance(item, key):
            return name_func_map[key](item)

    assert False, f'Cannot name item of type: {type(item)}'

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

def VConnect(lbits : M.BitsSignal, rhs, nonblock=True):
    assert lbits.meta.sigdir != M.SignalDir.INPUT
    VConnectRaw(VName(lbits), VName(rhs), nonblock)

@contextmanager
def VAlways(condition_list : list = None):
    if condition_list is None:
        VEmitRaw('always @* begin')

    else:
        signal_names = []

        for item in condition_list:
            if type(item) is VPosedge:
                assert type(item.signal) is M.BitsSignal
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
def VIf(bits : M.BitsSignal, invert=False):
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