import copy

from .model import *
from .verilog import *

__all__ = [
    'EmitModule',
    'EmitCircuit'
]

def NavigateTo(current_predicate, new_predicate):
    pass

def CreateIntermediate(bits, int_map : dict):
    int_bits = copy.copy(bits)
    int_bits.name = f'{bits.name}_int_'
    int_bits.sigstate = SignalTypes.REG
    int_map[bits.name] = (bits, int_bits)
    return int_bits

def EmitConnections(module, block_list, int_map, emit_comb=True):
    for item in block_list:
        if type(item) is Connection:
            assert item.lhs.sigtype == SignalTypes.BITS
            assert item.rhs.sigtype == SignalTypes.BITS

            if emit_comb and (item.lhs.sigstate == SignalTypes.WIRE):
                if item.lhs.name in int_map:
                    VConnect(int_map[item.lhs.name][1], item.rhs)
                else:
                    VConnect(item.lhs, item.rhs)
            elif (not emit_comb) and (item.lhs.sigstate == SignalTypes.REG):
                VConnect(item.lhs, item.rhs)

        elif type(item) is ConnectionBlock:
            with VIf(item.predicate):
                EmitConnections(module, item.true_block, int_map, emit_comb)
            
            if len(item.false_block) > 0:
                with VElse():
                    EmitConnections(module, item.false_block, int_map, emit_comb)
        else:
            assert False

def EmitCombinationalLogic(module, int_map):
    with VAlways():
        EmitConnections(module, module.connections, int_map)

def EmitSequentialLogic(module):
    pass
    # with VAlways(VPosedge(module.io.clock)):
    #     pass

def EmitModule(module):
    int_map = {}

    with VModule(module.name, module.io.io_dict):

        for signal in module.signals:
            for bits in ForEachBits(signal):
                VDecl(bits)

                if bits.sigstate == SignalTypes.WIRE:
                    int_bits = CreateIntermediate(bits, int_map)
                    VDecl(int_bits)

        for key in int_map:
            (bits, int_bits) = int_map[key]
            VConnect(bits, int_bits)

        EmitCombinationalLogic(module, int_map)
        EmitSequentialLogic(module)

def EmitCircuit(circuit):
    for module in circuit.modules:
        EmitModule(module)