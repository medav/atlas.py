from .model import *

def VEmitRaw(line):
    print(line)

def VName(signal):
    if signal.typespec == SignalBase.BUNDLE:
        raise TypeError('Bundles do not have Verilog names')
    elif signal.typespec == SignalBase.LIST:
        raise TypeError('Lists do not have Verilog names')

    if signal.name is None:
        raise NameError('Signal must have a name')

    name = signal.name
    while signal.parent is not None:
        signal = signal.parent

        if signal.name is None:
            raise NameError('Signal must have a name')

        name = f'{signal.name}_{name}'

    return name

def VAssign(lhs, rhs):
    VEmitRaw(f'assign {lhs} = {rhs};')