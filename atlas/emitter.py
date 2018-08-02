import copy

from .model import *
from .verilog import *

__all__ = [
    'EmitModule',
    'EmitCircuit'
]

def NavigateTo(current_predicate, new_predicate):
    pass

def CreateIntermediate(bits):
    int_bits = copy.copy(bits)
    int_bits.name = f'{bits.name}_int_'
    int_bits.sigstate = SignalTypes.REG
    return int_bits

def EmitConnections(signal):
    current_predicate = []
    bits_list = [
        (bits, CreateIntermediate(bits)) for bits in ForEachBits(signal)
    ]

    for (bits, int_bits) in bits_list:
        VDecl(int_bits)

    with VAlways():
        for (bits, int_bits) in bits_list:
            for connection in bits.connections:
                NavigateTo(current_predicate, connection.predicate)
                VConnect(VName(int_bits), VName(connection.rhs))

def EmitModule(module):
    with VModule(module.name, module.io.io_dict):
        for key in module.io.io_dict:
            signal = module.io.io_dict[key]
            if signal.sigdir != SignalTypes.INPUT:
                VDecl(signal)
                EmitConnections(signal)

        for signal in module.signals:
            VDecl(signal)
            EmitConnections(signal)

def EmitCircuit(circuit):
    for module in circuit.modules:
        EmitModule(module)