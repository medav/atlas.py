from ..base import *

from .verilog import *

global nodeid
nodeid = 0

def NewNodeName():
    global nodeid
    this_id = nodeid
    nodeid += 1
    return f'_NODE_{this_id}'

def EmitCombNode(target, node):
    if type(node.true_path) is not M.ConnectionTree:
        true_node = node.true_path
    else:
        true_node = M.BitsSignal(
            M.SignalMeta(
                name=NewNodeName(),
                parent=None,
            ),
            width=target.width
        )

        VDeclWire(true_node)
        EmitCombNode(true_node, node.true_path)

    if type(node.false_path) is not M.ConnectionTree:
        false_node = node.false_path
    else:
        false_node = M.BitsSignal(
            M.SignalMeta(
                name=NewNodeName(),
                parent=None,
            ),
            width=target.width
        )

        VDeclWire(false_node)
        EmitCombNode(false_node, node.false_path)

    VAssignRaw(
        VName(target),
        f'{VName(node.predicate)} ? {VName(true_node)} : {VName(false_node)}')

def EmitComb(bits):
    assert bits.clock is None
    ctree = BuildConnectionTree(bits.connections)

    if type(ctree) is M.ConnectionTree:
        EmitCombNode(bits, ctree)
    else:
        VAssignRaw(VName(bits), VName(ctree))

def EmitSeqConnections(bits, connections=None):
    if connections is None:
        connections = bits.connections

    for item in connections:
        if type(item) is M.ConnectionBlock:

            if len(item.true_block) > 0:
                with VIf(item.predicate):
                    EmitSeqConnections(bits, item.true_block)

            if len(item.false_block) > 0:
                if len(item.true_block) == 0:
                    with VIf(item.predicate, invert=True):
                        EmitSeqConnections(bits, item.false_block)
                else:
                    with VElse():
                        EmitSeqConnections(bits, item.false_block)
        else:
            VConnect(bits, item)

def EmitSeq(module):
    clocks = set()

    for bits in filter(lambda bits: bits.clock is not None, ForBitsInModule(module)):
        if bits.clock is not None:
            clocks.add(bits.clock)

    for clock in clocks:
        with VAlways([VPosedge(clock)]):
            for bits in filter(lambda bits: bits.clock is clock, ForBitsInModule(module)):
                if (bits.reset is not None) and (bits.reset_value is not None):
                    with VIf(bits.reset):
                        VConnect(bits, bits.reset_value)
                    with VElse():
                        EmitSeqConnections(bits)
                else:
                    EmitSeqConnections(bits)

def EmitModule(module):
    signals = []

    with VModule(module.name, module.io):
        VEmitRaw('// Internal Signal Declarations')
        for signal in module.signals:
            for bits in ForEachBits(signal):
                if bits.clock is None:
                    VDeclWire(bits)
                else:
                    VDeclReg(bits)

        for op in module.ops:
            op.Declare()

        VEmitRaw('')

        VEmitRaw(f'// Operator Synthesis')
        for op in module.ops:
            op.Synthesize()

        VEmitRaw('')

        VEmitRaw(f'// Connections')
        for bits, sigdir in ForEachIoBits(module.io):
            if sigdir != M.SignalTypes.INPUT:
                if len(bits.connections) > 0:
                    EmitComb(bits)

        #
        # Emit Combinational Connections
        #

        for signal in module.signals:
            for bits in ForEachBits(signal):
                if (len(bits.connections) > 0) and (bits.clock is None):
                    EmitComb(bits)

        #
        # Emit Sequential Connections
        #

        EmitSeq(module)

def EmitCircuit(circuit, filename='a.v'):
    with VFile(filename):
        for module in circuit.modules:
            EmitModule(module)