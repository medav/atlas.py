import copy

from .model import *
from .verilog import *

__all__ = [
    'EmitModule',
    'EmitCircuit'
]

def CreateIntermediate(bits):
    int_bits = copy.copy(bits)
    int_bits.name = f'{bits.name}_int_'
    return int_bits

def EmitConnections(bits, connections):
    for item in connections:
        if type(item) is ConnectionBlock:

            if len(item.true_block) > 0:
                with VIf(item.predicate):
                    EmitConnections(bits, item.true_block)

            if len(item.false_block) > 0:
                if len(item.true_block) == 0:
                    with VIf(item.predicate, invert=True):
                        EmitConnections(bits, item.false_block)
                else:
                    with VElse():
                        EmitConnections(bits, item.false_block)
        else:
            assert item.sigtype == SignalTypes.BITS
            assert bits.width == item.width
            VConnect(bits, item)

def EmitComb(bits, connections):
    assert bits.clock is None
    with VAlways():
        EmitConnections(bits, connections)

def EmitSeq(bits, connections):
    assert bits.clock is not None

    with VAlways([VPosedge(bits.clock)]):
        if (bits.reset is not None) and (bits.reset_value is not None):
            with VIf(bits.reset):
                VConnect(bits, bits.reset_value)
            with VElse():
                EmitConnections(bits, connections)
        else:
            EmitConnections(bits, connections)

def EmitModule(module):
    signals = []

    with VModule(module.name, module.io.io_dict):
        VEmitRaw('// IO Declarations')
        for bits, sigdir in ForEachIoBits(module.io.io_dict):
            if sigdir != SignalTypes.INPUT:
                int_bits = CreateIntermediate(bits)
                VDeclReg(int_bits)
                VAssign(bits, int_bits)
                signals.append((int_bits, bits.connections))

        VEmitRaw('')

        VEmitRaw('// Internal Signal Declarations')
        for signal in module.signals:
            for bits in ForEachBits(signal):

                if bits.clock is None:
                    int_bits = CreateIntermediate(bits)
                    VDeclWire(bits)
                    VDeclReg(int_bits)
                    VAssign(bits, int_bits)
                    signals.append((int_bits, bits.connections))
                else:
                    VDeclReg(bits)
                    signals.append((bits, bits.connections))

        for op in module.ops:
            op.Declare()

        VEmitRaw('')

        VEmitRaw(f'// Operator Synthesis')
        for op in module.ops:
            op.Synthesize()

        VEmitRaw('')

        VEmitRaw(f'// Connections')
        for bits, connections in signals:
            VEmitRaw(f'// Connections for {VName(bits)}')
            if bits.clock is None:
                EmitComb(bits, connections)
            else:
                EmitSeq(bits, connections)
            VEmitRaw('')

def EmitCircuit(circuit, filename='a.v'):
    with VFile(filename):
        for module in circuit.modules:
            EmitModule(module)