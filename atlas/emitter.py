import copy

from .debug import *
from .utilities import *

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


def BuildConnectionTree(connections):
    if len(connections) == 0:
        return None

    #
    # If the last assignment was un-predicated, all preceding assignments are
    # ignored by order of precedence, so just return it by itself.
    #

    if type(connections[-1]) is not ConnectionBlock:
        return connections[-1]

    #
    # If the last assignment is predicated with both paths containing non-zero
    # number of assignments, it's possible that one of the nodes deeper in the
    # tree hasn't fully filled out it's true / false paths. In order to ensure
    # correct behavior, the preceding connections in the current context are
    # promoted one level deeper (connections[:-1] + <true/false>_block).
    #

    if (len(connections[-1].true_block) > 0) and (len(connections[-1].false_block) > 0):
        return ConnectionTree(
            predicate=connections[-1].predicate,
            true_path=BuildConnectionTree(connections[:-1] + connections[-1].true_block),
            false_path=BuildConnectionTree(connections[:-1] + connections[-1].false_block))

    #
    # If the last assignment was predicated but one of the two paths has no
    # assignments, then defer to previous connections in this block.
    #

    assert not ((len(connections[-1].true_block) == 0) and (len(connections[-1].false_block) == 0))

    sub_ctree = BuildConnectionTree(connections[:-1])

    if len(connections[-1].true_block) > 0:
        return ConnectionTree(
            predicate=connections[-1].predicate,
            true_path=BuildConnectionTree(connections[:-1] + connections[-1].true_block),
            false_path=sub_ctree)

    if len(connections[-1].false_block) > 0:
        return ConnectionTree(
            predicate=connections[-1].predicate,
            true_path=sub_ctree,
            false_path=BuildConnectionTree(connections[:-1] + connections[-1].false_block))

def PrintCTree(ctree, indent=0):
    def WriteLine(line):
        print(' |  ' * indent + line)

    if ctree is None:
        WriteLine('None')
    elif type(ctree) is not ConnectionTree:
        WriteLine(VName(ctree))
    else:
        WriteLine(f'Predicate: {VName(ctree.predicate)}')
        WriteLine('True path:')
        PrintCTree(ctree.true_path, indent + 1)
        WriteLine('False path:')
        PrintCTree(ctree.false_path, indent + 1)

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
            VConnect(bits, item)

def EmitComb(bits, connections):
    assert bits.clock is None

    ctree = BuildConnectionTree(connections)
    print()
    print(f'ctree for {VName(bits)}')
    PrintCTree(ctree)

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

                if len(bits.connections) > 0:
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